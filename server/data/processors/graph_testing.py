import time
import copy

from data.processors.clustering import *
from data.processors.text import split_comment
import data.models as models
from typing import List
from data.processors.structure import SameArticleComparator, SameCommentComparator, ReplyToComparator, \
    TemporalComparator
from data.processors.embedding import SimilarityComparator
from data.processors.ranking import PageRanker, CentralityDegreeCalculator, SizeRanker, VotesRanker, RecencyRanker, \
    ToxicityRanker
from data.processors.filters import *


from configparser import ConfigParser
from common import config
import logging
import pandas as pd

COMPARATORS = [
    SameArticleComparator,
    SameCommentComparator,
    ReplyToComparator,
    SimilarityComparator,
    TemporalComparator
]

MODIFIERS = [
    # edge and node weighting
    PageRanker,
    CentralityDegreeCalculator,
    SizeRanker,
    VotesRanker,
    RecencyRanker,
    ToxicityRanker,

    # filtering
    GenericEdgeFilter, SimilarityEdgeFilter, ReplyToEdgeFilter, SameCommentEdgeFilter, SameArticleEdgeFilter,
    SameGroupEdgeFilter, TemporalEdgeFilter, OrEdgeFilter,
    GenericBottomEdgeFilter, BottomSimilarityEdgeFilter, BottomReplyToEdgeFilter, BottomTemporalEdgeFilter,
    BottomSameCommentFilter, BottomSameArticleEdgeFilter, BottomSameGroupEdgeFilter,
    GenericNodeWeightFilter, SizeFilter, PageRankFilter, DegreeCentralityFilter,
    RecencyFilter, VotesFilter, ToxicityFilter,
    GenericNodeWeightBottomFilter, SizeBottomFilter, PageRankBottomFilter, DegreeCentralityBottomFilter,
    RecencyBottomFilter, VotesBottomFilter, ToxicityBottomFilter,

    # merging and clustering
    GenericNodeMerger, SimilarityNodeMerger, ReplyToNodeMerger, SameCommentNodeMerger, SameArticleNodeMerger,
    SameGroupNodeMerger, TemporalNodeMerger, MultiNodeMerger,
    GenericClusterer, SimilarityClusterer, ReplyToClusterer, SameCommentClusterer, SameArticleClusterer,
    SameGroupClusterer, TemporalClusterer, MultiEdgeTypeClusterer
]

logger = logging.getLogger('data.processors.graph')


class GraphRepresentation(GraphRepresentationType):
    def __init__(self, comments: List[models.CommentCached], conf: dict = None):
        super().__init__(comments)

        # create a temporary copy of the global config
        self.conf = ConfigParser()
        self.conf.read_dict(config)
        if conf is not None:
            self.conf.read_dict(conf)
        self.comments: List[models.SplitComment] = [split_comment(comment) for comment in comments]

        # config: configuration from DEFAULT.ini
        # self.conf: configuration from code
        self.conf = config

        logger.debug(f'{len(self.comments)} comments turned '
                     f'into {len([s for c in self.comments for s in c.splits])} splits')

        # construct graph
        graph_iteration_config = [
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=False, descending_order=True)],
                "SC_PRB_k50"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=100, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=False, descending_order=True)],
                "SC_PRB_it100"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.5, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=False, descending_order=True)],
                "SC_PRB_d0.5"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankBottomFilter(top_k=100, strict=False, descending_order=True)],
                "SC_PRB_k100"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=True, descending_order=True)],
                "SC_PRB_strict"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=False, descending_order=False)],
                "SC_PRB_asc"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=False)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=False, descending_order=False)],
                "SC_PRB_no_consec"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankFilter(threshold=0.0005, strict=False, smaller_as=False)],
                "SC_PR_t0005"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankFilter(threshold=0.001, strict=False, smaller_as=False)],
                "SC_PR_t001"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankFilter(threshold=0.005, strict=False, smaller_as=False)],
                "SC_PR_t005"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankFilter(threshold=0.001, strict=False, smaller_as=False)],
                "SC_PR_t001"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankFilter(threshold=0.001, strict=True, smaller_as=False)],
                "SC_PR_strict"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_COMMENT", user_power_mode=True),
                 PageRankFilter(threshold=0.001, strict=False, smaller_as=True)],
                "SC_PR_smaller"
            ),
            (
                [ReplyToComparator(base_weight=1.0, only_root=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="REPLY_TO", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=False, descending_order=True)],
                "RT_PRB"
            ),
            (
                [SameArticleComparator(base_weight=1.0, only_root=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SAME_ARTICLE", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=False, descending_order=True)],
                "SA_PRB"
            ),
            (
                [TemporalComparator(base_weight=1.0, only_root=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="TEMPORAL", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=False, descending_order=True)],
                "T_PRB"
            ),
            (
                [SimilarityComparator(max_similarity=0.75, base_weight=0.1, only_root=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SIMILARITY", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=False, descending_order=True)],
                "S_PRB"
            ),
            (
                [SimilarityComparator(max_similarity=0.75, base_weight=0.1, only_root=True)],
                [PageRanker(num_iterations=10, d=0.85, edge_type="SIMILARITY", user_power_mode=True),
                 PageRankBottomFilter(top_k=50, strict=True, descending_order=True)],
                "S_PRB_strict"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [CentralityDegreeCalculator(),
                 DegreeCentralityFilter(threshold=0.0005, strict=False, smaller_as=False)],
                "S_CD"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [CentralityDegreeCalculator(),
                 DegreeCentralityBottomFilter(top_k=50, strict=False, descending_order=True)],
                "S_CDB"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [ToxicityRanker(window_length=125, whole_comment=True),
                 ToxicityBottomFilter(top_k=50, strict=False, descending_order=True)],
                "S_TB"
            ),
            (
                [SimilarityComparator(max_similarity=0.75, base_weight=0.1, only_root=True)],
                [VotesRanker(use_upvotes=True, use_downvotes=True),
                 VotesFilter(threshold=5, strict=False, smaller_as=False)],
                "S_V"
            ),
            (
                [SimilarityComparator(max_similarity=0.75, base_weight=0.1, only_root=True)],
                [VotesRanker(use_upvotes=True, use_downvotes=True),
                 VotesBottomFilter(top_k=50, strict=False, descending_order=True)],
                "S_VB"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [VotesRanker(use_upvotes=True, use_downvotes=True),
                 VotesBottomFilter(top_k=50, strict=False, descending_order=True)],
                "SC_VB"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [VotesRanker(use_upvotes=True, use_downvotes=True),
                 VotesBottomFilter(top_k=50, strict=True, descending_order=True)],
                "SC_VB_strict"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [SizeRanker(),
                 SizeBottomFilter(top_k=50, strict=False, descending_order=True)],
                "SC_SB"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [SizeRanker(),
                 SizeBottomFilter(top_k=50, strict=True, descending_order=True)],
                "SC_SB_strict"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [RecencyRanker(use_youngest=True),
                 RecencyBottomFilter(top_k=50, strict=False, descending_order=True)],
                "SC_RB"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [RecencyRanker(use_youngest=True),
                 RecencyBottomFilter(top_k=50, strict=True, descending_order=True)],
                "SC_RB_strict"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [RecencyRanker(use_youngest=False),
                 RecencyBottomFilter(top_k=50, strict=False, descending_order=True)],
                "SC_RB"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [RecencyRanker(use_youngest=False),
                 RecencyBottomFilter(top_k=50, strict=True, descending_order=True)],
                "SC_RB_strict"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [SameCommentNodeMerger(threshold=0.01, smaller_as=False)],
                "SC_merge_01"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [SameCommentNodeMerger(threshold=0.001, smaller_as=False)],
                "SC_merge_001"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [SameCommentNodeMerger(threshold=0.0001, smaller_as=False)],
                "SC_merge_0001"
            ),
            (
                [SameArticleComparator(base_weight=1.0, only_root=True)],
                [SameArticleNodeMerger(threshold=0.01, smaller_as=False)],
                "SA_merge_01"
            ),
            (
                [SameArticleComparator(base_weight=1.0, only_root=True)],
                [SameArticleNodeMerger(threshold=0.001, smaller_as=False)],
                "SA_merge_001"
            ),
            (
                [SameArticleComparator(base_weight=1.0, only_root=True)],
                [SameArticleNodeMerger(threshold=0.0001, smaller_as=False)],
                "SA_merge_0001"
            ),
            (
                [ReplyToComparator(base_weight=1.0, only_root=True)],
                [ReplyToNodeMerger(threshold=0.01, smaller_as=False)],
                "RT_merge_01"
            ),
            (
                [ReplyToComparator(base_weight=1.0, only_root=True)],
                [ReplyToNodeMerger(threshold=0.001, smaller_as=False)],
                "RT_merge_001"
            ),
            (
                [ReplyToComparator(base_weight=1.0, only_root=True)],
                [ReplyToNodeMerger(threshold=0.0001, smaller_as=False)],
                "RT_merge_0001"
            ),
            (
                [TemporalComparator(base_weight=1.0, only_root=True)],
                [TemporalNodeMerger(threshold=0.01, smaller_as=False)],
                "T_merge_01"
            ),
            (
                [TemporalComparator(base_weight=1.0, only_root=True)],
                [TemporalNodeMerger(threshold=0.001, smaller_as=False)],
                "T_merge_001"
            ),
            (
                [TemporalComparator(base_weight=1.0, only_root=True)],
                [TemporalNodeMerger(threshold=0.0001, smaller_as=False)],
                "T_merge_0001"
            ),
            (
                [SimilarityComparator(max_similarity=0.75, base_weight=0.1, only_root=True)],
                [SimilarityNodeMerger(threshold=0.01, smaller_as=False)],
                "S_merge_01"
            ),
            (
                [SimilarityComparator(max_similarity=0.75, base_weight=0.1, only_root=True)],
                [SimilarityNodeMerger(threshold=0.001, smaller_as=False)],
                "S_merge_001"
            ),
            (
                [SimilarityComparator(max_similarity=0.75, base_weight=0.1, only_root=True)],
                [SimilarityNodeMerger(threshold=0.0001, smaller_as=False)],
                "S_merge_0001"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [SameCommentClusterer(algorithm="girvannewman")],
                "SC_cluster_GN"
            ),
            (
                [SameCommentComparator(base_weight=1.0, only_consecutive=True)],
                [SameCommentClusterer(algorithm="gmc")],
                "SC_cluster_GMC"
            ),
            (
                [SameArticleComparator(base_weight=1.0, only_root=True)],
                [SameArticleClusterer(algorithm="girvannewman")],
                "SA_cluster_GN"
            ),
            (
                [SameArticleComparator(base_weight=1.0, only_root=True)],
                [SameArticleClusterer(algorithm="gmc")],
                "SA_cluster_GMC"
            ),
            (
                [ReplyToComparator(base_weight=1.0, only_root=True)],
                [ReplyToClusterer(algorithm="girvannewman")],
                "RT_cluster_GN"
            ),
            (
                [ReplyToComparator(base_weight=1.0, only_root=True)],
                [ReplyToClusterer(algorithm="gmc")],
                "RT_cluster_GMC"
            ),
            (
                [TemporalComparator(base_weight=1.0, only_root=True)],
                [TemporalClusterer(algorithm="girvannewman")],
                "T_cluster_GN"
            ),
            (
                [TemporalComparator(base_weight=1.0, only_root=True)],
                [TemporalClusterer(algorithm="gmc")],
                "T_cluster_GMC"
            ),
            (
                [SimilarityComparator(max_similarity=0.75, base_weight=0.1, only_root=True)],
                [SimilarityClusterer(algorithm="girvannewman")],
                "S_cluster_GN"
            ),
            (
                [SimilarityComparator(max_similarity=0.75, base_weight=0.1, only_root=True)],
                [SimilarityClusterer(algorithm="gmc")],
                "S_cluster_GMC"
            )
        ]

        configuration_number = 0
        results = []
        original_edges = copy.deepcopy(self.edges)
        original_comments = copy.deepcopy(self.comments)
        original_id2idx = copy.deepcopy(self.id2idx)
        original_orig_comments = copy.deepcopy(self.orig_comments)
        for comparators, modifiers, desc in graph_iteration_config:
            self.edges = copy.deepcopy(original_edges)
            self.comments = copy.deepcopy(original_comments)
            self.id2idx = copy.deepcopy(original_id2idx)
            self.orig_comments = copy.deepcopy(original_orig_comments)
            start_time = time.time()
            self._build_index()
            self._pairwise_comparisons(comparators)
            nr_removed = self._modify(modifiers)
            end_time = time.time()

            time_taken = round(end_time - start_time, 3)
            logging.info(f'configuration {configuration_number}| {desc}- {len(self.edges)} edges, {nr_removed} removed,'
                         f' {time_taken} seconds')
            results.append((configuration_number, desc, len(self.edges), nr_removed, time_taken))
            configuration_number += 1

        result_df = pd.DataFrame.from_records(results, columns=["configuration ID", "Description", "remaining edges",
                                                                "removed edges", "seconds"])
        print(result_df)
        result_df.to_csv("configuration_testing.csv", index=False)

    def __dict__(self) -> models.Graph.__dict__:
        return {
            'comments': self.comments,
            'id2idx': self.id2idx,
            'edges': self.edges
        }

    def _build_index(self):
        for i, comment in enumerate(self.comments):
            self.id2idx[comment.id] = i

    def _pairwise_comparisons(self, comparators):
        # comparators = [comparator(conf=self.conf) for comparator in COMPARATORS if comparator.is_on(self.conf)]
        for i in (range(len(self.comments))):
            comment_i = self.comments[i]
            orig_comment_i = self.orig_comments[i]
            for si in range(len(comment_i.splits)):
                for j in range(i, len(self.comments)):
                    comment_j = self.comments[j]
                    orig_comment_j = self.orig_comments[j]
                    # if comparing sentences within the same comment, skip lower triangle
                    for sj in range(si + 1 if i == j else 0, len(comment_j.splits)):
                        edge_weights = models.EdgeWeights()

                        for comparator in comparators:
                            comparator.update_edge_weights(edge_weights,
                                                           orig_comment_i, comment_i,
                                                           orig_comment_j, comment_j, si, sj)
                        if edge_weights.dict(exclude_unset=True):
                            self.edges.append(models.Edge(src=[i, si],
                                                          tgt=[j, sj],
                                                          wgts=edge_weights))

    def _modify(self, modifiers):
        # modifiers = [modifier(conf=self.conf) for modifier in MODIFIERS if modifier.is_on(self.conf)]
        logger.debug(modifiers)

        nr_unfiltered = len(self.edges)
        for modifier in modifiers:
            modifier.modify(self)

        number_removed_edges = nr_unfiltered-len(self.edges)
        logger.debug(f'{nr_unfiltered-len(self.edges)} edges removed')
        return number_removed_edges

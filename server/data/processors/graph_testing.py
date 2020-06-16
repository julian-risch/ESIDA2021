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

        configuration_number = 0
        results = []
        original_edges = copy.deepcopy(self.edges)
        original_comments = copy.deepcopy(self.comments)
        original_id2idx = copy.deepcopy(self.id2idx)
        original_orig_comments = copy.deepcopy(self.orig_comments)
        from test.configuration_testing import graph_iteration_config
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

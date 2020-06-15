from data.processors.clustering import *
from data.processors.embedding import *
from data.processors.filters import *
from data.processors.ranking import *
from data.processors.structure import *

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


def return_testing_configuration():
    return graph_iteration_config

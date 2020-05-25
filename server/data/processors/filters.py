import logging
from data.processors import Modifier, GraphRepresentationType
from data.processors.ranking import build_edge_dict

logger = logging.getLogger('data.graph.filters')


#
# Edge Filters
#

class GenericEdgeFilter(Modifier):
    def __init__(self, *args, threshold=None, edge_type=None, **kwargs):
        """
        Removes all edges of the specific type below a threshold
        :param args:
        :threshold: value for edges to filter
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.threshold = self.conf_getfloat("threshold", threshold)
        self.edge_type = self.conf_getfloat("edge_type", edge_type)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'threshold={self.threshold}'
                     f'and edge_type={self.edge_type}')

    def modify(self, graph: GraphRepresentationType):
        graph.edges = [edge for edge in graph.edges
                       if edge.wgts[self.edge_type] and edge.wgts[self.edge_type] > self.threshold]
        return graph


class SimilarityEdgeFilter(GenericEdgeFilter):
    def __init__(self, *args, threshold=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_type="SIMILARITY", **kwargs)


class ReplyToEdgeFilter(GenericEdgeFilter):
    def __init__(self, *args, threshold=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_type="REPLY_TO", **kwargs)


class SameCommentEdgeFilter(GenericEdgeFilter):
    def __init__(self, *args, threshold=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_type="SAME_COMMENT", **kwargs)


class SameArticleEdgeFilter(GenericEdgeFilter):
    def __init__(self, *args, threshold=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_type="SAME_ARTICLE", **kwargs)


class SameGroupEdgeFilter(GenericEdgeFilter):
    def __init__(self, *args, threshold=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_type="SAME_GROUP", **kwargs)


class TemporalEdgeFilter(GenericEdgeFilter):
    def __init__(self, *args, threshold=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_type="TEMPORAL", **kwargs)


class OrEdgeFilter(Modifier):
    def __init__(self, *args, reply_to_threshold=None, same_comment_threshold=None, same_article_threshold=None,
                 similarity_threshold=None, same_group_threshold=None, temporal_threshold=None, **kwargs):
        """
        Combination of other filters allows AND operation. This is experimental for OR operation.
        The edge is removed if not at least one condition is true.
        :param args:
        :threshold: value for edges to filter
        :param kwargs:
        """

        super().__init__(*args, **kwargs)
        self.reply_to_threshold = self.conf_getfloat("reply_to_threshold", reply_to_threshold)
        self.same_comment_threshold = self.conf_getfloat("same_comment_threshold", same_comment_threshold)
        self.same_article_threshold = self.conf_getfloat("same_article_threshold", same_article_threshold)
        self.similarity_threshold = self.conf_getfloat("similarity_threshold", similarity_threshold)
        self.same_group_threshold = self.conf_getfloat("same_group_threshold", same_group_threshold)
        self.temporal_threshold = self.conf_getfloat("temporal_threshold", temporal_threshold)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'reply_to_threshold={self.reply_to_threshold} '
                     f'same_comment_threshold={self.same_comment_threshold} '
                     f'same_article_threshold={self.same_article_threshold} '
                     f'similarity_threshold={self.similarity_threshold} '
                     f'same_group_threshold={self.same_group_threshold} '
                     f'temporal_threshold={self.temporal_threshold} '
                     )

    def modify(self, graph: GraphRepresentationType):
        graph.edges = [edge for edge in graph.edges
                       if (edge.wgts.REPLY_TO and 0 < self.reply_to_threshold < edge.wgts.REPLY_TO
                           and edge.wgts.REPLY_TO)
                       or (edge.wgts.SAME_COMMENT and 0 < self.same_comment_threshold < edge.wgts.SAME_COMMENT
                           and edge.wgts.SAME_COMMENT)
                       or (edge.wgts.SAME_ARTICLE and 0 < self.same_article_threshold < edge.wgts.SAME_ARTICLE
                           and edge.wgts.SAME_ARTICLE)
                       or (edge.wgts.SIMILARITY and 0 < self.similarity_threshold < edge.wgts.SIMILARITY
                           and edge.wgts.SIMILARITY)
                       or (edge.wgts.SAME_GROUP and 0 < self.same_group_threshold < edge.wgts.SAME_GROUP
                           and edge.wgts.SAME_GROUP)
                       or (edge.wgts.TEMPORAL and 0 < self.temporal_threshold < edge.wgts.TEMPORAL
                           and edge.wgts.TEMPORAL)
                       ]
        return graph


class GenericBottomEdgeFilter(Modifier):
    def __init__(self, *args, top_edges=None, edge_type=None, **kwargs):
        """
        Filters all edges except top edges for specific edge type
        :param args:
        :param top_edges: the number of top edges to keep for each node
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.top_edges = self.conf_getint('top_edges', top_edges)
        self.edge_type = self.conf_get('edge_type', edge_type)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'top_edges={self.top_edges} '
                     f'for edge_type={self.edge_type}')

    def modify(self, graph: GraphRepresentationType):
        def filter_none(wgt_type):
            if wgt_type is None:
                return 0
            else:
                return wgt_type
        filtered_edges = []
        edge_dict = build_edge_dict(graph)
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                node_edges = edge_dict[(graph.id2idx[comment.id], j)]
                node_edges = sorted(node_edges, key=lambda e: filter_none(e.wgts[self.edge_type]), reverse=True)[
                             :self.top_edges]
                for edge in node_edges:
                    if edge not in filtered_edges:
                        filtered_edges.append(edge)
        graph.edges = filtered_edges

        return graph


class BottomSimilarityEdgeFilter(GenericBottomEdgeFilter):
    def __init__(self, *args, top_edges=None, **kwargs):
        GenericBottomEdgeFilter.__init__(self, *args, top_edges=top_edges, edge_type="SIMILARITY", **kwargs)


class BottomReplyToEdgeFilter(GenericBottomEdgeFilter):
    def __init__(self, *args, top_edges=None, **kwargs):
        GenericBottomEdgeFilter.__init__(self, *args, top_edges=top_edges, edge_type="REPLY_TO", **kwargs)


class BottomTemporalEdgeFilter(GenericBottomEdgeFilter):
    def __init__(self, *args, top_edges=None, **kwargs):
        GenericBottomEdgeFilter.__init__(*args, top_edges=top_edges, edge_type="TEMPORAL", **kwargs)


class BottomSameCommentFilter(GenericBottomEdgeFilter):
    def __init__(self, *args, top_edges=None, **kwargs):
        GenericBottomEdgeFilter.__init__(self, *args, top_edges=top_edges, edge_type="SAME_COMMENT", **kwargs)


class BottomSameArticleEdgeFilter(GenericBottomEdgeFilter):
    def __init__(self, *args, top_edges=None, **kwargs):
        GenericBottomEdgeFilter.__init__(self, *args, top_edges=top_edges, edge_type="SAME_ARTICLE", **kwargs)


class BottomSameGroupEdgeFilter(GenericBottomEdgeFilter):
    def __init__(self, *args, top_edges=None, **kwargs):
        GenericBottomEdgeFilter.__init__(*args, top_edges=top_edges, edge_type="SAME_GROUP", **kwargs)


#
# Node Filters
#
class GenericNodeWeightFilter(Modifier):
    def __init__(self, *args, threshold=None, node_weight_type=None, strict=None, **kwargs):
        """
        Removes all edges connected to nodes of the specific type below a threshold
        :param args:
        :threshold: threshold weight value for nodes to filter from edges
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.threshold = self.conf_getfloat("threshold", threshold)
        self.node_weight_type = self.conf_get("node_weight_type", node_weight_type)
        self.strict = self.conf_getboolean("strict", strict)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'threshold={self.threshold}, '
                     f'strict_mode={strict} '
                     f'and node_weight_type={self.node_weight_type}')

    def modify(self, graph: GraphRepresentationType):
        relevant_nodes = [(graph.id2idx[comment.id], split_id) for comment in graph.comments
                          for split_id, split in enumerate(comment.splits)
                          if split.wgts[self.node_weight_type] >= self.threshold]

        if self.strict:
            graph.edges = [edge for edge in graph.edges
                           if edge.src in relevant_nodes and edge.tgt in relevant_nodes]
        else:
            graph.edges = [edge for edge in graph.edges
                           if edge.src in relevant_nodes and edge.tgt in relevant_nodes]

        return graph


class SizeFilter(GenericNodeWeightFilter):
    def __init__(self, *args, threshold=None, strict=None, **kwargs):
        super().__init__(*args, threshold=threshold, node_weight_type="SIZE", strict=strict, **kwargs)


class PageRankFilter(GenericNodeWeightFilter):
    def __init__(self, *args, threshold=None, strict=None, **kwargs):
        super().__init__(*args, threshold=threshold, node_weight_type="PAGERANK", strict=strict, **kwargs)


class DegreeCentralityFilter(GenericNodeWeightFilter):
    def __init__(self, *args, threshold=None, strict=None, **kwargs):
        super().__init__(*args, threshold=threshold, node_weight_type="DEGREE_CENTRALITY", strict=strict, **kwargs)


class RecencyFilter(GenericNodeWeightFilter):
    def __init__(self, *args, threshold=None, strict=None, **kwargs):
        super().__init__(*args, threshold=threshold, node_weight_type="RECENCY", strict=strict, **kwargs)


class VotesFilter(GenericNodeWeightFilter):
    def __init__(self, *args, threshold=None, strict=None, **kwargs):
        super().__init__(*args, threshold=threshold, node_weight_type="VOTES", strict=strict, **kwargs)


class ToxicityFilter(GenericNodeWeightFilter):
    def __init__(self, *args, threshold=None, strict=None, **kwargs):
        super().__init__(*args, threshold=threshold, node_weight_type="TOXICITY", strict=strict, **kwargs)


class GenericNodeWeightBottomFilter(Modifier):
    def __init__(self, *args, top_k=None, node_weight_type=None, strict=None, **kwargs):
        """
        Remove edges from a graph not connected to top-k nodes of the specified weight
        :param args:
        :node_weight_type: type of node weight
        :k: top k page-ranked items to choose
        :strict: filter edges strictly (only allow edges between top-k nodes) or not (edge only needs on top-k node)
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.node_weight_type = self.conf_get("node_weight_type", node_weight_type)
        self.top_k = self.conf_getint("top_k", top_k)
        self.strict = self.conf_getboolean('strict', strict)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'k={self.top_k} and strict={self.strict} '
                     f'on {self.node_weight_type}')

    def modify(self, graph: GraphRepresentationType):
        weights = {(graph.id2idx[comment.id], j): split.wgts[self.node_weight_type]
                   for comment in graph.comments for j, split in enumerate(comment.splits)}
        filtered_ranks = {k: v for k, v in sorted(weights.items(),
                                                  key=lambda item: item[1], reverse=True)[:self.top_k]}
        if self.strict:
            graph.edges = [edge for edge in graph.edges
                           if edge.src in filtered_ranks and edge.tgt in filtered_ranks]
        else:
            graph.edges = [edge for edge in graph.edges
                           if edge.src in filtered_ranks or edge.tgt in filtered_ranks]


class SizeBottomFilter(GenericNodeWeightBottomFilter):
    def __init__(self, *args, top_k=None, strict=None, **kwargs):
        super().__init__(*args, top_k=top_k, node_weight_type="SIZE", strict=strict, **kwargs)


class PageRankBottomFilter(GenericNodeWeightBottomFilter):
    def __init__(self, *args, top_k=None, strict=None, **kwargs):
        super().__init__(*args, top_k=top_k, node_weight_type="PAGERANK", strict=strict, **kwargs)


class DegreeCentralityBottomFilter(GenericNodeWeightBottomFilter):
    def __init__(self, *args, top_k=None, strict=None, **kwargs):
        super().__init__(*args, top_k=top_k, node_weight_type="DEGREE_CENTRALITY", strict=strict, **kwargs)


class RecencyBottomFilter(GenericNodeWeightBottomFilter):
    def __init__(self, *args, top_k=None, strict=None, **kwargs):
        super().__init__(*args, top_k=top_k, node_weight_type="RECENCY", strict=strict, **kwargs)


class VotesBottomFilter(GenericNodeWeightBottomFilter):
    def __init__(self, *args, top_k=None, strict=None, **kwargs):
        super().__init__(*args, top_k=top_k, node_weight_type="VOTES", strict=strict, **kwargs)


class ToxicityBottomFilter(GenericNodeWeightBottomFilter):
    def __init__(self, *args, top_k=None, strict=None, **kwargs):
        super().__init__(*args, top_k=top_k, node_weight_type="TOXICITY", strict=strict, **kwargs)

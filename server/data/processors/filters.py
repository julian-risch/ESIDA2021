import logging
from collections import defaultdict
from typing import List
import numpy as np
import scipy.sparse as sparse
import data.models as models
from data.processors import Modifier, GraphRepresentationType
from data.processors.ranking import build_edge_dict

logger = logging.getLogger('data.graph.filters')


class BottomReplyToEdgeFilter(Modifier):
    def __init__(self, *args, top_edges=None, **kwargs):
        """
        Filters all edges except top edges for specific edge type
        :param args:
        :param top_edges: the number of top edges to keep for each node
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.top_edges = self.conf_getint('top_edges', top_edges)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'top_edges={self.top_edges}')

    def modify(self, graph: GraphRepresentationType):
        filtered_edges = []
        edge_dict = build_edge_dict(graph)
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                node_edges = edge_dict[(graph.id2idx[comment.id], j)]
                node_edges = sorted(node_edges, key=lambda e: e.wgts.REPLY_TO, reverse=True)[
                             :self.top_edges]
                for edge in node_edges:
                    if edge not in filtered_edges:
                        filtered_edges.append(edge)

        graph.edges = filtered_edges


class BottomSimilarityEdgeFilter(Modifier):
    def __init__(self, *args, top_edges=None, **kwargs):
        """
        Filters all edges except top edges for specific edge type
        :param args:
        :param top_edges: the number of top edges to keep for each node
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.top_edges = self.conf_getint('d', top_edges)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'top_edges={self.top_edges}')

    def modify(self, graph: GraphRepresentationType):
        filtered_edges = []
        edge_dict = build_edge_dict(graph)

        # for node_id in graph.id2idx.keys():
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                node_edges = edge_dict[(graph.id2idx[comment.id], j)]
                node_edges = sorted(node_edges, key=lambda e: e.wgts.SIMILARITY, reverse=True)[
                             :self.top_edges]
                for edge in node_edges:
                    if edge not in filtered_edges:
                        filtered_edges.append(edge)
        graph.edges = filtered_edges

        return graph


# todo: add bottom edge filters for other edge types


class SimilarityEdgeFilter(Modifier):
    def __init__(self, *args, threshold=None, **kwargs):
        """
        Removes all edges of the specific type below a threshold
        :param args:
        :threshold: value for edges to filter
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.threshold = self.conf_getfloat("threshold", threshold)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'threshold={self.threshold}')

    @classmethod
    def short_name(cls) -> str:
        return 'sef'

    @classmethod
    def edge_type(cls) -> str:
        return "similarity"

    def modify(self, graph_to_modify: GraphRepresentationType):
        # note that edge_type is function call here and in BottomSimilarityEdgeFilter it can be an attribute

        graph_to_modify.edges = [edge for edge in graph_to_modify.edges if edge.wgts.similarity > self.threshold]
        # graph_to_modify.edges = [edge for edge in graph_to_modify.edges if edge.wgts[self.__class__.edge_type()][0] > self.threshold]
        return graph_to_modify


class PageRankFilter(Modifier):
    def __init__(self, *args, k=None, strict=None, **kwargs):
        """
        Remove edges from a graph not connected to top-k nodes
        :param args:
        :k: top k page-ranked items to choose
        :strict: filter edges strictly (only allow edges between top-k nodes) or not (edge only needs on top-k node)
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.k = self.conf_getint("k", k)
        self.strict = self.conf_getboolean('strict', strict)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'k={self.k} and strict={self.strict}')

    @classmethod
    def short_name(cls) -> str:
        return 'prf'

    @classmethod
    def split_type(cls) -> str:
        return "pagerank"

    def modify(self, graph: GraphRepresentationType):
        page_ranks = {(comment.id, j): split.wgts.PAGERANK
                      for comment in graph.comments for j, split in enumerate(comment.splits)}
        filtered_ranks = {k: v for k, v in sorted(page_ranks.items(),
                                                  key=lambda item: item[1], reverse=True)[:self.k]}

        if self.strict:
            graph.edges = [edge for edge in graph.edges
                           if edge.src in filtered_ranks and edge.tgt in filtered_ranks]
        else:
            graph.edges = [edge for edge in graph.edges
                           if edge.src in filtered_ranks or edge.tgt in filtered_ranks]

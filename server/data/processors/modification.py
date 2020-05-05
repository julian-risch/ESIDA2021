import logging
from collections import defaultdict
from typing import List
import numpy as np
import scipy.sparse as sparse
import data.models as models
from data.processors import Modifier
# from data.processors.graph import GraphRepresentation

logger = logging.getLogger('data.graph.comparator')


# helper functions
def node_to_sid(node: List[int] = None, a: int = None, b: int = None) -> str:
    if node:
        return f'{node[0]}|{node[1]}'
    else:
        return f'{a}|{b}'


def sid_to_nodes(sid: str = None) -> List[int]:
    return [int(node_id) for node_id in sid.split('|')]


def build_edge_dict(graph: "GraphRepresentation"):
    dic = defaultdict(list)
    for e in graph.edges:
        src = node_to_sid(e.src)
        tgt = node_to_sid(e.tgt)
        if e not in dic[src]:
            dic[src].append(e)
        if e not in dic[tgt]:
            dic[tgt].append(e)
    return dic


class PageRanker(Modifier):
    def pagerank(self, graph: "GraphRepresentation", type_of_edge: str):
        def edge_list_to_adjacence_matrix(edges, edge_type: str):
            # arr = np.array([[f'{edge.src[0]}|{edge.src[1]}', f'{edge.tgt[0]}|{edge.tgt[1]}', edge.wgts[edge_type]]
            #                 for edge in edges])
            nodes = set()
            arr = []
            for edge in edges:
                node_to_sid()
                src_sid = node_to_sid(edge.src)
                tgt_sid = node_to_sid(edge.tgt)
                nodes.add(src_sid)
                nodes.add(tgt_sid)
                arr.extend(np.array([src_sid, tgt_sid, edge.wgts[edge_type]]))

            arr = np.array(arr)

            shape = tuple(arr.max(axis=0)[:2] + 1)
            coo = sparse.coo_matrix((arr[:, 2], (arr[:, 0], arr[:, 1])), shape=shape,
                                    dtype=arr.dtype)
            return coo.to_dense(), nodes

        # todo: check if adjacence matrix works as intended
        adjacence_matrix, node_sids = edge_list_to_adjacence_matrix(graph.edges, type_of_edge)

        m = adjacence_matrix / adjacence_matrix.sum(axis=0, keepdims=1)
        n = m.shape[1]
        v = np.random.rand(n, 1)
        v = v / np.linalg.norm(v, 1)
        m_hat = (self.d * m + (1 - self.d) / n)
        for i in range(self.num_iterations):
            v = m_hat @ v
        ranks = {n: r[0] for n, r in zip(node_sids, v)}

        ranks = {k: v for k, v in sorted(ranks.items(), key=lambda item: item[1], reverse=True)}

        if self.normalize:
            values = list(ranks.values())
            v_max = np.max(values)
            v_min = np.min(values)
            if v_max == v_min:
                v_min = -1 + v_max
            ranks = {k: (v - v_min) / (v_max - v_min) + 0.001 for k, v in ranks.items()}

        # update node of graph with new weights for PageRank
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                # split.wgts[models.PAGERANK] = ranks[node_to_sid(node=None, a=comment.id, b=j)]
                split.wgts[models.SplitWeights.pagerank] = ranks[node_to_sid(node=None, a=comment.id, b=j)]

        return graph

    def __init__(self, *args, num_iterations: int = None, d: float = None, normalize=None, **kwargs):
        """
        Returns a graph with page-ranked node weights
        :param args:
        :param num_iterations: number of iteration for PageRank
        :d: d parameter for PageRank
        :normalize: normalize the PageRank values?
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.num_iterations = self.conf_getint('num_iterations', num_iterations)
        self.d = self.conf_getint('d', d)
        self.normalize = self.conf_getboolean('normalize', normalize)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'num_iterations={self.num_iterations}, d={self.d} and normalize={self.normalize}')

    @classmethod
    def short_name(cls) -> str:
        return 'pr'

    def modify(self, graph_to_modify: "GraphRepresentation") -> "GraphRepresentation":
        return self.pagerank(graph_to_modify, type_of_edge="similarity")


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

    def modify(self, graph_to_modify: "GraphRepresentation") -> "GraphRepresentation":
        page_ranks = {node_to_sid(node=None, a=comment.id, b=j): split.wgts[models.SplitWeights.pagerank]
                      for comment in graph_to_modify.comments for j, split in enumerate(comment.splits)}
        filtered_ranks = {k: v for k, v in sorted(page_ranks.items(), key=lambda item: item[1], reverse=True)[:self.k]}

        if self.strict:
            graph_to_modify.edges = [edge for edge in graph_to_modify.edges
                                     if node_to_sid(edge.src) in filtered_ranks and node_to_sid(edge.tgt) in filtered_ranks]
        else:
            graph_to_modify.edges = [edge for edge in graph_to_modify.edges
                                     if node_to_sid(edge.src) in filtered_ranks or node_to_sid(edge.tgt) in filtered_ranks]

        return graph_to_modify


class CentralityDegreeCalculator(Modifier):
    def __init__(self, *args, **kwargs):
        """
        Returns a graph with page-ranked node weights
        :param args:
        :param num_iterations: number of iteration for PageRank
        :d: d parameter for PageRank
        :normalize: normalize the PageRank values?
        :param kwargs:
        """
        super().__init__(*args, **kwargs)

        logger.debug(f'{self.__class__.__name__} initialised')

    @classmethod
    def short_name(cls) -> str:
        return 'pr'

    def degree_centralities(self, graph):
        counter_dict = defaultdict(int)
        for edge in graph.edges:
            counter_dict[node_to_sid(edge.tgt)] += 1
            counter_dict[node_to_sid(edge.src)] += 1

        # update node of graph with new weights for for degree centrality
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                split.wgts[models.SplitWeights.degreecentrality] = counter_dict[node_to_sid(node=None, a=comment.id, b=j)]

        return graph

    def modify(self, graph_to_modify: "GraphRepresentation") -> "GraphRepresentation":
        return self.degree_centralities(graph_to_modify)


# class EdgeFilter(Modifier):
#     def __init__(self, *args, thresholds, **kwargs):
#         """
#         Returns base_weight iff split_a and split_b are part of the same comment.
#         :param args:
#         :param kwargs:
#         """
#         super().__init__(*args, **kwargs)
#         self.thresholds = {models.EdgeType.SAME_COMMENT: 0.7,
#                            models.EdgeType.SAME_ARTICLE: 0.8,
#                            models.EdgeType.SIMILARITY: 0.9,
#                            models.EdgeType.SAME_GROUP: 0.1,
#                            models.EdgeType.REPLY_TO: 0.8}
#
#         logger.debug(f'{self.__class__.__name__} initialised with '
#                      f'{self.thresholds=}')
#
#     @classmethod
#     def short_name(cls) -> str:
#         return 'ef'
#
#     def modify(self, graph: "GraphRepresentation") -> "GraphRepresentation":
#         def within_thresholds(wgt_list: List[models.EdgeWeightType], thresholds: Dict[models.EdgeType, float]):
#             for wgt in wgt_list:
#                 if wgt[0] < thresholds[wgt[1]]:
#                     return False
#             return True
#
#         graph.edges = [edge for edge in graph.edges if within_thresholds(edge.wgts, thresholds=self.thresholds)]
#         return graph
#     # def remove_edges(self, textual=0.8, structural=0.96, temporal=7200):
#     #     # self.edges = [edge for edge in self.edges if edge.weights_bigger_as_threshold()]
#     #     self.edges = [edge for edge in self.edges
#     #                   if edge.weights["textual"] >= textual
#     #                   and edge.weights["structural"] >= structural
#     #                   and edge.weights["temporal"] <= temporal]

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

    def modify(self, graph_to_modify: "GraphRepresentation") -> "GraphRepresentation":
        # note that edge_type is function call here and in BottomSimilarityEdgeFilter it can be an attribute
        for e in graph_to_modify.edges:
            print(e.wgts[0][0])
        graph_to_modify.edges = [edge for edge in graph_to_modify.edges if edge.wgts[0][0] > self.threshold]
        # graph_to_modify.edges = [edge for edge in graph_to_modify.edges if edge.wgts[self.__class__.edge_type()][0] > self.threshold]
        return graph_to_modify


class BottomSimilarityEdgeFilter(Modifier):
    def __init__(self, *args,  top_edges=None, **kwargs):
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

    @classmethod
    def short_name(cls) -> str:
        return 'bsef'

    @classmethod
    def edge_type(cls) -> str:
        return "similarity"

    def modify(self, graph_to_modify: "GraphRepresentation") -> "GraphRepresentation":
        filtered_edges = []
        edge_dict = build_edge_dict(graph_to_modify)

        # for node_id in graph.id2idx.keys():
        for comment in graph_to_modify.comments:
            for j, split in enumerate(comment.splits):
                node_edges = edge_dict[node_to_sid(node=None, a=comment.id, b=j)]
                node_edges = sorted(node_edges, key=lambda e: e.wgts[self.__class__.edge_type()], reverse=True)[:self.top_edges]
                for edge in node_edges:
                    if edge not in filtered_edges:
                        filtered_edges.append(edge)
        graph_to_modify.edges = filtered_edges

        return graph_to_modify


class BottomReplyToEdgeFilter(Modifier):
    def __init__(self, *args,  top_edges=None, **kwargs):
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

    @classmethod
    def short_name(cls) -> str:
        return 'brtef'

    @classmethod
    def edge_type(cls) -> str:
        return "reply_to"

    def modify(self, graph_to_modify: "GraphRepresentation") -> "GraphRepresentation":
        filtered_edges = []
        edge_dict = build_edge_dict(graph_to_modify)
        for comment in graph_to_modify.comments:
            for j, split in enumerate(comment.splits):
                node_edges = edge_dict[node_to_sid(node=None, a=graph_to_modify.id2idx[comment.id], b=j)]
                print(node_edges)
                node_edges = sorted(node_edges, key=lambda e: e.wgts[self.__class__.edge_type()], reverse=True)[
                             :self.top_edges]
                for edge in node_edges:
                    if edge not in filtered_edges:
                        filtered_edges.append(edge)
        print(self.top_edges, len(filtered_edges))
        graph_to_modify.edges = filtered_edges

        return graph_to_modify

# todo: add bottom edge filters for other edge types


class Representives:
    @classmethod
    def concanative(cls, node, removed_nodes):
        node.text += " | " + " | ".join([removed_node.text for removed_node in removed_nodes])
        return node

    # @classmethod
    # def avg_embedding(cls, node, removed_nodes):
    #     nodes = list(removed_nodes)
    #     nodes.append(node)
    #
    #     vecs = [n.vector for n in nodes]
    #     avg = Vector.average(vecs)
    #
    #     sims = [avg.cos_sim(vec) for vec in vecs]
    #     max_id = sims.index(max(sims))
    #     return nodes[max_id]


# I think the clustering result should be passed to the frontend and not modify the graph at all
class NodeMerger(Modifier):
    def __init__(self, *args, textual_threshold: float = None, structural_threshold: float = None, temporal_threshold: int = None, **kwargs):
        """
        Merges nodes together
        :param args:
        :param textual_threshold: threshold for textual similarity
        :param structural_threshold: threshold for structural similarity
        :param temporal_threshold: threshold for temporal similarity
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.textual_threshold = self.conf_getfloat('textual_threshold', textual_threshold)
        self.structural_threshold = self.conf_getfloat('structural_threshold', structural_threshold)
        self.temporal_threshold = self.conf_getfloat('temporal_threshold', temporal_threshold)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'textual_threshold={self.textual_threshold}, structural_threshold={self.structural_threshold} '
                     f'and temporal_threshold={self.temporal_threshold}')

    @classmethod
    def short_name(cls) -> str:
        return 'nm'

    def modify(self, graph_to_modify: "GraphRepresentation") -> "GraphRepresentation":
        clusters = self.merge_nodes(graph_to_modify, textual=0.8, structural=0.8, temporal=3600, conj="and", representive_weight="pagerank")
        return graph_to_modify

    def merge_nodes(self, graph: "GraphRepresentation", textual=0.8, structural=0.8, temporal=3600, conj="and", representive_weight="pagerank"):
        def clusters(to_replace):
            finalized_replacements = {}
            for k, v in to_replace.items():
                for k2, v2 in to_replace.items():
                    if v == k2:
                        finalized_replacements[k] = v2

                if k not in finalized_replacements:
                    finalized_replacements[k] = v

            cluster = defaultdict(list)
            for k, v in to_replace.items():
                cluster[v].append(k)

            for k, v in cluster.items():
                for k2, v2 in cluster.items():
                    if k != k2 and k in v2:
                        cluster[k2].extend(v)
                        cluster[k].clear()
            # print(cluster)
            # replacement -> [to_be_replaced_1, ..., to_be_replaced_n]
            cluster = {k: l for k, l in cluster.items() if len(l) > 0}

            # to_be_replaced -> replacement
            finalized_replacements = {v: k for k, l in cluster.items() for v in l}

            return cluster, finalized_replacements

        edge_dict = build_edge_dict(graph)

        replacements = {}

        # investigate what can be replaced with what
        for edge in graph.edges:
            if conj == "or":
                filter_bool = edge.wgts[models.EdgeWeights.similarity] > textual \
                              or edge.wgts[models.EdgeWeights.reply_to] > structural \
                              or edge.wgts[models.EdgeWeights.same_comment] > structural \
                              or edge.wgts[models.EdgeWeights.same_article] > structural \
                              or edge.wgts[models.EdgeWeights.same_group] > structural \
                              or edge.wgts[models.EdgeWeights.temporal] < temporal
            else:
                filter_bool = edge.wgts[models.EdgeWeights.similarity] > textual \
                              and edge.wgts[models.EdgeWeights.reply_to] > structural \
                              and edge.wgts[models.EdgeWeights.same_comment] > structural \
                              and edge.wgts[models.EdgeWeights.same_article] > structural \
                              and edge.wgts[models.EdgeWeights.same_group] > structural \
                              and edge.wgts[models.EdgeWeights.temporal] < temporal

            if filter_bool:
                source = edge.src
                target = edge.tgt

                if source is None or target is None:
                    continue

                if source == target:
                    edge.src = None
                    edge.tgt = None
                    continue

                source_weight = graph.comments[source[0]].splits[source[1]].wgts[representive_weight]
                target_weight = graph.comments[target[0]].splits[target[1]].wgts[representive_weight]

                if source_weight > target_weight:
                    use = source
                    drop = target
                else:
                    use = target
                    drop = source

                if use == drop:
                    raise UserWarning("use and drop same!")

                replacements[node_to_sid(drop)] = node_to_sid(use)

        # use only replacements that cannot be replaced by others
        cluster, final_replacements = clusters(replacements)
        #   # replace nodes in edges
        for edge in graph.edges:
            if node_to_sid(edge.src) in final_replacements.keys():
                edge.src = sid_to_nodes(final_replacements[edge.src])

            if node_to_sid(edge.tgt) in final_replacements.keys():
                edge.tgt = sid_to_nodes(final_replacements[edge.tgt])

        #   # remove nodes that should be replaced and memorize them
        # remove_dict = defaultdict(list)
        # for node in graph.nodes:
        #     if node.id in final_replacements.keys():
        #         remove_dict[final_replacements[node.id]].append(node)
        #         graph.nodes.remove(node)
                # merge value_ids with otherwise deleted information
        #   # obsolete node merge
        # for node in graph.nodes:
        #     if node.id in remove_dict.keys():
        #         replaced_nodes = remove_dict[node.id]
                # representant = Representives.avg_embedding(node, replaced_nodes)
                # representant = Representives.concanative(node, replaced_nodes)
                # node.text = representant.text
                # node.vector = representant.vector

        #   # final filtering
        graph.edges = list([e for e in graph.edges if not (e.src is None or e.tgt is None)
                           and self.weights_bigger_as_threshold(e, threshold=0)
                           and node_to_sid(e.src) != node_to_sid(e.tgt)])

        return cluster

    def weights_bigger_as_threshold(self, edge: models.Edge, threshold: float = 0, edge_types=None):
        if edge_types is None:
            edge_types = [models.EdgeWeights.similarity, models.EdgeWeights.same_comment]
        choosen_weights = [edge.wgts[edge_type] for edge_type in edge_types]

        # boolean_and
        for w in choosen_weights:
            if w <= threshold:
                return False
        return True




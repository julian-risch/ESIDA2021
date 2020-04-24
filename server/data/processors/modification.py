import logging
from collections import defaultdict

import numpy as np
import scipy.sparse as sparse
import data.models as models
from data.processors import Modifier

logger = logging.getLogger('data.graph.comparator')


class PageRanker(Modifier):
    def pagerank(self, graph):
        #todo: replace graph.nodes properly
        # FIXME: use proper adjacence matrix
        adjacence_matrix = [] # np.array of adjacence matrix



        m = adjacence_matrix / adjacence_matrix.sum(axis=0, keepdims=1)
        n = m.shape[1]
        v = np.random.rand(n, 1)
        v = v / np.linalg.norm(v, 1)
        m_hat = (self.d * m + (1 - self.d) / n)
        for i in range(self.num_iterations):
            v = m_hat @ v
        ranks = {n: r[0] for n, r in zip(graph.id2idx.keys(), v)}

        ranks = {k: v for k, v in sorted(ranks.items(), key=lambda item: item[1], reverse=True)}

        if self.normalize:
            values = list(ranks.values())
            v_max = np.max(values)
            v_min = np.min(values)
            if v_max == v_min:
                v_min = -1 + v_max
            ranks = {k: (v - v_min) / (v_max - v_min) + 0.001 for k, v in ranks.items()}

        # update node of graph with new weights for PageRank
        for node_id in graph.id2idx:
            graph.comments[node_id].splits[0].wgts[models.SplitType.PAGERANK] = ranks[node_id]

            # node.wgts[models.NodeType.PAGERANK] = ranks[node.id]

    def __init__(self, *args, num_iterations: int = None, d: float = None, normalize=None, **kwargs):
        """
        Returns a graph with node pageranked node weights
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

    def modify(self, graph: models.Graph) -> models.Graph:
        self.pagerank(graph)
        return graph


def build_edge_dict(graph: models.Graph):
    dic = defaultdict(list)
    for e in graph.edges:
        if e not in dic[e.src]:
            dic[e.src].append(e)
        if e not in dic[e.tgt]:
            dic[e.tgt].append(e)
    return dic


# class EdgeFilter(Modifier):
#     def __init__(self, *args, thresholds, **kwargs):
#         """
#         Returns base_weight iff split_a and split_b are part of the same comment.
#         :param args:
#         :param kwargs:
#         """
#         super().__init__(*args, **kwargs)
#         # fixme: do this in a way that mathces config files
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
#     def modify(self, graph: models.Graph) -> models.Graph:
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
        Returns base_weight iff split_a and split_b are part of the same comment.
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
    def edge_type(cls) -> models.EdgeType:
        return models.EdgeType.SIMILARITY

    def modify(self, graph: models.Graph) -> models.Graph:
        # FIXME: dont understand why edge_type is function call here and in BottomSimilarityEdgeFilter attribute
        graph.edges = [edge for edge in graph.edges if edge.wgts[self.__class__.edge_type()] > self.threshold]
        return graph


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
    def edge_type(cls) -> models.EdgeType:
        return models.EdgeType.SIMILARITY

    def modify(self, graph: models.Graph) -> models.Graph:
        filtered_edges = []
        edge_dict = build_edge_dict(graph)

        # FIXME: check if node index correctly choosen
        for node_id in graph.id2idx.keys():
            node_edges = edge_dict[node_id]
            node_edges = sorted(node_edges, key=lambda e: e.wgts[self.__class__.edge_type()], reverse=True)[:self.top_edges]
            for edge in node_edges:
                if edge not in filtered_edges:
                    filtered_edges.append(edge)
        graph.edges = filtered_edges

        return graph


class BottomReplyToEdgeFilter(Modifier):
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
        return 'brtef'

    @classmethod
    def edge_type(cls) -> models.EdgeType:
        return models.EdgeType.REPLY_TO

    def modify(self, graph: models.Graph) -> models.Graph:
        filtered_edges = []
        edge_dict = build_edge_dict(graph)

        # FIXME: check if node index correctly choosen
        for node_id in graph.id2idx.keys():
            node_edges = edge_dict[node_id]
            node_edges = sorted(node_edges, key=lambda e: e.wgts[self.__class__.edge_type], reverse=True)[:self.top_edges]
            for edge in node_edges:
                if edge not in filtered_edges:
                    filtered_edges.append(edge)
        graph.edges = filtered_edges

        return graph

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


class NodeMerger(Modifier):
    def __init__(self, *args, base_weight=None, only_consecutive: bool = None, **kwargs):
        """
        Returns base_weight iff split_a and split_b are part of the same comment.
        :param args:
        :param base_weight: weight to attach
        :param only_consecutive: only return weight of splits are consecutive
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.base_weight = self.conf_getfloat('base_weight', base_weight)
        self.only_consecutive = self.conf_getboolean('only_consecutive', only_consecutive)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'base_weight: {self.base_weight} and only_consecutive: {self.only_consecutive}')

    @classmethod
    def short_name(cls) -> str:
        return 'nm'

    def modify(self, graph: models.Graph) -> models.Graph:
        return graph

    def merge_nodes(self, graph, textual=0.8, structural=0.8, temporal=3600, representative_function=len, conj="and"):
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

        # FIXME: user proper node dict
        node_dict = graph.id2idx
        edge_dict = build_edge_dict(graph)

        replacements = {}

        # investigate what can be replaced with what
        for edge in graph.edges:

            if conj == "or":
                filter_bool = edge.wgts[models.EdgeType.SIMILARITY] > textual \
                              or edge.wgts[models.EdgeType.REPLY_TO] > structural \
                              or edge.wgts[models.EdgeType.SAME_COMMENT] > structural \
                              or edge.wgts[models.EdgeType.SAME_ARTICLE] > structural \
                              or edge.wgts[models.EdgeType.SAME_GROUP] > structural \
                              or edge.wgts[models.EdgeType.TEMPORAL] < temporal
            else:
                filter_bool = edge.wgts[models.EdgeType.SIMILARITY] > textual \
                              and edge.wgts[models.EdgeType.REPLY_TO] > structural \
                              and edge.wgts[models.EdgeType.SAME_COMMENT] > structural \
                              and edge.wgts[models.EdgeType.SAME_ARTICLE] > structural \
                              and edge.wgts[models.EdgeType.SAME_GROUP] > structural \
                              and edge.wgts[models.EdgeType.TEMPORAL] < temporal

            if filter_bool:
                source = node_dict.get(edge.src)
                target = node_dict.get(edge.tgt)

                if source is None or target is None:
                    continue

                if source == target:
                    edge.src = None
                    edge.tgt = None
                    continue

                # todo: read textual attribute correctly from nodes
                # graph.comments[graph.id2idx[source]].text
                if representative_function(source.text) > representative_function(target.text):
                    use = source
                    drop = target
                else:
                    use = target
                    drop = source

                if use == drop:
                    raise UserWarning("use and drop same!")

                replacements[drop.node_id] = use.node_id

        # use only replacements that cannot be replaced by others
        _, final_replacements = clusters(replacements)
        # replace nodes in edges
        for edge in graph.edges:
            if edge.src in final_replacements.keys():
                edge.src = final_replacements[edge.src]

            if edge.tgt in final_replacements.keys():
                edge.tgt = final_replacements[edge.tgt]

        # remove nodes that should be replaced and memorize them
        remove_dict = defaultdict(list)
        for node in graph.nodes:
            if node.id in final_replacements.keys():
                remove_dict[final_replacements[node.id]].append(node)
                graph.nodes.remove(node)
                # merge value_ids with otherwise deleted information

        # node merge
        for node in graph.nodes:
            if node.id in remove_dict.keys():
                replaced_nodes = remove_dict[node.id]
                # representant = Representives.avg_embedding(node, replaced_nodes)
                representant = Representives.concanative(node, replaced_nodes)
                # todo: set text and vector of node
                # node.text = representant.text
                # node.vector = representant.vector

        # final filtering
        graph.edges = list([e for e in graph.edges if not (e.source_id is None or e.target_id is None)
                           and self.weights_bigger_as_threshold(e, threshold=0)
                           and e.source_id != e.target_id])
        graph.nodes = [node for node in graph.nodes if node.node_id in edge_dict]
        # todo: update index
        # graph.id2idx = ...

        return None

    def weights_bigger_as_threshold(self, edge: models.Edge, threshold: float = 0, edge_types=None):
        if edge_types is None:
            edge_types = [models.EdgeType.SIMILARITY, models.EdgeType.SAME_COMMENT]
        choosen_weights = [edge.wgts[edge_type] for edge_type in edge_types]

        # boolean_and
        for w in choosen_weights:
            if w <= threshold:
                return False
        return True




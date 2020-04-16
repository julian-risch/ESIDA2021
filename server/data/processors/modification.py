from collections import defaultdict

from data.processors import Modifier
import data.models as models
from typing import List, Dict
import logging
import numpy as np

logger = logging.getLogger('data.graph.comparator')


# class AModifiyer(Modifier):
#     def __init__(self, *args, base_weight=None, only_consecutive: bool = None, **kwargs):
#         """
#         Returns base_weight iff split_a and split_b are part of the same comment.
#         :param args:
#         :param base_weight: weight to attach
#         :param only_consecutive: only return weight of splits are consecutive
#         :param kwargs:
#         """
#         super().__init__(*args, **kwargs)
#         self.base_weight = self.conf_getfloat('base_weight', base_weight)
#         self.only_consecutive = self.conf_getboolean('only_consecutive', only_consecutive)
#
#         logger.debug(f'{self.__class__.__name__} initialised with '
#                      f'base_weight: {self.base_weight} and only_consecutive: {self.only_consecutive}')
#
#     @classmethod
#     def short_name(cls) -> str:
#         return 'sc'
#
#     @classmethod
#     def edge_type(cls) -> models.EdgeType:
#         return models.EdgeType.SAME_COMMENT
#
#     def modify(self, graph: models.Graph) -> models.Graph:
#         return graph

class PageRanker(Modifier):
    def pagerank(self, graph, num_iterations: int = 100, d: float = 0.85, normalize=True):
        m = graph.adjacence_matrix / graph.adjacence_matrix.sum(axis=0, keepdims=1)
        n = m.shape[1]
        v = np.random.rand(n, 1)
        v = v / np.linalg.norm(v, 1)
        m_hat = (d * m + (1 - d) / n)
        for i in range(num_iterations):
            v = m_hat @ v
        ranks = {n.node_id: r[0] for n, r in zip(graph.nodes, v)}

        ranks = {k: v for k, v in sorted(ranks.items(), key=lambda item: item[1], reverse=True)}

        if normalize:
            values = list(ranks.values())
            v_max = np.max(values)
            v_min = np.min(values)
            if v_max == v_min:
                v_min = -1 + v_max
            ranks = {k: (v - v_min) / (v_max - v_min) + 0.001 for k, v in ranks.items()}

        # update Graph
        for node_id in graph.id2idx:
            if node_id.weights is None:
                node_id.weights = {}

            node_id.weights["pagerank"] = ranks[node_id]

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
        return 'pr'

    def modify(self, graph: models.Graph) -> models.Graph:
        return graph


def build_edge_dict(graph: models.Graph):
    dic = defaultdict(list)
    for e in graph.edges:
        if e not in dic[e.src]:
            dic[e.src].append(e)
        if e not in dic[e.tgt]:
            dic[e.tgt].append(e)
    return dic


class EdgeFilter(Modifier):
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
        return 'ef'

    def modify(self, graph: models.Graph) -> models.Graph:
        def within_thresholds(wgt_list: List[models.EdgeWeightType], thresholds: Dict[models.EdgeType, float]):
            for wgt in wgt_list:
                if wgt[0] < thresholds[wgt[1]]:
                    return False
            return True

        example_thresholds = {models.EdgeType.SAME_COMMENT: 0.7,
                              models.EdgeType.SAME_ARTICLE: 0.8,
                              models.EdgeType.SIMILARITY: 0.9,
                              models.EdgeType.SAME_GROUP: 0.1,
                              models.EdgeType.REPLY_TO: 0.8}

        graph.edges = [edge for edge in graph.edges if within_thresholds(edge.wgts, thresholds=example_thresholds)]
        return graph
    # def remove_edges(self, textual=0.8, structural=0.96, temporal=7200):
    #     # self.edges = [edge for edge in self.edges if edge.weights_bigger_as_threshold()]
    #     self.edges = [edge for edge in self.edges
    #                   if edge.weights["textual"] >= textual
    #                   and edge.weights["structural"] >= structural
    #                   and edge.weights["temporal"] <= temporal]


class BottomEdgeFilter(Modifier):
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
        return 'bef'

    def modify(self, graph: models.Graph, top_edges=5, edge_type=models.EdgeType.SIMILARITY) -> models.Graph:
        filtered_edges = []
        edge_dict = build_edge_dict(graph)

        # FIXME: check if node index correctly choosen
        for node_id in graph.id2idx.keys():
            node_edges = edge_dict[node_id]
            node_edges = sorted(node_edges, key=lambda e: e.wgts[edge_type], reverse=True)[:top_edges]
            for edge in node_edges:
                if edge not in filtered_edges:
                    filtered_edges.append(edge)
        graph.edges = filtered_edges

        return graph


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

    def modify(self, graph: models.Graph, top_edges=5, edge_type=models.EdgeType.SIMILARITY) -> models.Graph:
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

            # FIXME: user edge weights correctly
            if conj == "or":
                filter_bool = edge.weights["textual"] > textual or edge.weights["structural"] > structural or \
                              edge.weights["temporal"] < temporal
            else:
                filter_bool = edge.weights["textual"] > textual and edge.weights["structural"] > structural and \
                              edge.weights["temporal"] < temporal

            # todo: replace use of node class with node id
            if filter_bool:
                source = node_dict.get(edge.src)
                target = node_dict.get(edge.tgt)

                if source is None or target is None:
                    continue

                if source == target:
                    edge.src = None
                    edge.tgt = None
                    continue

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
            if edge.source_id in final_replacements.keys():
                edge.src = final_replacements[edge.src]

            if edge.target_id in final_replacements.keys():
                edge.tgt = final_replacements[edge.tgt]

        # remove nodes that should be replaced and memorize them
        remove_dict = defaultdict(list)
        for node in graph.nodes:
            if node.node_id in final_replacements.keys():
                remove_dict[final_replacements[node.node_id]].append(node)
                graph.nodes.remove(node)
                # merge value_ids with otherwise deleted information

        # node merge
        for node in graph.nodes:
            if node.node_id in remove_dict.keys():
                replaced_nodes = remove_dict[node.node_id]
                # representant = Representives.avg_embedding(node, replaced_nodes)
                representant = Representives.concanative(node, replaced_nodes)
                node.text = representant.text
                node.vector = representant.vector

        # final filtering
        # self.edges = list([e for e in self.edges if not (e.source_id is None or e.target_id is None)
        #                    and e.weights_bigger_as_threshold(threshold=0,
        #                                                      aggregate_function=boolean_or)
        #                    and e.source_id != e.target_id])
        # self.nodes = [node for node in self.nodes if node.node_id in edge_dict]

        return None

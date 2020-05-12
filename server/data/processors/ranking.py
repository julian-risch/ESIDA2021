import logging
from collections import defaultdict
from typing import List, Callable, Tuple
import numpy as np
import scipy.sparse as sparse
import data.models as models
from data.processors import Modifier, GraphRepresentationType

logger = logging.getLogger('data.graph.modification')


# helper functions
def node_to_sid(node: Tuple[int, int] = None, a: int = None, b: int = None) -> str:
    if node:
        return f'{node[0]}|{node[1]}'
    else:
        return f'{a}|{b}'


def sid_to_nodes(sid: str = None) -> Tuple[int, int]:
    s = sid.split('|')
    return int(s[0]), int(s[1])


def build_edge_dict(graph):
    dic = defaultdict(list)
    for e in graph.edges:
        src = node_to_sid(e.src)
        tgt = node_to_sid(e.tgt)
        if e not in dic[src]:
            dic[src].append(e)
        if e not in dic[tgt]:
            dic[tgt].append(e)
    return dic


def edge_list_to_adjacency_matrix(edges, get_weight: Callable[[models.EdgeWeights], float]):
    nodes = set()
    arr = []
    for edge in edges:
        node_to_sid()
        src_sid = node_to_sid(edge.src)
        tgt_sid = node_to_sid(edge.tgt)
        nodes.add(src_sid)
        nodes.add(tgt_sid)
        arr.extend(np.array([src_sid, tgt_sid, get_weight(edge)]))

    arr = np.array(arr)

    shape = tuple(arr.max(axis=0)[:2] + 1)
    coo = sparse.coo_matrix((arr[:, 2], (arr[:, 0], arr[:, 1])), shape=shape,
                            dtype=arr.dtype)
    return coo.to_dense(), nodes


class PageRanker(Modifier):
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
        self.d = self.conf_getfloat('d', d)
        self.normalize = self.conf_getboolean('normalize', normalize)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'num_iterations={self.num_iterations}, d={self.d} and normalize={self.normalize}')

    def modify(self, graph: GraphRepresentationType):

        adjacence_matrix, node_sids = edge_list_to_adjacency_matrix(graph.edges, lambda e: e.similarity)

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
                split.wgts.pagerank = ranks[node_to_sid(node=None, a=comment.id, b=j)]


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

    def modify(self, graph: GraphRepresentationType):
        counter_dict = defaultdict(int)
        for edge in graph.edges:
            counter_dict[node_to_sid(edge.tgt)] += 1
            counter_dict[node_to_sid(edge.src)] += 1

        # update node of graph with new weights for degree centrality
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                split.wgts.degree_centrality = counter_dict[node_to_sid(node=None, a=comment.id, b=j)]


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
    def __init__(self, *args, textual_threshold: float = None, structural_threshold: float = None,
                 temporal_threshold: int = None, **kwargs):
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

    @staticmethod
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

    def modify(self, graph: GraphRepresentationType):
        # FIXME: these variables should be class variables and configurable with config
        textual = 0.8
        structural = 0.8
        temporal = 3600
        conj = "and",
        representive_weight = "pagerank"

        replacements = {}

        # investigate what can be replaced with what
        for edge in graph.edges:
            if conj == "or":
                filter_bool = edge.wgts.similarity > textual \
                              or edge.wgts.reply_to > structural \
                              or edge.wgts.same_comment > structural \
                              or edge.wgts.same_article > structural \
                              or edge.wgts.same_group > structural \
                              or edge.wgts.temporal < temporal
            else:
                filter_bool = edge.wgts.similarity > textual \
                              and edge.wgts.reply_to > structural \
                              and edge.wgts.same_comment > structural \
                              and edge.wgts.same_article > structural \
                              and edge.wgts.same_group > structural \
                              and edge.wgts.temporal < temporal

            if filter_bool:
                source: Tuple[int, int] = edge.src
                target: Tuple[int, int] = edge.tgt

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
        cluster, final_replacements = self.clusters(replacements)
        #   # replace nodes in edges
        for edge in graph.edges:
            if node_to_sid(edge.src) in final_replacements.keys():
                edge.src = sid_to_nodes(final_replacements[edge.src])

            if node_to_sid(edge.tgt) in final_replacements.keys():
                edge.tgt = sid_to_nodes(final_replacements[edge.tgt])

        #   # final filtering
        graph.edges = list([e for e in graph.edges if not (e.src is None or e.tgt is None)
                            and self.weights_bigger_as_threshold(e, threshold=0)
                            and node_to_sid(e.src) != node_to_sid(e.tgt)])

    def weights_bigger_as_threshold(self, edge: models.Edge, threshold: float = 0, edge_types=None):
        if edge_types is None:
            edge_types = [models.EdgeWeights.similarity, models.EdgeWeights.same_comment]
        choosen_weights = [edge.wgts[edge_type] for edge_type in edge_types]

        # boolean_and
        for w in choosen_weights:
            if w <= threshold:
                return False
        return True

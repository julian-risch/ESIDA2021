import logging
from collections import defaultdict, OrderedDict
from operator import itemgetter
from typing import List, Callable, Tuple
import numpy as np
import scipy.sparse as sparse
import data.models as models
from data.processors import Modifier, GraphRepresentationType
from scipy import sparse
from fast_pagerank import pagerank, pagerank_power
logger = logging.getLogger('data.graph.ranking')


def build_edge_dict(graph):
    dic = defaultdict(list)
    for e in graph.edges:
        if e not in dic[e.src]:
            dic[e.src].append(e)
        if e not in dic[e.tgt]:
            dic[e.tgt].append(e)
    return dic


class PageRanker(Modifier):
    def __init__(self, *args, num_iterations: int = None, d: float = None, normalize=None, edge_type=None, **kwargs):
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
        self.edge_type = self.conf_get('edge_type', edge_type)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'num_iterations={self.num_iterations}, d={self.d} and normalize={self.normalize}')


    def page_rank_fast(self, graph: GraphRepresentationType):
        def edge_list_to_adjacency_list(edge_type):
            adjacency_weights = []
            adjacency_edges = []

            node_counter = 0
            node_index = {}
            for c in graph.comments:
                for split_id, _ in enumerate(c.splits):
                    node_index[(graph.id2idx[c.id], split_id)] = node_counter
                    node_counter += 1
            for e in graph.edges:
                weight = e.wgts[edge_type]
                if weight:
                    adjacency_edges.append([node_index[e.src], node_index[e.tgt]])
                    adjacency_weights.append(weight)

            return np.array(adjacency_edges), adjacency_weights, node_index

        adjacency_matrix, weights, int_index = edge_list_to_adjacency_list(self.edge_type)
        csr_graph = sparse.csr_matrix((weights, (adjacency_matrix[:, 0], adjacency_matrix[:, 1])),
                                      shape=(len(int_index.keys()), len(int_index.keys())))
        pr = pagerank(csr_graph, p=self.d)
        # pr = pagerank_power(G, p=0.85, tol=1e-6, max_iter=self.num_iterations)

        # update node of graph with new weights for PageRank
        counter = 0
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                split.wgts.PAGERANK = pr[counter]
                counter += 1

    def modify(self, graph: GraphRepresentationType):
        self.page_rank_fast(graph)


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
            counter_dict[edge.tgt] += 1
            counter_dict[edge.src] += 1
        # update node of graph with new weights for degree centrality
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                split.wgts.DEGREE_CENTRALITY = counter_dict[(graph.id2idx[comment.id], j)]


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
                filter_bool = edge.wgts.SIMILARITY > textual \
                              or edge.wgts.REPLY_TO > structural \
                              or edge.wgts.SAME_COMMENT > structural \
                              or edge.wgts.SAME_ARTICLE > structural \
                              or edge.wgts.SAME_GROUP > structural \
                              or edge.wgts.TEMPORAL < temporal
            else:
                filter_bool = edge.wgts.SIMILARITY > textual \
                              and edge.wgts.REPLY_TO > structural \
                              and edge.wgts.SAME_COMMENT > structural \
                              and edge.wgts.SAME_ARTICLE > structural \
                              and edge.wgts.SAME_GROUP > structural \
                              and edge.wgts.TEMPORAL < temporal

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

                replacements[drop] = use

        # use only replacements that cannot be replaced by others
        cluster, final_replacements = self.clusters(replacements)
        #   # replace nodes in edges
        for edge in graph.edges:
            if edge.src in final_replacements.keys():
                edge.src = final_replacements[edge.src]

            if edge.tgt in final_replacements.keys():
                edge.tgt = final_replacements[edge.tgt]

        #   # final filtering
        graph.edges = list([e for e in graph.edges if not (e.src is None or e.tgt is None)
                            and self.weights_bigger_as_threshold(e, threshold=0)
                            and e.src != e.tgt])

    def weights_bigger_as_threshold(self, edge: models.Edge, threshold: float = 0, edge_types=None):
        if edge_types is None:
            edge_types = [models.EdgeWeights.SIMILARITY, models.EdgeWeights.SAME_COMMENT]
        choosen_weights = [edge.wgts[edge_type] for edge_type in edge_types]

        # boolean_and
        for w in choosen_weights:
            if w <= threshold:
                return False
        return True

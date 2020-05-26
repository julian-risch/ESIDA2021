import logging
import re
from collections import defaultdict
from typing import List, Callable, Tuple
import numpy as np
import data.models as models
from data.processors import Modifier, GraphRepresentationType
import logging
from scipy import sparse
from fast_pagerank import pagerank, pagerank_power

logger = logging.getLogger('data.graph.clustering')


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

        # merge preperation:
        for comment in graph.comments:
            for split in comment.splits:
                split.wgts[models.SplitWeights.MERGE_ID] = 0


    def weights_bigger_as_threshold(self, edge: models.Edge, threshold: float = 0, edge_types=None):
        if edge_types is None:
            edge_types = [models.EdgeWeights.SIMILARITY, models.EdgeWeights.SAME_COMMENT]
        choosen_weights = [edge.wgts[edge_type] for edge_type in edge_types]

        # boolean_and
        for w in choosen_weights:
            if w <= threshold:
                return False
        return True

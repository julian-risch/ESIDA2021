import logging
import operator
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


class GenericNodeMerger(Modifier):
    def __init__(self, *args, threshold: float = None, smaller_as=None, edge_weight_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.threshold = self.conf_getfloat('threshold', threshold)
        self.smaller_as = self.conf_getboolean('smaller_as', smaller_as)
        self.edge_weight_type = self.conf_get('edge_weight_type', edge_weight_type)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'threshold={self.threshold}, smaller_as={self.smaller_as} '
                     f'and edge_weight_type={self.edge_weight_type}')

    def modify(self, graph: GraphRepresentationType):
        if self.smaller_as:
            operator_filter = operator.le
        else:
            operator_filter = operator.ge

        look_up = {}
        reverse_look_up = defaultdict(set)
        cluster_id = 0

        # FIXME: there is a bug preventing similary edges to be merged
        for edge in graph.edges:
            if edge.wgts[self.edge_weight_type] is None:
                continue
            if operator_filter(edge.wgts[self.edge_weight_type], self.threshold):
                # use old id if existing, else increment
                if edge.tgt in look_up or edge.src in look_up:
                    tgt_cluster = look_up.get(edge.tgt)
                    src_cluster = look_up.get(edge.src)

                    if tgt_cluster != src_cluster:

                        if src_cluster is not None and tgt_cluster is None:
                            concrete_id = src_cluster
                        elif src_cluster is None and tgt_cluster is not None:
                            concrete_id = tgt_cluster
                        else:
                            # actual merge by replacing cluster ids in lookup tables
                            concrete_id = src_cluster
                            nodes_to_change = reverse_look_up[tgt_cluster]
                            for node in nodes_to_change:
                                look_up[node] = concrete_id
                                reverse_look_up[concrete_id].add(node)

                            del reverse_look_up[tgt_cluster]
                    else:
                        concrete_id = src_cluster
                else:
                    concrete_id = cluster_id
                    cluster_id += 1

                reverse_look_up[concrete_id].add(edge.tgt)
                reverse_look_up[concrete_id].add(edge.src)
                look_up[edge.tgt] = concrete_id
                look_up[edge.src] = concrete_id

        # merge preperation:
        for comment in graph.comments:
            for j, split in enumerate(comment.splits):
                cluster = look_up.get((graph.id2idx[comment.id], j))
                # set id of nodes without cluster to -1
                if cluster is None:
                    cluster = -1
                split.wgts.MERGE_ID = cluster

        # print(reverse_look_up)
        return look_up, reverse_look_up


class SimilarityNodeMerger(GenericNodeMerger):
    def __init__(self, *args, threshold=None, smaller_as=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_weight_type="SIMILARITY", smaller_as=smaller_as, **kwargs)


class ReplyToNodeMerger(GenericNodeMerger):
    def __init__(self, *args, threshold=None, smaller_as=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_weight_type="REPLY_TO", smaller_as=smaller_as, **kwargs)


class SameCommentNodeMerger(GenericNodeMerger):
    def __init__(self, *args, threshold=None, smaller_as=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_weight_type="SAME_COMMENT", smaller_as=smaller_as, **kwargs)


class SameArticleNodeMerger(GenericNodeMerger):
    def __init__(self, *args, threshold=None, smaller_as=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_weight_type="SAME_ARTICLE", smaller_as=smaller_as, **kwargs)


class SameGroupNodeMerger(GenericNodeMerger):
    def __init__(self, *args, threshold=None, smaller_as=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_weight_type="SAME_GROUP", smaller_as=smaller_as, **kwargs)


class TemporalNodeMerger(GenericNodeMerger):
    def __init__(self, *args, threshold=None, smaller_as=None, **kwargs):
        super().__init__(*args, threshold=threshold, edge_weight_type="TEMPORAL", smaller_as=smaller_as, **kwargs)


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

import operator
from collections import defaultdict
from data.processors import Modifier, GraphRepresentationType
import logging
import networkx as nx

logger = logging.getLogger('data.graph.clustering')


class MultiNodeMerger(Modifier):
    def __init__(self, *args, reply_to_threshold=None, same_comment_threshold=None, same_article_threshold=None,
                 similarity_threshold=None, same_group_threshold=None, temporal_threshold=None, smaller_as=None,
                 conj_or=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.reply_to_threshold = self.conf_getfloat("reply_to_threshold", reply_to_threshold)
        self.same_comment_threshold = self.conf_getfloat("same_comment_threshold", same_comment_threshold)
        self.same_article_threshold = self.conf_getfloat("same_article_threshold", same_article_threshold)
        self.similarity_threshold = self.conf_getfloat("similarity_threshold", similarity_threshold)
        self.same_group_threshold = self.conf_getfloat("same_group_threshold", same_group_threshold)
        self.temporal_threshold = self.conf_getfloat("temporal_threshold", temporal_threshold)

        self.smaller_as = self.conf_getboolean('smaller_as', smaller_as)
        self.conj_or = self.conf_getboolean('conj_or', conj_or)

        self.threshold_dict = {"SIMILARITY": self.similarity_threshold,
                               "SAME_GROUP": self.same_group_threshold,
                               "TEMPORAL": self.temporal_threshold,
                               "SAME_ARTICLE": self.same_article_threshold,
                               "REPLY_TO": self.reply_to_threshold,
                               "SAME_COMMENT": self.same_comment_threshold}

        self.threshold_dict = {weight_type: threshold for weight_type, threshold in self.threshold_dict.items()
                               if threshold >= 0}

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'conj_or={self.conj_or}, smaller_as={self.smaller_as} '
                     f'and thresholds={self.threshold_dict}')

    def modify(self, graph: GraphRepresentationType):
        def loop_further_boolean(e):
            for weight_type, threshold in self.threshold_dict.items():
                temp_result = e.wgts[weight_type] is not None
                if self.conj_or and temp_result:
                    return True
                if not self.conj_or and not temp_result:
                    return False
            return not self.conj_or

        def filter_boolean(e, operator_func):
            for weight_type, threshold in self.threshold_dict.items():
                if e.wgts[weight_type] is None:
                    temp_result = False
                else:
                    temp_result = operator_func(e.wgts[weight_type], threshold)
                if self.conj_or and temp_result:
                    return True
                if not self.conj_or and not temp_result:
                    return False

            return not self.conj_or

        if self.smaller_as:
            operator_filter = operator.le
        else:
            operator_filter = operator.ge

        look_up = {}
        reverse_look_up = defaultdict(set)
        cluster_id = 0

        for edge in graph.edges:
            if not loop_further_boolean(edge):
                continue

            if filter_boolean(edge, operator_filter):
                # use old id if existing, else increment
                print(edge)
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

        return look_up, reverse_look_up


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


class GenericClusterer(Modifier):
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

        return look_up, reverse_look_up
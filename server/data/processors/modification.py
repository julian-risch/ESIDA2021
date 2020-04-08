from data.processors import Modifier
import data.models as models
from typing import List, Tuple
import logging
import numpy as np

logger = logging.getLogger('data.graph.comparator')


class AModifiyer(Modifier):
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
        return 'sc'

    @classmethod
    def edge_type(cls) -> models.EdgeType:
        return models.EdgeType.SAME_COMMENT

    def modify(self, graph: models.Graph) -> models.Graph:
        return graph

class AModifiyer(Modifier):
    def pagerank(self, num_iterations: int = 100, d: float = 0.85, normalize=True):
        m = self.adjacence_matrix / self.adjacence_matrix.sum(axis=0, keepdims=1)
        n = m.shape[1]
        v = np.random.rand(n, 1)
        v = v / np.linalg.norm(v, 1)
        m_hat = (d * m + (1 - d) / n)
        for i in range(num_iterations):
            v = m_hat @ v
        ranks = {n.node_id: r[0] for n, r in zip(self.nodes, v)}

        ranks = {k: v for k, v in sorted(ranks.items(), key=lambda item: item[1], reverse=True)}

        if normalize:
            values = list(ranks.values())
            v_max = np.max(values)
            v_min = np.min(values)
            if v_max == v_min:
                v_min = -1 + v_max
            ranks = {k: (v - v_min) / (v_max - v_min) + 0.001 for k, v in ranks.items()}

        # update Graph
        for node in self.nodes:
            if node.weights is None:
                node.weights = {}

            node.weights["pagerank"] = ranks[node.node_id]

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
        return 'sc'

    @classmethod
    def edge_type(cls) -> models.EdgeType:
        return models.EdgeType.SAME_COMMENT

    def modify(self, graph: models.Graph) -> models.Graph:
        return graph


from abc import ABC, abstractmethod
from common import config
import data.models as models
from typing import List, Union, Optional
import logging

logger = logging.getLogger('data.processor')


class GraphRepresentationType(ABC):
    def __init__(self, comments: List[models.CommentCached]):
        # full text comments might be needed by comparator
        self.orig_comments = comments

        # data for models.Graph
        self.comments: List[models.SplitComment] = []
        self.id2idx = {}
        self.edges: List[models.Edge] = []
        self.nodes = []


class Comparator(ABC):
    def __init__(self, conf=None):
        self.conf = conf

    @classmethod
    def is_on(cls, conf=None):
        return (conf or config).getboolean(cls.__name__, 'active', fallback=True)

    def conf_getboolean(self, key: str, param: bool) -> bool:
        if param is not None:
            return param
        return self.conf.getboolean(self.__class__.__name__, key)

    def conf_getfloat(self, key: str, param: float) -> float:
        if param is not None:
            return param
        return self.conf.getfloat(self.__class__.__name__, key)

    def conf_getint(self, key: str, param: int) -> int:
        if param is not None:
            return param
        return self.conf.getint(self.__class__.__name__, key)

    def conf_get(self, key: str, param: str) -> str:
        if param is not None:
            return param
        return self.conf.get(self.__class__.__name__, key)

    def update_edge_weights(self, edge_weights: models.EdgeWeights,
                            a: models.CommentCached, _a: models.SplitComment,
                            b: models.CommentCached, _b: models.SplitComment,
                            split_a, split_b):
        weight = self.compare(a, _a, b, _b, split_a, split_b)
        # logger.debug(f'update: {self.__class__.__name__} - {weight} - {edge}')
        if weight:
            # logger.debug(f'setting weight {weight} from {self.__class__.__name__}')
            self._set_weight(edge_weights, weight)
            # logger.debug(f'setting weight {weight} from {self.__class__.__name__} - {edge_weights}')

    @abstractmethod
    def _set_weight(self, edge: models.EdgeWeights, weight: float):
        raise NotImplementedError

    @abstractmethod
    def compare(self, a: models.CommentCached, _a: models.SplitComment,
                b: models.CommentCached, _b: models.SplitComment,
                split_a, split_b) -> float:
        """
        Returns a similarity score
        :param a: First comment to compare
        :param _a: Split version of first comment
        :param b: Second comment to compare
        :param _b: Split version of second comment
        :param split_a: index of sentence within comment a
        :param split_b: index of sentence within comment b
        :return: edge weight
        """
        raise NotImplementedError


class Modifier(ABC):
    def __init__(self, conf=None):
        self.conf = conf

    @classmethod
    def is_on(cls, conf=None):
        return (conf or config).getboolean(cls.__name__, 'active', fallback=True)

    def conf_getboolean(self, key: str, param: bool) -> bool:
        if param is not None:
            return param
        return self.conf.getboolean(self.__class__.__name__, key)

    def conf_getfloat(self, key: str, param: float) -> float:
        if param is not None:
            return param
        return self.conf.getfloat(self.__class__.__name__, key)

    def conf_getint(self, key: str, param: int) -> int:
        if param is not None:
            return param
        return self.conf.getint(self.__class__.__name__, key)

    def conf_get(self, key: str, param: str) -> str:
        if param is not None:
            return param
        return self.conf.get(self.__class__.__name__, key)

    @abstractmethod
    def modify(self, graph: GraphRepresentationType):
        """
        Returns the modified, original, graph
        """
        raise NotImplementedError

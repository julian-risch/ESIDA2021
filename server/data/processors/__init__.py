from abc import ABC, abstractmethod
from common import config
import data.models as models


class Comparator(ABC):
    def __init__(self, conf=None):
        self.conf = conf

    @classmethod
    def is_on(cls, conf=None):
        return (conf or config).getboolean(cls.__name__, 'active', fallback=True)

    def conf_getboolean(self, key, param):
        if param is not None:
            return param
        return self.conf.getboolean(self.__class__.__name__, key)

    def conf_getfloat(self, key, param):
        if param is not None:
            return param
        return self.conf.getfloat(self.__class__.__name__, key)

    def conf_get(self, key, param):
        if param is not None:
            return param
        return self.conf.get(self.__class__.__name__, key)

    @classmethod
    @abstractmethod
    def short_name(cls) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def edge_type(cls) -> models.EdgeWeights:
        raise NotImplementedError

    def compare(self, a: models.CommentCached, _a: models.SplitComment,
                b: models.CommentCached, _b: models.SplitComment,
                split_a, split_b) -> models.EdgeWeights:
        """
        Returns a similarity score
        :param a: First comment to compare
        :param _a: Split version of first comment
        :param b: Second comment to compare
        :param _b: Split version of second comment
        :param split_a: index of sentence within comment a
        :param split_b: index of sentence within comment b
        :return: edge type and weight
        """
        raise NotImplementedError


class Modifier(ABC):
    def __init__(self, conf=None):
        self.conf = conf

    @classmethod
    def is_on(cls, conf=None):
        return (conf or config).getboolean(cls.__name__, 'active', fallback=True)

    @classmethod
    def use(cls, modifiers_to_use, graph_to_modify, conf=None):
        modifiers = [modifier(conf=conf) for modifier in modifiers_to_use if modifier.is_on(conf)]
        for modifier in modifiers:
            modifier.modify(graph_to_modify)

    def conf_getboolean(self, key, param):
        if param is not None:
            return param
        return self.conf.getboolean(self.__class__.__name__, key)

    def conf_getfloat(self, key, param):
        if param is not None:
            return param
        return self.conf.getfloat(self.__class__.__name__, key)

    def conf_getint(self, key, param):
        if param is not None:
            return param
        return self.conf.getint(self.__class__.__name__, key)

    def conf_get(self, key, param):
        if param is not None:
            return param
        return self.conf.get(self.__class__.__name__, key)

    @classmethod
    @abstractmethod
    def short_name(cls) -> str:
        raise NotImplementedError

    def modify(self, graph_to_modify):
        """
        Returns the modified, original, graph
        :param graph_to_modify: The graph for modification
        :return: The modified graph
        """
        raise NotImplementedError

from abc import ABC, abstractmethod
from common import config
import data.models as models
from typing import List, Tuple


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

    @abstractmethod
    def compare(self, a: models.CommentCached, _a: models.SplitComment,
                b: models.CommentCached, _b: models.SplitComment,
                sentence_a, sentence_b) -> Tuple[models.EdgeType, float]:
        """
        Returns a similarity score
        :param a: First comment to compare
        :param _a: Split version of first comment
        :param b: Second comment to compare
        :param _b: Split version of second comment
        :param sentence_a: index of sentence within comment a
        :param sentence_b: index of sentence within comment b
        :return: edge type and weight
        """
        raise NotImplementedError

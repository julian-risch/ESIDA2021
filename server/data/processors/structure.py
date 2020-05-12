import logging
from datetime import datetime
import data.models as models
from data.processors import Comparator

logger = logging.getLogger('data.graph.structure')


class SameCommentComparator(Comparator):
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

    def _set_weight(self, edge: models.EdgeWeights, weight: float):
        edge.SAME_COMMENT = weight

    def compare(self, a: models.CommentCached, _a: models.SplitComment,
                b: models.CommentCached, _b: models.SplitComment,
                split_a, split_b) -> float:
        if a.id == b.id and ((self.only_consecutive and ((split_a + 1) == split_b)) or not self.only_consecutive):
            return self.base_weight


class SameArticleComparator(Comparator):
    def __init__(self, *args, base_weight=None, only_root: bool = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_weight = self.conf_getfloat('base_weight', base_weight)
        self.only_root = self.conf_getboolean('only_root', only_root)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'base_weight: {self.base_weight} and only_root: {self.only_root}')

    def _set_weight(self, edge: models.EdgeWeights, weight: float):
        edge.SAME_ARTICLE = weight

    def compare(self, a: models.CommentCached, _a: models.SplitComment,
                b: models.CommentCached, _b: models.SplitComment,
                split_a, split_b) -> float:
        if a.article_id == b.article_id and ((self.only_root and split_a == 0 and split_b == 0) or not self.only_root):
            return self.base_weight


class ReplyToComparator(Comparator):
    def __init__(self, *args, base_weight=None, only_root: bool = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_weight = self.conf_getfloat('base_weight', base_weight)
        self.only_root = self.conf_getboolean('only_root', only_root)

        logger.debug(f'{self.__class__.__name__} initialised with '
                     f'base_weight: {self.base_weight} and only_root: {self.only_root}')

    def _set_weight(self, edge: models.EdgeWeights, weight: float):
        edge.REPLY_TO = weight

    def compare(self, a: models.CommentCached, _a: models.SplitComment,
                b: models.CommentCached, _b: models.SplitComment,
                split_a, split_b) -> float:
        if ((a.reply_to_id is not None and a.reply_to_id == b.id) or
            (b.reply_to_id is not None and b.reply_to_id == a.id)) and \
                ((self.only_root and split_a == 0 and split_b == 0) or not self.only_root):
            return self.base_weight


class TemporalComparator(Comparator):
    def __init__(self, *args, max_time=1000, base_weight=None, only_root: bool = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_time = self.conf_getint('max_time', max_time)
        self.base_weight = self.conf_getfloat('base_weight', base_weight)
        self.only_root = self.conf_getboolean('only_root', only_root)

        logger.debug(f'{self.__class__.__name__} initialised with max_time: {self.max_time} '
                     f'base_weight: {self.base_weight} and only_root: {self.only_root}')

    def _set_weight(self, edge: models.EdgeWeights, weight: float):
        edge.TEMPORAL = weight

    def compare(self, a: models.CommentCached, _a: models.SplitComment,
                b: models.CommentCached, _b: models.SplitComment,
                split_a, split_b) -> float:
        def time_second_difference(x, y):
            if x > y:
                return (x - y).total_seconds()
            return int((y - x).total_seconds())

        def timestring_to_stamp(timestring):
            return datetime.strptime(timestring, "%Y-%m-%d %H:%M:%S")

        weight = time_second_difference(timestring_to_stamp(a.timestamp), timestring_to_stamp(b.timestamp))

        if weight < self.max_time:
            return (weight / self.max_time) * self.base_weight

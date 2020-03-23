from data.processors import Comparator
import data.models as models
from typing import List, Tuple


class SameCommentComparator(Comparator):
    def __init__(self, *args, base_weight=None, only_consecutive=True, **kwargs):
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

    @classmethod
    def short_name(cls) -> str:
        return 'sc'

    @classmethod
    def edge_type(cls) -> models.EdgeType:
        return models.EdgeType.SAME_COMMENT

    def _compare(self, a: models.CommentCached, _a: models.SplitComment, b: models.CommentCached,
                 _b: models.SplitComment, split_a, split_b) -> float:
        if a.id == b.id and ((self.only_consecutive and ((split_a + 1) == split_b)) or not self.only_consecutive):
            return self.base_weight


class SameArticleComparator(Comparator):
    def __init__(self, *args, base_weight=None, only_root=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_weight = self.conf_getfloat('base_weight', base_weight)
        self.only_root = self.conf_getboolean('only_root', only_root)

    @classmethod
    def short_name(cls) -> str:
        return 'sa'

    @classmethod
    def edge_type(cls) -> models.EdgeType:
        return models.EdgeType.SAME_ARTICLE

    def _compare(self, a: models.CommentCached, _a: models.SplitComment, b: models.CommentCached,
                 _b: models.SplitComment, split_a, split_b) -> float:
        if a.article_id == b.article_id and ((self.only_root and split_a == 0 and split_b == 0) or not self.only_root):
            return self.base_weight


class ReplyToComparator(Comparator):
    def __init__(self, *args, base_weight=None, only_root=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_weight = self.conf_getfloat('base_weight', base_weight)
        self.only_root = self.conf_getboolean('only_root', only_root)

    @classmethod
    def short_name(cls) -> str:
        return 'rep'

    @classmethod
    def edge_type(cls) -> models.EdgeType:
        return models.EdgeType.REPLY_TO

    def _compare(self, a: models.CommentCached, _a: models.SplitComment, b: models.CommentCached,
                 _b: models.SplitComment, split_a, split_b) -> float:
        if ((a.reply_to_id is not None and a.reply_to_id == b.comment_id) or
            (b.reply_to_id is not None and b.reply_to_id == a.comment_id)) and \
                ((self.only_root and split_a == 0 and split_b == 0) or not self.only_root):
            return self.base_weight

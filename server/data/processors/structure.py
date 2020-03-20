from data.processors import Comparator
import data.models as models
from typing import List, Tuple


class SameCommentComparator(Comparator):
    def __init__(self, *args, base_weight=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_weight = self.conf_getfloat('base_weight', base_weight)

    @classmethod
    def short_name(cls) -> str:
        return 'sc'

    def compare(self, a: models.CommentCached, _a: models.SplitComment, b: models.CommentCached,
                _b: models.SplitComment, sentence_a, sentence_b) -> Tuple[models.EdgeType, float]:
        if a.id == b.id:
            return models.EdgeType.SAME_COMMENT, self.base_weight


class SameArticleComparator(Comparator):
    def __init__(self, *args, base_weight=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_weight = self.conf_getfloat('base_weight', base_weight)

    @classmethod
    def short_name(cls) -> str:
        return 'sa'

    def compare(self, a: models.CommentCached, _a: models.SplitComment, b: models.CommentCached,
                _b: models.SplitComment, sentence_a, sentence_b) -> Tuple[models.EdgeType, float]:
        if a.article_id == b.article_id:
            return models.EdgeType.SAME_ARTICLE, self.base_weight


class ReplyToComparator(Comparator):
    def __init__(self, *args, base_weight=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_weight = self.conf_getfloat('base_weight', base_weight)

    @classmethod
    def short_name(cls) -> str:
        return 'rep'

    def compare(self, a: models.CommentCached, _a: models.SplitComment, b: models.CommentCached,
                _b: models.SplitComment, sentence_a, sentence_b) -> Tuple[models.EdgeType, float]:
        if (a.reply_to_id is not None and a.reply_to_id == b.comment_id) or \
                (b.reply_to_id is not None and b.reply_to_id == a.comment_id):
            return models.EdgeType.REPLY_TO, self.base_weight

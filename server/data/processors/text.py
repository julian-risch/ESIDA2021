import re
import data.models as models
from typing import List
from common import config


MIN_SPLIT_LENGTH = config.getint('TextProcessing', 'min_split_len')


def split_sentences(s):
    # https://stackoverflow.com/questions/25735644/python-regex-for-splitting-text-into-sentences-sentence-tokenizing
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', s)


def split_comment(comment: models.CommentCached) -> models.SplitComment:
    text_sentences = split_sentences(comment.text)
    splits = []
    bound = 0
    for text_sentence in text_sentences:
        # skip things that are too short.
        if len(text_sentence) < 10:
            continue
        splits.append(models.Split(s=bound, e=bound + len(text_sentence)))
        bound += len(text_sentence) + 1

    return models.SplitComment(
        id=comment.id,
        splits=splits
    )


def get_split_text(comment: models.CommentCached, split: models.Split):
    return comment[split.s:split.e]


def get_split_texts(comment: models.CommentCached, splits: List[models.Split]):
    return [get_split_text(comment, split) for split in splits]

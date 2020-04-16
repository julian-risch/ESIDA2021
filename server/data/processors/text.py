import re
import data.models as models
from typing import List
from common import config
# import spacy

MIN_SPLIT_LENGTH = config.getint('TextProcessing', 'min_split_len')


# def preprocess(texts, lemmatize: bool = True, lower: bool = True,
#                pos_filter: list = None, remove_stopwords: bool = False,
#                remove_punctuation: bool = False, lan_model: None):
#     def token_representation(token):
#         representation = str(token.lemma_) if lemmatize else str(token)
#         if lower:
#             representation = representation.lower()
#         return representation
#
#     nlp = spacy.load("de_core_news_sm") if lan_model is None else lan_model
#
#     preprocessed_texts = []
#
#     if pos_filter is None:
#         for doc in nlp.pipe(texts, disable=['parser', 'ner', 'tagger']):
#             preprocessed_texts.append(
#                 [token_representation(token)
#                  for token in doc
#                  if (not remove_stopwords or not token.is_stop)
#                  and (not remove_punctuation or token.is_alpha)]
#             )
#
#     else:
#         for doc in nlp.pipe(texts, disable=['parser', 'ner']):
#             preprocessed_texts.append(
#                 [token_representation(token)
#                  for token in doc if (not remove_stopwords or not token.is_stop)
#                  and (not remove_punctuation or token.is_alpha)
#                  and token.pos_ in pos_filter]
#             )
#     return preprocessed_texts


def split_sentences(s):
    # https://stackoverflow.com/questions/25735644/python-regex-for-splitting-text-into-sentences-sentence-tokenizing
    # FIXME this isn't ideal, newline is ignored
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', s, flags=re.MULTILINE)


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

    # FIXME: if needed there must be a way to change comment texts
    #        and replace tokens e.g. with lemmas, lowercase etc and filter POS, punctuation
    # preprocessed_splitted_sentences = preprocess(splits,
    #                                              lemmatize=True,
    #                                              lower=True,
    #                                              pos_filter= None,
    #                                              remove_stopwords=False,
    #                                              remove_punctuation=False,
    #                                              lan="DE")

    return models.SplitComment(
        id=comment.id,
        splits=splits
    )


def get_split_text(comment: models.CommentCached, split: models.Split):
    return comment[split.s:split.e]


def get_split_texts(comment: models.CommentCached, splits: List[models.Split]):
    return [get_split_text(comment, split) for split in splits]

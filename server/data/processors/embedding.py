import numpy as np
import fasttext as ft
from typing import List, Dict
from data.processors import Comparator, Modifier, GraphRepresentationType
import data.models as models
import logging
from common import config

FASTTEXT_PATH = config.get('TextProcessing', 'fasttext_path')
logger = logging.getLogger('data.graph.embedding')


def load_fasttext_model():
    return ft.load_model(FASTTEXT_PATH)


def vectorize_sentence(model, sentence: str) -> List[float]:
    return model.get_sentence_vector(sentence.replace("\n", " "))


def vectorize_comments(model, comment_texts: List[str]) -> Dict[int, List[float]]:
    if not model:
        model = load_fasttext_model()
    vectorized_documents = {i: vectorize_sentence(model, comment_text.replace("\n", " "))
                            for i, comment_text in enumerate(comment_texts)}

    vectorized_documents = {k: np.array(v) for k, v in vectorized_documents.items()}

    return vectorized_documents


def cosine_similarity(model, text_a: str, text_b: str):
    if text_a is None or text_b is None:
        return 0
    if text_a is text_b:
        return 1

    a = vectorize_sentence(model, text_a)
    b = vectorize_sentence(model, text_b)

    self_norm = np.linalg.norm(a)
    other_norm = np.linalg.norm(b)
    if self_norm == 0 and other_norm == 0:
        return 1
    if self_norm == 0 or other_norm == 0:
        return 0
    return np.dot(a, b) / (self_norm * other_norm)


class SimilarityComparator(Comparator):
    def __init__(self, *args, max_similarity: float = None, base_weight=None, only_root: bool = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_similarity = self.conf_getfloat('max_similarity', max_similarity)
        self.base_weight = self.conf_getfloat('base_weight', base_weight)
        self.only_root = self.conf_getboolean('only_root', only_root)

        logger.debug(f'{self.__class__.__name__} initialised with max_similarity: {self.max_similarity} '
                     f'base_weight: {self.base_weight} and only_root: {self.only_root}, load fasttext model...')
        self.model = load_fasttext_model()
        logger.debug(f'loaded fast text model')

    def _set_weight(self, edge: models.EdgeWeights, weight: float):
        edge.SIMILARITY = weight

    def compare(self, a: models.CommentCached, _a: models.SplitComment,
                b: models.CommentCached, _b: models.SplitComment,
                split_a, split_b) -> float:
        weight = cosine_similarity(self.model, a.text, b.text)
        if weight < self.max_similarity:  #
            return ((1.0 - weight) / (1.0 - self.max_similarity)) * self.base_weight

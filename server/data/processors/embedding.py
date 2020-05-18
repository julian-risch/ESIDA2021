import numpy as np
import fasttext as ft
from typing import List, Dict
from data.processors import Comparator, Modifier, GraphRepresentationType
import data.models as models
import logging
from common import config
import re

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


class ToxicityRanker(Modifier):
    def __init__(self, *args, ft_model, window_length=40, **kwargs):
        """
        Returns a graph with toxicity node weights
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)

        logger.debug(f'{self.__class__.__name__} initialised')
        self.ft_model = ft_model
        self.n_features = ft_model.get_dimension()
        self.window_length = self.conf_getint('window_length', window_length)

    def normalize(self, s):
        # transform to lowercase characters
        s = str(s)
        s = s.lower()
        # Isolate punctuation
        s = re.sub(r'([\'\"\.\(\)\!\?\-\\\/\,])', r' \1 ', s)
        # Remove some special characters
        s = re.sub(r'([\;\:\|\n])', ' ', s)
        return s

    def text_to_vector(self, text):
        """
        Given a string, normalizes it, then splits it into words and finally converts
        it to a sequence of word vectors.
        """
        text = self.normalize(text)
        words = text.split()
        window = words[-self.window_length:]
        x = np.zeros((self.window_length, self.n_features))
        for i, word in enumerate(window):
            x[i, :] = self.ft_model.get_word_vector(word).astype('float32')
        return x

    def orig_comment_to_data(self, comments: List[models.CommentCached]):
        """
        Convert a given list of original_comment to a dataset of inputs for the NN.
        """
        x = np.zeros((len(comments), self.window_length, self.n_features), dtype='float32')

        for i, comment in enumerate(comments):
            x[i, :] = self.text_to_vector(comment.text)
        return x

    def graph_comments_to_data(self, graph: GraphRepresentationType):
        """
        Convert a graph with slitted comments to a dataset of inputs for the NN.
        """
        number_of_data_points = 0
        for comment in graph.comments:
            for _ in comment.splits:
                number_of_data_points += 1

        x = np.zeros((number_of_data_points, self.window_length, self.n_features), dtype='float32')

        index = 0
        for comment in graph.comments:
            for split in comment.splits:
                # todo: check if comment id is the correct id, otherwise call graph.id2idx[comment.id]
                text = graph.orig_comments[comment.id][split.s, split.e]
                x[index, :] = self.text_to_vector(text)
                index += 1
        return x

    def modify(self, graph: GraphRepresentationType):
        # alternative for orig_comments
        # x = self.orig_comment_to_data(graph.orig_comments)

        x = self.graph_comments_to_data(graph)

        for comment in graph.comments:
            for split in comment.splits:
                # todo: add toxicity score for split
                split.wgts.TOXICITY = ...

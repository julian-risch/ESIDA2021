import numpy as np
import fasttext as ft
from typing import List, Dict


def load_fasttext_model(path='E:\\cc.de.300.bin'):
    return ft.load_model(path)


def vectorize_sentence(model, sentence: str) -> List[float]:
    return model.get_sentence_vector(sentence.replace("\n", " "))


def vectorize_comments(model, comment_texts: List[str]) -> Dict[int, List[float]]:
    if not model:
        model = load_fasttext_model()
    vectorized_documents = {i: vectorize_sentence(model, comment_text.replace("\n", " "))
                            for i, comment_text in enumerate(comment_texts)}

    vectorized_documents = {k: np.array(v) for k, v in vectorized_documents.items()}

    return vectorized_documents

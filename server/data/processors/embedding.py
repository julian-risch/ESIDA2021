import numpy as np
import fasttext as ft


def load_fasttext_model(path='E:\\cc.de.300.bin'):
    return ft.load_model(path)


def vectorize(model, comment_texts):
    if not model:
        model = load_fasttext_model()
    vectorized_documents = {i: model.get_sentence_vector(comment_text.replace("\n", " "))
                            for i, comment_text in enumerate(comment_texts)}

    vectorized_documents = {k: np.array(v) for k, v in vectorized_documents.items()}

    return vectorized_documents

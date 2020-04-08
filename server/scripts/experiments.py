import data.database as db
import data.models as models
from typing import Union, Optional, Tuple, List
from data.processors.graph import GraphRepresentation


async def get_graph(article_ids: List[int] = None, conf: dict = None) -> models.Graph:
    comments = await db.get_comments(article_ids)
    graph_rep = GraphRepresentation(comments, conf=conf)
    graph = models.Graph(**graph_rep.__dict__())

    return graph


get_graph()
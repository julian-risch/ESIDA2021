import data.database as db
import data.models as models
from typing import Union, Optional, Tuple, List, Any, Coroutine

from data.models import Graph
from data.processors import Modifier
from data.processors.graph import GraphRepresentation
from data.processors.modification import PageRankFilter, PageRanker

MODIFIERS = [PageRanker, PageRankFilter]


async def get_graph(article_ids: List[int] = None, conf: dict = None) -> models.Graph:
    comments = await db.get_comments(article_ids)
    graph_rep = GraphRepresentation(comments, conf=conf)
    graph = models.Graph(**graph_rep.__dict__())

    return graph


# todo: get config, article IDs
conf = None
article_ids = None

graph = get_graph(article_ids, conf)

graph = Modifier.use(modifiers_to_use=MODIFIERS, graph_to_modify=graph, conf=conf)

from sqlalchemy import create_engine, Column, ForeignKey, MetaData, Table
from sqlalchemy.types import DateTime, Boolean, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import databases
from typing import List, Optional, Mapping, Union
import logging
import json

import data.models as models
from common import config

logger = logging.getLogger('data.db')

DATABASE_URL = config.get('cache', 'db_url')

database = databases.Database(DATABASE_URL)
metadata = MetaData()

engine = create_engine(DATABASE_URL,
                       connect_args={
                           # has to be set to False if sqlite is used
                           "check_same_thread": not DATABASE_URL.startswith('sqlite')
                       })

Base = declarative_base(metadata=metadata)


def init_db(app):
    @app.on_event("startup")
    async def startup():
        await database.connect()
        logger.debug('Database connected')

    @app.on_event("shutdown")
    async def shutdown():
        await database.disconnect()
        logger.debug('Database connection closed')


articles_table = Table(
    'articles',
    metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('url', String, index=True, unique=True),
    Column('title', String),
    Column('subtitle', String, nullable=True),
    Column('summary', String, nullable=True),
    Column('author', String, nullable=True),
    Column('text', String, nullable=False),
    Column('published_time', DateTime),
    Column('scrape_time', DateTime),
    Column('scraper', String)
)

comments_table = Table(
    'comments',
    metadata,

    Column('id', Integer, primary_key=True, index=True),
    Column('article_id', Integer, ForeignKey('articles.id'), nullable=False),
    Column('comment_id', String, index=True, nullable=False),
    Column('username', String),
    Column('timestamp', DateTime),
    Column('text', String),
    Column('reply_to', String, ForeignKey('comments.comment_id'), nullable=True),

    # Optional details from FAZ and TAZ
    Column('num_replies', Integer, nullable=True),
    Column('user_id', String, nullable=True),

    # Optional details from SPON
    Column('upvotes', Integer, nullable=True),
    Column('downvotes', Integer, nullable=True),
    Column('love', Integer, nullable=True),

    # Optional details from Welt
    Column('likes', Integer, nullable=True),
    Column('recommended', Integer, nullable=True),
    Column('child_count', Integer, nullable=True),

    # Optional details from ZON
    Column('leseempfehlungen', Integer, nullable=True),

    # Optional details from Tagesschau
    Column('title', String, nullable=True),
)

graphs_table = Table(
    'graphs',
    metadata,
    Column('id', Integer, primary_key=True, index=True),
    # Comma separated list of article_ids (JSON array)
    Column('article_ids', String, index=True),
    # JSON dump of models.Graph
    Column('graph', String)
)

Base.metadata.create_all(bind=engine)


async def insert_article(article: models.ArticleScraped):
    last_record_id = await database.execute(articles_table.insert().values(**article.dict()))
    logger.debug(f'INSERTed article to DB with ID: {last_record_id}!')
    return last_record_id


async def insert_comment(comment: models.CommentScraped, article_id: int) -> int:
    last_record_id = await database.execute(
        comments_table.insert().values(article_id=article_id, **comment.dict()))
    return last_record_id


async def insert_comments(comments: List[models.CommentScraped], article_id: int):
    values = [{**comment.dict(), 'article_id': article_id} for comment in comments]
    await database.execute_many(comments_table.insert(), values=values)
    logger.debug(f'INSERTed {len(comments)} comments into DB!')


async def get_article_id(url: str) -> int:
    logger.debug(f'Get article id for url: {url}')
    query = 'SELECT id FROM articles WHERE url = :url'
    article_id = await database.fetch_one(query, {'url': url})
    return article_id['id']


async def delete_article(url: str = None, article_id: int = None, recursive=False):
    logger.debug(f'DELETE article from DB: id: {article_id}, url: {url}')
    assert url or article_id
    if url is not None:
        article_id = await get_article_id(url)

    # apparently no article for this URL in the DB
    if not article_id:
        return

    if recursive:
        await delete_comments(article_id=article_id)
        await delete_edges(article_id=article_id)

    await database.execute('DELETE FROM articles '
                           'WHERE id = :article_id;',
                           {'article_id': article_id})


async def delete_comments(url: str = None, article_id: int = None):
    logger.debug(f'DELETE all comments related to article id: {article_id}, url: {url}')
    assert url or article_id
    if url:
        article_id = get_article_id(url)

    await database.execute('DELETE FROM comments '
                           'WHERE article_id = :article_id',
                           {'article_id': article_id})


async def delete_edges(graph_id: int = None, article_id: int = None):
    logger.debug(f'DELETE all graphs for graph.id: {graph_id}, article_id: {article_id}')
    assert graph_id or article_id

    if graph_id:
        await database.execute('DELETE FROM graphs '
                               'WHERE id = :graph_id',
                               {'graph_id': graph_id})
    else:
        await database.execute('DELETE FROM graphs '
                               'WHERE id in ('
                               '    SELECT graphs.id '
                               '    FROM graphs, json_each(graphs.article_ids) as article_ids'
                               '    WHERE article_ids.value = :article_id)',
                               {'article_id': article_id})


async def get_article(url: str = None, article_id: int = None) -> Mapping:
    logger.debug(f'Get article from DB: id: {article_id}, url: {url}')
    assert url or article_id
    if url is not None:
        query = 'SELECT * FROM articles WHERE url = :url'
        return await database.fetch_one(query, {'url': url})

    query = 'SELECT * FROM articles WHERE id = :article_id'
    return await database.fetch_one(query, {'article_id': article_id})


async def get_comments(article_ids: Union[List[int], int]) -> List[models.CommentCached]:
    # can be called for a single article_id, so wrap it.
    if isinstance(article_ids, int):
        article_ids = [article_ids]

    # make it save to inject into sql query
    article_ids = ','.join([str(i) for i in article_ids if isinstance(i, int)])

    comments = await database.fetch_all('SELECT c1.*, c2.id as reply_to_id '
                                        'FROM comments c1 '
                                        'LEFT JOIN comments c2 ON c1.reply_to = c2.comment_id '
                                        f'WHERE c1.article_id IN ({article_ids});')
    logger.debug(f'Found {len(comments)} comments for article_ids: {article_ids}')
    return [models.CommentCached(**comment) for comment in comments]


async def get_article_with_comments(url: str = None, article_id: int = None) -> models.ArticleCached:
    article = await get_article(url, article_id)
    assert bool(article)
    article = models.ArticleCached(**article)

    comments = await get_comments(article.id)
    article.comments = comments

    return article


async def get_graph(article_ids: List[int]) -> models.Graph:
    # make it save to inject into sql query
    article_ids = [i for i in sorted(article_ids) if isinstance(i, int)]

    result = await database.fetch_one('SELECT * FROM graphs WHERE article_ids = :article_ids',
                                      {'article_ids': json.dumps(article_ids)})
    if result:
        graph = json.loads(result['graph'])
        logger.debug(f'Retrieved graph id: {result["id"]} for {article_ids}')
        return models.Graph(article_ids=json.loads(result['article_ids']),
                            graph_id=result['id'],
                            comments=graph['comments'],
                            id2idx=graph['id2idx'],
                            edges=graph['edges'])


async def store_graph(article_ids: List[int], graph: models.Graph):
    # make it save to inject into sql query
    article_ids = json.dumps([i for i in sorted(article_ids) if isinstance(i, int)])
    graph = graph.json(exclude={'articles_id', 'graph_id'})

    last_record_id = await database.execute(graphs_table.insert().values({
        'graph': graph,
        'article_ids': article_ids
    }))
    logger.debug(f'INSERTed graph for {article_ids} to DB with ID: {last_record_id}!')
    return last_record_id

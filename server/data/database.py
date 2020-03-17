from sqlalchemy import create_engine, Column, ForeignKey, MetaData, Table
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.types import DateTime, Boolean, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import databases
from typing import List, Optional, Mapping
import logging

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
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base(metadata=metadata)


# def get_db():
#     db: SessionLocal = None
#     try:
#         db = SessionLocal()
#         yield db
#     finally:
#         db.close()


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
    # comments = relationship('Comment', back_populates='article')
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

    # article = relationship('Article', back_populates='comments')
)

# class Article(Base):
#     __tablename__ = 'articles'
#
#     id = Column(Integer, primary_key=True, index=True)
#     url = Column(String, index=True, unique=True)
#     title = Column(String)
#     subtitle = Column(String, nullable=True)
#     summary = Column(String, nullable=True)
#     author = Column(String, nullable=True)
#     text = Column(String, nullable=False)
#     published_time = Column(DateTime)
#     scrape_time = Column(DateTime)
#     scraper = Column(String)
#
#     comments = relationship('Comment', back_populates='article')
#
#
# class Comment(Base):
#     __tablename__ = 'comments'
#
#     id = Column(Integer, primary_key=True, index=True)
#     article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
#     comment_id = Column(String, index=True, nullable=False)
#     username = Column(String)
#     timestamp = Column(DateTime)
#     text = Column(String)
#     reply_to = Column(String, ForeignKey('comments.comment_id'), nullable=True)
#
#     # Optional details from FAZ and TAZ
#     num_replies = Column(Integer, nullable=True)
#     user_id = Column(String, nullable=True)
#
#     # Optional details from SPON
#     upvotes = Column(Integer, nullable=True)
#     downvotes = Column(Integer, nullable=True)
#     love = Column(Integer, nullable=True)
#
#     # Optional details from Welt
#     likes = Column(Integer, nullable=True)
#     recommended = Column(Integer, nullable=True)
#     child_count = Column(Integer, nullable=True)
#
#     # Optional details from ZON
#     leseempfehlungen = Column(Integer, nullable=True)
#
#     # Optional details from Tagesschau
#     title = Column(String, nullable=True)
#
#     article = relationship('Article', back_populates='comments')


Base.metadata.create_all(bind=engine)


async def insert_article(article: models.ArticleScraped):
    last_record_id = await database.execute(articles_table.insert().values(**article.dict()))
    return last_record_id


async def insert_comment(comment: models.CommentScraped, article_id: int) -> int:
    last_record_id = await database.execute(
        comments_table.insert().values(article_id=article_id, **comment.dict()))
    return last_record_id


async def insert_comments(comments: List[models.CommentScraped], article_id: int):
    values = [{**comment.dict(), 'article_id': article_id} for comment in comments]
    await database.execute_many(comments_table.insert(), values=values)


async def get_article(url: str = None, article_id: int = None) -> Mapping:
    assert url or article_id
    if url is not None:
        query = 'SELECT * FROM articles WHERE url = :url'
        return await database.fetch_one(query, {'url': url})

    query = 'SELECT * FROM articles WHERE id = :article_id'
    return await database.fetch_one(query, {'article_id': article_id})


async def get_article_with_comments(url: str = None, article_id: int = None) -> models.ArticleCached:
    article = await get_article(url, article_id)
    assert bool(article)
    article = models.ArticleCached(**article)

    query = 'SELECT * FROM comments WHERE article_id = :article_id'
    comments = await database.fetch_all(query, {'article_id': article.id})
    comments = [models.CommentCached(**comment) for comment in comments]

    article.comments = comments

    return article

# async def insert_article(article: models.ArticleCreate):
#    db_article = Article(**article.dict())
#    database.add(db_article)


# __all__ = ['Comment', 'Article', 'init_db']

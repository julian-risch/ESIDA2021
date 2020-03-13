from pydantic import BaseModel, validator, ValidationError, AnyHttpUrl
from datetime import datetime
from typing import List, Optional
from enum import Enum
import re


class Comment(BaseModel):
    user: str
    id: str
    timestamp: datetime
    text: str
    reply_to: Optional[str] = None

    # Optional details from FAZ and TAZ
    number_of_replies: Optional[int] = None
    user_id: Optional[str] = None

    # Optional details from SPON
    upvotes: Optional[int] = None
    downvotes: Optional[int] = None
    love: Optional[int] = None

    # Optional details from Welt
    likes: Optional[int] = None
    recommended: Optional[int] = None
    child_count: Optional[int] = None

    # Optional details from ZON
    leseempfehlungen: Optional[int] = None

    # @validator('timestamp')
    # def dt2str(self, v):
    #    if type(v) == str and re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", v):
    #        return v
    #    if type(v) == datetime:
    #        return v.strftime('%Y-%m-%d %H:%M:%S')
    #    raise ValueError('must be string of the form of timestamp or datetime object')


class Article(BaseModel):
    url: AnyHttpUrl
    title: str
    summary: str = None
    author: str = None
    text: str
    published_time: datetime
    scrape_time: datetime
    scraper: str
    comments: List[Comment] = []


class ScrapeResultStatus(str, Enum):
    NO_COMMENTS = 'NO_COMMENTS'
    OK = 'OK'
    ERROR = 'ERROR'


class ScrapeResult(BaseModel):
    payload: Article = None,
    detail: ScrapeResultStatus = ScrapeResultStatus.OK

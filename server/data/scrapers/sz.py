from data.scrapers import Scraper, NoCommentsWarning, UnknownStructureWarning
import re
from datetime import datetime
from common import config
import logging
import data.models as models
import json

logger = logging.getLogger('scraper')


class SueddeutscheScraper(Scraper):
    API_KEY = config.get('scrapers', 'sz_api_key')

    @staticmethod
    def assert_url(url):
        return re.match(r'(https?://)?(www\.)?sueddeutsche\.de/.*', url)

    @classmethod
    def _scrape(cls, url):
        bs = cls.get_html(url)
        article = cls._scrape_article(bs, url)
        comments = cls._scrape_comments(bs, url)

        return article, comments

    @classmethod
    def _author(cls, bs):
        author = bs.select('a.sz-article-byline__author-link')
        if author:
            return author[0].get_text()
        logger.debug('no author found!')
        return None

    @classmethod
    def _title(cls, bs):
        try:
            return ' '.join([e.get_text() for e in bs.select('header.sz-article__header h2 span')])
        except AttributeError:
            pass
        try:
            return bs.select_one('article > header > h2').get_text()
        except AttributeError:
            raise UnknownStructureWarning(f'Article Layout not known; couldn\'t find title!')

    @classmethod
    def _summary(cls, bs):
        try:
            sel = bs.select('div.sz-article-intro p')
            if not sel:
                sel = bs.select('div.sz-article__intro p')
            if sel:
                return '\n\n'.join([e.get_text().strip() for e in sel])
        except Exception:
            pass

    @classmethod
    def _published_time(cls, bs):
        try:
            return datetime.strptime(bs.select('time.sz-article-header__time')[0]['datetime'],
                                     '%Y-%m-%d %H:%M:%S')
        except IndexError:
            pass
        try:
            return datetime.strptime(bs.select('.sz-article__header time')[0]['datetime'],
                                     '%Y-%m-%d %H:%M:%S')
        except IndexError:
            pass
        raise UnknownStructureWarning(f'Article Layout not known; couldn\'t find published_time!')

    @classmethod
    def _scrape_article(cls, bs, url):
        try:
            data = models.ArticleScraped(
                url=url,
                author=cls._author(bs),
                title=cls._title(bs),
                summary=cls._summary(bs),
                text=re.sub(r'\s+', ' ', ' '.join([
                    par.get_text() for par in bs.select('div.sz-article__body.sz-article-body p')])),
                published_time=cls._published_time(bs),
                scraper=str(cls))
        except IndexError as e:
            raise UnknownStructureWarning(f'Article Layout not known; caused by error: "{e}"')

        return data

    @classmethod
    def _scrape_comments(cls, bs, url):
        discussion_url = [e['href'] for e in bs.select('div.sz-article-body__asset a.sz-teaser--article')
                          if 'leserdiskussion' in e['href']]
        if len(discussion_url) > 0:
            return cls._scrape_comments_disqus(discussion_url[0])

        conf = json.loads(bs.select_one('#szde-article-config').get_text())
        print(conf)

    @classmethod
    def _scrape_comments_disqus(cls, url):
        comments = []

        parameters = {
            'api_key': cls.API_KEY,
            'forum': 'szde',
            'limit': 100,
            'thread': f'link:{url}',
            # 'cursor': f'next:{}'
        }

        # gather comments and meta data about comments in a list
        responses = []

        # raw return includes metadata about the page of comments (e.g.if any more pages)
        raw_return = cls.get_json('https://disqus.com/api/3.0/posts/list.json', params=parameters)
        responses.extend(raw_return['response'])

        # pagination: keep adding comments from next pages.
        counter = 0
        max_counter = 100

        # scrape all next pages, but do not go into infinite loop
        while raw_return['cursor']['hasNext'] and counter < max_counter:
            parameters['cursor'] = raw_return['cursor']['next']
            raw_return = cls.get_json('https://disqus.com/api/3.0/posts/list.json', params=parameters)
            responses.extend(raw_return['response'])

        for comment_data in responses:
            comment = models.CommentScraped(
                comment_id=comment_data['id'],
                username=comment_data['author']['username'],
                timestamp=datetime.strptime(comment_data['createdAt'], '%Y-%m-%dT%H:%M:%S'),
                text=comment_data['raw_message'],
                reply_to=comment_data['parent'])
            comments.append(comment)
        return comments


if __name__ == '__main__':
    SueddeutscheScraper.test_scraper([
        'https://www.sueddeutsche.de/politik/brexit-johnson-unterhaus-neuwahlen-1.4647880',
        'https://www.sueddeutsche.de/politik/groko-csu-spd-einigung-grundrente-1.4676599'
    ])

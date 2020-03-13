from data.platforms import Scraper
import re
import requests
from datetime import datetime
from common import config


class SueddeutscheScraper(Scraper):
    API_KEY = config.get('scrapers', 'sz_api_key')

    @staticmethod
    def assert_url(url):
        return re.match(r'(https?://)?(www\.)?sueddeutsche\.de/.*', url)

    @classmethod
    def _scrape(cls, url):
        bs = cls.get_html(url)
        article = cls._scrape_article(bs, url)

        discussion_url = [e['href'] for e in bs.select('div.sz-article-body__asset a.sz-teaser--article')
                          if 'leserdiskussion' in e['href']]
        if len(discussion_url) > 0:
            article['comments'] = cls._scrape_comments_disqus(discussion_url[0])
        else:
            raise UserWarning('No Comments found!')
        return article

    @classmethod
    def _scrape_author(cls, bs):
        author = bs.select('a.sz-article-byline__author-link')
        if author:
            return author[0].get_text()
        cls.info('WARN: no author found!')
        return None

    @classmethod
    def _scrape_article(cls, bs, url):

        try:
            data = cls.make_article(
                url=url,
                author=cls._scrape_author(bs),
                title=bs.select('h2 span.sz-article-header__title')[0].get_text(),
                summary='\n\n'.join([e.get_text().strip() for e in bs.select('div.sz-article-intro p')]),
                text=re.sub(r'\s+', ' ', ' '.join([
                    par.get_text() for par in bs.select('div.sz-article__body.sz-article-body p')])),
                published=datetime.strptime(bs.select('time.sz-article-header__time')[0]['datetime'], '%Y-%m-%d %H:%M:%S'))
        except IndexError:
            raise UserWarning("Article Layout not known!")

        return data

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
        raw_return = requests.get('https://disqus.com/api/3.0/posts/list.json', params=parameters).json()
        responses.extend(raw_return['response'])

        # pagination: keep adding comments from next pages.
        counter = 0
        max_counter = 100

        # scrape all next pages, but do not go into infinite loop
        while raw_return['cursor']['hasNext'] and counter < max_counter:
            parameters['cursor'] = raw_return['cursor']['next']
            raw_return = requests.get('https://disqus.com/api/3.0/posts/list.json', params=parameters).json()
            responses.extend(raw_return['response'])

        for comment_data in responses:
            comment = cls.make_comment(cid=comment_data['id'],
                                       user=comment_data['author']['username'],
                                       published=datetime.strptime(comment_data['createdAt'], '%Y-%m-%dT%H:%M:%S'),
                                       text=comment_data['raw_message'],
                                       reply_to=comment_data['parent'])
            comments.append(comment)
        return comments


# toDO: fix mistakes, after fixing add urls to stories
if __name__ == '__main__':
    Scraper.LOG_REQUESTS = True
    Scraper.LOG_INFO = True
    SueddeutscheScraper.test_scraper([
        'https://www.sueddeutsche.de/politik/brexit-johnson-unterhaus-neuwahlen-1.4647880',
        'https://www.sueddeutsche.de/politik/groko-csu-spd-einigung-grundrente-1.4676599'
        # has comments, but stated it has no comments
    ])

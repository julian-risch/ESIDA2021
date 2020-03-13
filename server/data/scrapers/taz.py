import re
from data.scrapers import Scraper
from datetime import datetime
import logging
import data.models as models

logger = logging.getLogger('scraper')


class TAZScraper(Scraper):
    @staticmethod
    def assert_url(url):
        return re.match(r'(https?://)?(www\.)?taz\.de/.*', url)

    @classmethod
    def _scrape(cls, url):
        bs = cls.get_html(url)
        article_data = cls._scrape_article(bs, url)
        article_data['comments'] = cls._scrape_comments(bs)

        return article_data

    @classmethod
    def _scrape_author(cls, bs):
        author = bs.select('div[itemprop="author"] h4[itemprop="name"]')
        if author:
            return author[0].get_text().strip()
        logger.debug('WARN: no author found!')
        return None

    @classmethod
    def _scrape_article(cls, bs, url):

        article = cls.make_article(
            url=url,
            title=bs.select('article h1[itemprop="headline"]')[0].get_text().strip(),
            summary=bs.select('article p[itemprop="description"]')[0].get_text().strip(),
            author=cls._scrape_author(bs),
            text='\n\n'.join([e.get_text().strip() for e in bs.select('article p.article')]),
            published=datetime.strptime(bs.select('li[itemprop="datePublished"]')[0]['content'], '%Y-%m-%dT%H:%M:%S%z')
        )

        return article

    @classmethod
    def _scrape_comments(cls, bs):
        comments = []
        stack = [(None, c) for c in bs.select('div.sect_commentlinks > ul > li')]

        while len(stack) > 0:
            parent_id, c = stack.pop()
            comment = cls._parse_comment(c, parent_id)

            for sub in c.select(':scope > ul.thread > li'):
                stack.append((comment['id'], sub))

            comments.append(comment)

        return comments

    @classmethod
    def _parse_comment(cls, e, parent_id):

        user_id = None
        try:
            user_id = e.select('a.author')[0]['href']
        except:
            raise KeyError

        parsed_comment = cls.make_comment(
            cid=e['id'],
            user=e.select('a.author h4')[0].get_text().strip(),
            published=datetime.strptime(e.select('time[datetime]')[0]['datetime'], '%Y-%m-%dT%H:%M:%S%z'),
            text=e.select('div')[0].get_text().strip(),
            reply_to=parent_id,
            user_id=user_id
        )
        return parsed_comment


if __name__ == '__main__':
    Scraper.LOG_REQUESTS = True
    Scraper.LOG_INFO = True
    TAZScraper.test_scraper([
        'https://taz.de/Die-Gruenen-und-die-K-Frage/!5642445/',
        'https://taz.de/Von-Israel-besetzte-Gebiete/!5637101/',
        'https://taz.de/Abwahl-von-AfD-Politiker-im-Ausschuss/!5641977/',
        'https://taz.de/Machtambitionen-der-Gruenen/!5638650/',
        'https://taz.de/Gruene-Bundesvorsitzende-bestaetigt/!5642426/'
    ])

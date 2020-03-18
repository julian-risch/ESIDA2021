import * as d3 from './libs/d3.min.js'
import { emitter } from "./libs/tinyemitter.js";

const request = (method, url, payload, rawPayload = false) => {
    return new Promise(function (resolve, reject) {
        let xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function () {
            if (this.readyState === 4) {
                if (this.status === 200) {
                    let r = this.responseText;
                    if (this.getResponseHeader("Content-Type") === 'application/json')
                        r = JSON.parse(r);
                    resolve(r);
                } else {
                    reject('FAIL');
                }
            }
        };
        xhttp.open(method, url, true);
        xhttp.setRequestHeader('Accept', 'application/json');
        xhttp.setRequestHeader('Accept', 'text/plain');
        xhttp.send(rawPayload ? payload : JSON.stringify(payload));
    });
};

const GET = (url) =>
    request('GET', url);

const POST = (url, payload, rawPayload = false) =>
    request('POST', url, payload, rawPayload);

/**
 * This should be a 1:1 copy of the API as specified in the openapi.json
 */
const _api = {
    'GET': {
        '/api/platforms/article': (url, override_cache, ignore_cache) => {
            let query = '/api/platforms/article?';
            query += 'url=' + encodeURIComponent(url);
            if (override_cache)
                query += '&override_cache=true';
            if (ignore_cache)
                query += '&ignore_cache=true';

            return GET(query);
        },
        '/api/platforms/scrape': (url) => {
            let query = '/api/platforms/scrape?';
            query += 'url=' + encodeURIComponent(url);

            return GET(query);
        },
        '/api/ping': () => {
            return GET('/api/ping');
        }
    },
    'POST': {
        '/api/ping/{name}': (name) => {
            let query = `/api/ping/${name}`;
            return POST(query);
        }
    }
};

const SCRAPERS = {
    isValidURL: (url) => !!url.match(/^https?:\/\/(www\.)?(zeit|sz|sueddeutsche|faz|spiegel|tagesschau|welt|taz)\.(de|net)\/.*$/i),
    scraper2source: {
        "<class 'data.scrapers.faz.FAZScraper'>": 'faz',
        "<class 'data.scrapers.spon.SPONScraper'>": 'spiegel',
        "<class 'data.scrapers.sz.SZScraper'>": 'sz',
        "<class 'data.scrapers.tagesschau.TagesschauScraper'>": 'tagesschau',
        "<class 'data.scrapers.taz.TAZScraper'>": 'taz',
        "<class 'data.scrapers.welt.WeltScraper'>": 'welt',
        "<class 'data.scrapers.zon.ZONScraper'>": 'zeit'
    },
    CODES: {
        OK: 'OK',
        ERROR: 'ERROR',
        NO_COMMENTS: 'NO_COMMENTS',
        NO_SCRAPER: 'NO_SCRAPER',
        SCRAPER_ERROR: 'SCRAPER_ERROR'
    }
};


class Api {
    constructor() {
        this._initListeners();
    }

    _initListeners() {
        emitter.on('newSourceURL', this.getArticle.bind(this));
    }

    getArticle(url) {
        _api.GET["/api/platforms/article"](url).then((d) => {
            if (d.detail.status === SCRAPERS.CODES.OK) {
                d.payload.source = SCRAPERS.scraper2source[d.payload.scraper];
                d.payload.dateObj = new Date(d.payload.published_time);
                emitter.emit('receivedArticle', d);
            } else {
                console.log(d);
            }
        }).catch((e) => {
            console.log(e);
        });
    }
}


const API = new Api();

export { API, SCRAPERS }
import { E, emitter } from "./events.js";
import * as JsSearch from "../libs/js-search.js"

const EDGE_TYPES = Object.freeze({
    REPLY_TO: 0,
    SAME_ARTICLE: 1,
    SIMILARITY: 2,
    SAME_GROUP: 3,
    SAME_COMMENT: 4
});
const EDGE_TYPES_REV = Object.freeze(Object.fromEntries(
    Object.entries(EDGE_TYPES).map(([k, v]) => [v, k])));

const GRAPH_CONFIG = {
    SameCommentComparator: {
        active: true,
        base_weight: 1.0,
        only_consecutive: true
    },
    SameArticleComparator: {
        active: true,
        base_weight: 1.0,
        only_root: true
    },
    ReplyToComparator: {
        active: true,
        base_weight: 1.0,
        only_root: true
    },
    SimilarityComparator: {
        active: false,
        base_weight: 0.1,
        only_root: true,
        max_similarity: 0.75
    },
    TemporalComparator: {
        active: true,
        base_weight: 1.0,
        only_root: true,
        max_time: 1000
    },
    SizeRanker: {
        active: true
    },
    RecencyRanker: {
        active: true,
        use_yongest: false
    },
    VotesRanker: {
        active: true,
        use_upvotes: true,
        use_downvotes: true
    },
    PageRanker: {
        active: true,
        num_iterations: 100,
        d: 0.85,
        edge_type: 'TEMPORAL',
        use_power_mode: true
    },
    ToxicityRanker: {
        active: false,
        window_length: 125,
        whole_comment: true
    },
    CentralityDegreeCalculator: {
        active: true
    },
    GenericEdgeFilter: {
        active: false,
        threshold: 0.13,
        smaller_as: false,
        edge_type: 'REPLY_TO'
    },
    SimilarityEdgeFilter: {
        active: false,
        threshold: 0.3,
        smaller_as: false
    },
    ReplyToEdgeFilter: {
        active: false,
        threshold: 0.5,
        smaller_as: false
    },
    SameCommentEdgeFilter: {
        active: false,
        threshold: 0.5,
        smaller_as: false
    },
    SameArticleEdgeFilter: {
        active: false,
        threshold: 0.5,
        smaller_as: false
    },
    SameGroupEdgeFilter: {
        active: false,
        threshold: 0.5,
        smaller_as: false
    },
    TemporalEdgeFilter: {
        active: false,
        threshold: 0.5,
        smaller_as: false
    },
    OrEdgeFilter: {
        active: false,
        reply_to_threshold: 0.5,
        same_comment_threshold: 0.5,
        same_article_threshold: -0.5,
        similarity_threshold: -0.5,
        same_group_threshold: -0.5,
        temporal_threshold: 0.5
    },
    GenericBottomEdgeFilter: {
        active: false,
        top_edges: 2,
        descending_order: true,
        edge_type: 'REPLY_TO'
    },
    BottomSimilarityEdgeFilter: {
        active: false,
        top_edges: 5,
        descending_order: true
    },
    BottomReplyToEdgeFilter: {
        active: false,
        top_edges: 100,
        descending_order: true
    },
    BottomTemporalEdgeFilter: {
        active: false,
        top_edges: 100,
        descending_order: true
    },
    BottomSameCommentFilter: {
        active: false,
        top_edges: 100,
        descending_order: true
    },
    BottomSameArticleEdgeFilter: {
        active: false,
        top_edges: 100,
        descending_order: true
    },
    BottomSameGroupEdgeFilter: {
        active: false,
        top_edges: 100,
        descending_order: true
    },
    GenericNodeWeightFilter: {
        active: false,
        strict: false,
        threshold: 2,
        smaller_as: false,
        node_weight_type: 'DEGREE_CENTRALITY'
    },
    SizeFilter: {
        active: false,
        strict: false,
        threshold: 1,
        smaller_as: false
    },
    PageRankFilter: {
        active: false,
        strict: false,
        threshold: 1,
        smaller_as: false
    },
    DegreeCentralityFilter: {
        active: false,
        strict: false,
        threshold: 1,
        smaller_as: false
    },
    RecencyFilter: {
        active: false,
        strict: false,
        threshold: 1,
        smaller_as: false
    },
    VotesFilter: {
        active: true,
        strict: false,
        threshold: 2,
        smaller_as: false
    },
    ToxicityFilter: {
        active: false,
        strict: false,
        threshold: 0.5,
        smaller_as: true
    },
    GenericNodeWeightBottomFilter: {
        active: false,
        strict: false,
        top_k: 5,
        descending_order: true,
        node_weight_type: 'DEGREE_CENTRALITY'
    },
    SizeBottomFilter: {
        active: false,
        strict: false,
        top_k: 5,
        descending_order: true
    },
    PageRankBottomFilter: {
        active: true,
        strict: true,
        top_k: 200,
        descending_order: true
    },
    DegreeCentralityBottomFilter: {
        active: false,
        strict: false,
        top_k: 5,
        descending_order: true
    },
    RecencyBottomFilter: {
        active: false,
        strict: false,
        top_k: 5,
        descending_order: true
    },
    VotesBottomFilter: {
        active: false,
        strict: false,
        top_k: 50,
        descending_order: true
    },
    ToxicityBottomFilter: {
        active: false,
        strict: false,
        top_k: 500,
        descending_order: true
    },
    GenericNodeMerger: {
        active: false,
        threshold: 0.5,
        smaller_as: false,
        edge_weight_type: 'SAME_COMMENT'
    },
    SimilarityNodeMerger: {
        active: false,
        threshold: 0.11,
        smaller_as: false
    },
    ReplyToNodeMerger: {
        active: true,
        threshold: 0.5,
        smaller_as: false
    },
    SameCommentNodeMerger: {
        active: false,
        threshold: 0.5,
        smaller_as: false
    },
    SameArticleNodeMerger: {
        active: false,
        threshold: 0.5,
        smaller_as: false
    },
    SameGroupNodeMerger: {
        active: false,
        threshold: 0.5,
        smaller_as: false
    },
    TemporalNodeMerger: {
        active: false,
        threshold: 0.12,
        smaller_as: false
    },
    MultiNodeMerger: {
        active: false,
        reply_to_threshold: 0.5,
        same_comment_threshold: 0.5,
        same_article_threshold: -0.5,
        similarity_threshold: -0.5,
        same_group_threshold: -0.5,
        temporal_threshold: -0.5,
        smaller_as: false,
        conj_or: true
    },
    GenericClusterer: {
        active: false,
        edge_weight_type: 'SAME_COMMENT',
        algorithm: 'GirvanNewman'
    },
    SimilarityClusterer: {
        active: false,
        algorithm: 'GirvanNewman'
    },
    ReplyToClusterer: {
        active: false,
        algorithm: 'GirvanNewman'
    },
    SameCommentClusterer: {
        active: false,
        algorithm: 'GirvanNewman'
    },
    SameArticleClusterer: {
        active: false,
        algorithm: 'GirvanNewman'
    },
    SameGroupClusterer: {
        active: false,
        algorithm: 'GirvanNewman'
    },
    TemporalClusterer: {
        active: false,
        algorithm: 'GirvanNewman'
    },
    MultiEdgeTypeClusterer: {
        active: false,
        use_reply_to: true,
        use_same_comment: true,
        use_same_article: false,
        use_similarity: false,
        use_same_group: false,
        use_temporal: false,
        algorithm: 'GirvanNewman'
    },
    GenericSingleEdgeAdder: {
        active: true,
        base_weight: 0.1,
        edge_weight_type: 'TEMPORAL',
        node_weight_type: 'RECENCY'
    }
};

const API_SETTINGS = {
    GRAPH_IGNORE_CACHE: false
};

function difference(setA, setB) {
    let _difference = new Set(setA);
    for (let elem of setB) {
        _difference.delete(elem)
    }
    return _difference
}

class Article {
    constructor(url, title, subtitle, summary, author, text,
                publishedTime, scrapeTime, scraper, articleId, numComments) {
        this.url = url;
        this.title = title;
        this.subtitle = subtitle;
        this.summary = summary;
        this.author = author;
        this.text = text;
        this.publishedTime = publishedTime;
        this.scrapeTime = scrapeTime;
        this.source = scraper;
        this.articleId = articleId;
        this.numComments = numComments;
    }
}

class DataStore {
    comments = {};
    sources = {};
    id2idx = {};
    edges = [];
    groups = {};

    activeFilters = {
        highlight: false,
        timeRange: false,
        search: false,
        lasso: false
    }

    constructor() {
        emitter.on(E.RECEIVED_ARTICLE, this.onArticleReceive.bind(this));
        emitter.on(E.RECEIVED_COMMENTS, this.onCommentsReceive.bind(this));
        emitter.on(E.GRAPH_RECEIVED, this.onGraphReceive.bind(this));
        emitter.on(E.DATA_UPDATED_COMMENTS, this.resetSearchIndex.bind(this));
        emitter.on(E.COMMENT_SEARCH, this.searchComments.bind(this));
        emitter.on(E.CLEAR_FILTERS, this.clearFilters.bind(this));
        emitter.on(E.CLEAR_SEARCH_FILTER, () => this.clearFilters('search'));
    }

    appendComments(comments) {
        comments.forEach(c => {
            // some additional properties per comment
            // to manage highlighting (on click),
            // text search, lasso, and time range selection
            c.activeFilters = {
                highlight: false,
                timeRange: false,
                search: false,
                lasso: false
            }

            this.comments[c.id] = c;
        });
    }

    resetSearchIndex() {
        this.searchIndex = new JsSearch.Search(['id']);
        this.searchIndex.tokenizer = new JsSearch.StemmingTokenizer(JsSearch.stemmer, new JsSearch.SimpleTokenizer());
        this.searchIndex.addIndex('text');
        this.searchIndex.addDocuments(Object.values(this.comments));
    }

    clearFilters(filters) {
        if (!filters) filters = ['highlight', 'timeRange', 'search', 'lasso'];
        if (typeof filters === 'string') filters = [filters]

        filters.forEach(filter => this.activeFilters[filter] = false);
        Object.keys(this.comments).forEach(key => {
            filters.forEach(filter => this.comments[key].activeFilters[filter] = false);
        });
        emitter.emit(E.FILTERS_UPDATED, this.comments);
    }

    applyFilter(filter, activeIds) {
        let resultIds = new Set(activeIds);
        Object.keys(this.comments).forEach(key => {
            this.comments[key].activeFilters[filter] = resultIds.has(this.comments[key].id)
        });
        this.activeFilters[filter] = true;
        emitter.emit(E.FILTERS_UPDATED, this.comments);
    }

    searchComments(query) {
        let searchResult = this.searchIndex.search(query);
        this.applyFilter('search', searchResult.map(c => c.id))
    }

    onCommentsReceive(comments) {
        let lenBefore = Object.keys(this.comments).length;

        this.appendComments(comments);

        console.log(`Received ${comments.length} comments, DataStore.comments ` +
            `before: ${lenBefore} and after: ${Object.keys(this.comments).length} ` +
            `(diff: ${Object.keys(this.comments).length - lenBefore})`);

        emitter.emit(E.DATA_UPDATED_COMMENTS, this.comments)
    }

    onArticleReceive(article) {
        this.sources[article.articleId] = article;
    }

    onGraphReceive(graph_id, splitComments, id2idx, edges) {
        this.id2idx = id2idx;
        this.idx2id = Object.fromEntries(Object.entries(id2idx).map(([k, v]) => [v, k]));
        this.edges = edges;
        splitComments.forEach(splitComment => {
            this.comments[splitComment.id].group = splitComment.grp_id;
            if (!(splitComment.grp_id in this.groups)) this.groups[splitComment.grp_id] = [];
            this.groups[splitComment.grp_id].push(splitComment.id);

            let text = this.comments[splitComment.id].text;
            //this.comments[splitComment.id].splits = splitComment.splits.map((split) => text.substr(split.s, split.e));
            this.comments[splitComment.id].splits = splitComment.splits;
        });

        emitter.emit(E.REDRAW);
    }

    getCommentText(commentId, split) {
        let bounds = this.comments[commentId].splits[split];
        return this.comments[commentId].text.substr(bounds.s, bounds.e);
    }

    getArticleIds() {
        return Object.keys(this.sources).map(k => parseInt(k));
    }

}

let data = new DataStore();

export { GRAPH_CONFIG, API_SETTINGS, DataStore, Article, data, EDGE_TYPES, EDGE_TYPES_REV };
import { E as TinyEmitter } from "../libs/tinyemitter.js";

const emitter = new TinyEmitter();

const E = {
    // backend successfully responded with an article + comments
    RECEIVED_ARTICLE: 'RECEIVED_ARTICLE', // DATA: full response object
    // same as RECEIVED_ARTICLE
    RECEIVED_COMMENTS: 'RECEIVED_COMMENTS', // DATA: only list of comments
    // request for article failed
    ARTICLE_FAILED: 'ARTICLE_FAILED', // DATA: full response object or error obj
    // URL was submitted
    NEW_SOURCE_URL: 'NEW_SOURCE_URL', // DATA: URL as str
    // user chose an example from the list
    EXAMPLE_SELECTED: 'EXAMPLE_SELECTED', // DATA: story object including list of URLs
    // is emitted when a new graph should be requested from backend
    GRAPH_REQUESTED: 'GRAPH_REQUESTED', // DATA: empty
    GRAPH_REQUEST_FAILED: 'GRAPH_REQUEST_FAILED',
    GRAPH_RECEIVED: 'GRAPH_RECEIVED',
    REDRAW: 'REDRAW',
    DRAWING_CONFIG_CHANGED: 'DRAWING_CONFIG_CHANGED'
};
Object.freeze(E);

export { emitter, E }
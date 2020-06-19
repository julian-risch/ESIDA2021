// import { E as TinyEmitter } from "../libs/tinyemitter.js";


class TinyEmitter {
    constructor() {
        this.listeners = {};
        this.listenerCounter = 0;
    }

    on(name, callback, ctx, selfDestruct) {
        (this.listeners[name] || (this.listeners[name] = {}))[this.listenerCounter] = {
            fn: callback,
            ctx: ctx,
            selfDestruct: !!selfDestruct
        };
        let ret = [name, this.listenerCounter];
        this.listenerCounter++;
        return ret;
    }

    once(name, callback, ctx) {
        return this.on(name, callback, ctx, true);
    }

    emit(name, ...data) {
        //console.log(name, data, this);
        Object.entries(this.listeners[name]).forEach(([key, listener]) => {
            listener.fn.apply(listener.ctx, data);
            if (listener.selfDestruct)
                this.off([name, key]);
        });
    }

    off(key) {
        if (key instanceof (Array))
            delete this.listeners[key[0]][key[1]];
        else
            delete this.listeners[key];
    }
}

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
    // request to fully redraw the graph
    REDRAW: 'REDRAW',
    // request to stop the simulation
    SIMULATION_STOP: 'SIMULATION_STOP',
    // the DRAWING_CONFIG was changed
    DRAWING_CONFIG_CHANGED: 'DRAWING_CONFIG_CHANGED', // DATA: path in config, new value
    // comments in the DataStore were updated
    DATA_UPDATED_COMMENTS: 'DATA_UPDATED_COMMENTS', // DATA: the dict of comments
    // a comment was selected for highlight (or unselected)
    COMMENT_SELECTED: 'COMMENT_SELECTED', // DATA: commentId (optional)
    // request to remove all filters
    CLEAR_FILTERS: 'CLEAR_FILTERS', // DATA: none
    // request to remove search filter
    CLEAR_SEARCH_FILTER: 'CLEAR_SEARCH_FILTER', // DATA: none
    // emitted when the search box updated
    COMMENT_SEARCH: 'COMMENT_SEARCH', // DATA: current search query
    // emitted when the DataSource has updated the 'active' field
    FILTERS_UPDATED: 'FILTERS_UPDATED', // DATA: comment object with updated 'active' field

};
Object.freeze(E);

export { emitter, E }
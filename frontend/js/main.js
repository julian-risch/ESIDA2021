import { ELEMENTS, SidebarSourceElement } from "./env/elements.js";
import { emitter, E } from "./env/events.js"
import { data } from "./env/data.js";
import { URI } from "./env/uri.js";
import { EXAMPLE_STORIES } from "./env/examples.js";
import { GRAPH_CONFIG, API_SETTINGS } from "./env/data.js";

ELEMENTS.SIDEBAR.addEmptySource();

// if there is a state stored in URL, get the source URLs/IDs
// FIXME: before release, swap the following two lines.
//let urls = URI.get_arr('source', []);
let urls = URI.get_arr('source', EXAMPLE_STORIES[6].sources);

// if there is a state stored in URL, update internal GRAPH_CONFIG
let graph_config = URI.get_arr('graph_config', []);
if (graph_config.length > 0) {
    console.log('Override graph config from URL: ', graph_config)
    graph_config.forEach(c => {
        const conf = c.split('|')
        Object.entries(JSON.parse(conf[1])).forEach(cc => {
            GRAPH_CONFIG[conf[0]][cc[0]] = cc[1];
        });
    });
}

// alternatively, one can simply select the number of the example by index
const example = URI.get_int('example', undefined);
if (example !== undefined) {
    urls = EXAMPLE_STORIES[example].sources;

    graph_config = EXAMPLE_STORIES[example].graph_config || {};
    if (Object.keys(graph_config).length > 0) {
        console.log('Override graph config from example: ', graph_config)
        Object.entries(graph_config).forEach(c => {
            Object.entries(c[1]).forEach(cc => {
                GRAPH_CONFIG[c[0]][cc[0]] = cc[1];
            });
        });
    }
}

// override API settings
API_SETTINGS.GRAPH_IGNORE_CACHE = URL.get_bool('graph_ignore_cache', API_SETTINGS.GRAPH_IGNORE_CACHE);

// if data was collected, trigger source fetch events
if (urls.length > 0) {
    urls.forEach((url) => emitter.emit(E.NEW_SOURCE_URL, url));

    // some magic, so it waits till data for all articles was received
    // and then triggers event to get graph
    let countdown = {
        cntdwn: urls.length,
        e1: emitter.on(E.RECEIVED_ARTICLE, () => countdown.cb()),
        e2: emitter.on(E.ARTICLE_FAILED, () => countdown.cb()),
        cb: () => {
            countdown.cntdwn--;
            if (countdown.cntdwn <= 0) {
                emitter.off(countdown.e1);
                emitter.off(countdown.e2);
                emitter.emit(E.GRAPH_REQUESTED);
            }
        }
    }
    console.log(data);
}
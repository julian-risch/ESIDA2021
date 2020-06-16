import { ELEMENTS, SidebarSourceElement } from "./env/elements.js";
import { emitter, E } from "./env/events.js"
import { data } from "./env/data.js";
import { URI } from "./env/uri.js";
//import { ComExDrawing } from "./drawing/drawing.js";

ELEMENTS.SIDEBAR.addEmptySource();

// for faster testing
let init_urls = [
    'https://www.zeit.de/digital/internet/2020-03/fake-news-coronavirus-falschnachrichten-luegen-panikmache', // id=149
    150, // https://www.faz.net/aktuell/wissen/medizin-ernaehrung/corona-patienten-italienische-verhaeltnisse-koennen-wir-haendeln-16674388.html
    151
];

// if testing is over, uncomment this:
//init_urls = [];

let urls = URI.get_arr('source', init_urls);
console.log(urls);
if (urls.length > 0) {
    urls.forEach((url) => emitter.emit(E.NEW_SOURCE_URL, url));
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

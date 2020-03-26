import { ELEMENTS, SidebarSourceElement } from "./env/elements.js";
import { emitter, E } from "./env/events.js"
import { data } from "./env/data.js";
//import { ComExDrawing } from "./drawing/drawing.js";

ELEMENTS.SIDEBAR.addEmptySource();

emitter.emit(E.NEW_SOURCE_URL,
    'https://www.zeit.de/digital/internet/2020-03/fake-news-coronavirus-falschnachrichten-luegen-panikmache' // id=149
);

emitter.emit(E.NEW_SOURCE_URL,
    150 //https://www.faz.net/aktuell/wissen/medizin-ernaehrung/corona-patienten-italienische-verhaeltnisse-koennen-wir-haendeln-16674388.html
);
emitter.emit(E.NEW_SOURCE_URL, 151);

setTimeout(() => {
    emitter.emit(E.GRAPH_REQUESTED)
}, 1000);

console.log(data);
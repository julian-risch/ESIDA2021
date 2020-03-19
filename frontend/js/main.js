import { ELEMENTS, SidebarSourceElement } from "./env/elements.js";
import { emitter, E } from "./env/events.js"

/*
ELEMENTS.SIDEBAR.addSource('zeit',
    'https://www.zeit.de/digital/internet/2020-03/fake-news-coronavirus-falschnachrichten-luegen-panikmache',
    'So erkennen Sie, welche Nachrichten zum Coronavirus stimmen',
    new Date(2020, 3, 16, 13, 32), 175);
ELEMENTS.SIDEBAR.addEmptySource();
*/

ELEMENTS.SIDEBAR.addEmptySource();
emitter.emit(E.NEW_SOURCE_URL,
    'https://www.zeit.de/digital/internet/2020-03/fake-news-coronavirus-falschnachrichten-luegen-panikmache');
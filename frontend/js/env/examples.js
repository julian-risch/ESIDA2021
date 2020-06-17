import { LANG } from "./lang.js";
import { URI } from "./uri.js";
import { E, emitter } from "./events.js";

const EXAMPLE_STORIES = [
    {
        title: LANG.EMPTY_EXAMPLE.s,
        sources: []
    }, {
        title: 'Brände in Australien',
        sources: [
            'https://www.faz.net/aktuell/politik/ausland/braende-in-australien-zur-flucht-ist-es-zu-spaet-16567672.html',
            //'https://www.spiegel.de/wissenschaft/natur/buschfeuer-in-australien-satellitenbild-zeigt-riesige-rauchwolke-a-1303595.html',
            //'https://www.zeit.de/news/2020-01/06/australiens-einzigartige-tierwelt-leidet-unter-den-braenden',
            //'https://www.zeit.de/gesellschaft/zeitgeschehen/2020-01/australien-feuer-buschbraende-waldbraende-duerre-fs',
            //'https://www.tagesschau.de/ausland/buschfeuer-australien-127.html',
            //'https://www.zeit.de/news/2020-01/06/australiens-premier-buschbraende-dauern-noch-monate',
            //'https://www.faz.net/aktuell/gesellschaft/zukunft-nach-braenden-unklar-tier-massensterben-durch-braende-in-australien-16565020.html',
            //'https://www.zeit.de/news/2020-01/05/buschfeuer-in-australien-schrecken-nimmt-kein-ende',
            'https://www.welt.de/vermischtes/article204780066/Buschbraende-in-Australien-Millionen-Tiere-sterben-Pink-spendet-500-000-Dollar.html'
        ]
    }, {
        title: 'Erdogan bei Putin',
        sources: [
            'https://www.zeit.de/politik/ausland/2020-01/libyen-eu-kritik-unterstuetzung-militaer-ausland',
            'https://www.welt.de/newsticker/dpa_nt/infoline_nt/brennpunkte_nt/article204846606/Buergerkrieg-in-Libyen-Krisengespraech-von-Erdogan-und-Putin.html',
            'https://www.tagesschau.de/ausland/tuerkei-russland-123.html',
            'https://www.sueddeutsche.de/politik/konflikte-buergerkrieg-in-libyen-krisengespraech-von-erdogan-und-putin-dpa.urn-newsml-dpa-com-20090101-200108-99-386678'
        ]
    }, {
        title: 'Kanada vs VW',
        sources: [
            'https://www.tagesschau.de/wirtschaft/kanada-vw-strafe-dieselgate-101.html',
            'https://www.spiegel.de/wirtschaft/unternehmen/volkswagen-kanada-will-136-millionen-euro-wegen-dieselskandal-a-10b3e036-ef61-4b27-bbb6-c2cdfca716b0',
            'https://www.faz.net/aktuell/wirtschaft/unternehmen/dieselskandal-vw-muss-weitere-millionenstrafe-in-kanada-zahlen-16596295.html',
            'https://www.welt.de/regionales/niedersachsen/article205270781/Kanada-verhaengt-im-Dieselgate-Skandal-Strafe-gegen-VW.html',
            'https://www.zeit.de/wirtschaft/unternehmen/2020-01/dieselgate-kanada-millionen-strafe-volkswagen-abgasstandards',
            'https://www.welt.de/wirtschaft/article205270161/Kanada-verhaengt-im-Dieselgate-Skandal-Millionenstrafe-gegen-VW.html',
            'https://www.zeit.de/news/2020-01/23/kanada-verhaengt-millionenstrafe-gegen-vw'
        ]
    }, {
        title: 'Corona',
        sources: [
            'url1',
            'url2'
        ]
    },

];

emitter.on(E.EXAMPLE_SELECTED, (example) => {
    URI.set_val('source', example.sources, true);
})

export { EXAMPLE_STORIES };
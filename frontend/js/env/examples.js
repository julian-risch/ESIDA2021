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
                'https://www.welt.de/vermischtes/article204780066/Buschbraende-in-Australien-Millionen-Tiere-sterben-Pink-spendet-500-000-Dollar.html',// (164 Kommentare)
                'https://www.faz.net/aktuell/wissen/klimawandel-und-braende-in-australien-keine-einsicht-in-der-hoelle-16568655.html',// (246 Kommentare)
                //'https://www.zeit.de/wissen/2020-01/buschfeuer-australien-waldbraende-buschbraende-region-duerre-3',// (684 Kommentare)
                'https://taz.de/Waldbraende-in-Australien/!5653513',// (7 Kommentare)
                'https://www.spiegel.de/panorama/gesellschaft/australien-fordert-240-000-buerger-wegen-feuern-zur-evakuierung-auf-a-9e171bd7-042f-475e-a29d-66cee34f8966'// (32 Kommentare)

                //'https://www.faz.net/aktuell/politik/ausland/braende-in-australien-zur-flucht-ist-es-zu-spaet-16567672.html',
                //'https://www.welt.de/vermischtes/article204780066/Buschbraende-in-Australien-Millionen-Tiere-sterben-Pink-spendet-500-000-Dollar.html',

                //'https://www.zeit.de/gesellschaft/zeitgeschehen/2020-01/australien-feuer-buschbraende-waldbraende-duerre-fs',// 80 comments, wrong date
                //'https://www.spiegel.de/wissenschaft/natur/buschfeuer-in-australien-satellitenbild-zeigt-riesige-rauchwolke-a-1303595.html',// no comments
                //'https://www.zeit.de/news/2020-01/06/australiens-einzigartige-tierwelt-leidet-unter-den-braenden',// no comments
                //'https://www.tagesschau.de/ausland/buschfeuer-australien-127.html', // no comments
                //'https://www.zeit.de/news/2020-01/06/australiens-premier-buschbraende-dauern-noch-monate',// no comments
                //'https://www.faz.net/aktuell/gesellschaft/zukunft-nach-braenden-unklar-tier-massensterben-durch-braende-in-australien-16565020.html',// no comments
                //'https://www.zeit.de/news/2020-01/05/buschfeuer-in-australien-schrecken-nimmt-kein-ende',// no comments
            ],
            graph_config: {
                SameCommentComparator: {
                    active: false,
                    base_weight: 1.0,
                    only_consecutive: true
                },
                SameArticleComparator: {
                    active: false,
                    base_weight: 1.0,
                    only_root: true
                },
                ReplyToComparator: {
                    active: false,
                    base_weight: 1.0,
                    only_root: true
                },
                VotesRanker: {
                    active: false
                },
                VotesFilter: {
                    active: false
                },
                PageRankBottomFilter: {
                    active: false,
                    strict: true,
                    top_k: 200,
                    descending_order: true
                },
                TemporalComparator: {
                    active: true,
                    base_weight: 1.0,
                    only_root: true,
                    max_time: 1000
                },
                RecencyRanker: {
                    active: true,
                    use_yongest: false
                },
                ReplyToNodeMerger: {
                    active: false,
                },
                TemporalEdgeFilter: {
                    active: true,
                    threshold: 0.3,
                    smaller_as: true
                },
                BottomTemporalEdgeFilter: {
                    active: false,
                    top_edges: 100,
                    descending_order: false
                },
                TemporalNodeMerger: {
                    active: false,
                    threshold: 0.3,
                    smaller_as: true
                },
                TemporalClusterer: {
                    active: true,
                    algorithm: 'GirvanNewman'
                }
            }
        }, {
            title: 'Brexit',
            sources: [
                'https://www.zeit.de/politik/ausland/2019-12/vorgezogene-neuwahl-grossbritannien-premierminister-boris-johnson',// (1087 Kommentare)
                'https://www.welt.de/politik/ausland/article204275602/UK-Wahl-Dank-Johnsons-Triumph-ist-der-Brexit-Ende-Januar-so-gut-wie-sicher.html',// (359 Kommentare)
                'https://www.faz.net/aktuell/politik/wahl-in-grossbritannien/wahl-in-grossbritannien-um-welchen-preis-kaempft-boris-johnson-16533411.html',// (204 Kommentare)
                'https://taz.de/Wahl-in-Grossbritannien/!5649610'// (ca 90 Kommentare)
            ]
        },
        {
            title: 'Erdogan bei Putin',
            sources: [
                'https://www.zeit.de/politik/ausland/2020-01/libyen-eu-kritik-unterstuetzung-militaer-ausland',
                'https://www.welt.de/newsticker/dpa_nt/infoline_nt/brennpunkte_nt/article204846606/Buergerkrieg-in-Libyen-Krisengespraech-von-Erdogan-und-Putin.html',
                'https://www.tagesschau.de/ausland/tuerkei-russland-123.html',
                'https://www.sueddeutsche.de/politik/konflikte-buergerkrieg-in-libyen-krisengespraech-von-erdogan-und-putin-dpa.urn-newsml-dpa-com-20090101-200108-99-386678'
            ]
        }
        ,
        {
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
        }
        ,
        {
            title: 'Corona',
            sources: [
                'url1',
                'url2'
            ]
        }
        ,
        {
            title: 'Default Example',
            sources: [
                'https://www.zeit.de/digital/internet/2020-03/fake-news-coronavirus-falschnachrichten-luegen-panikmache', // id=149
                150, // https://www.faz.net/aktuell/wissen/medizin-ernaehrung/corona-patienten-italienische-verhaeltnisse-koennen-wir-haendeln-16674388.html
                151
            ]
        }
    ]
;

emitter.on(E.EXAMPLE_SELECTED, (example) => {
    URI.set_val('source', example.sources, !('graph_config' in example));

    if ('graph_config' in example)
        URI.set_val('graph_config', Object.entries(example.graph_config).map((conf) =>
            `${conf[0]}|${JSON.stringify(conf[1])}`), true);
})

export { EXAMPLE_STORIES };
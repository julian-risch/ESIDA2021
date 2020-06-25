import { E, emitter } from "../env/events.js";
import { getNodes } from "../env/elements.js";
import { GUI } from "../libs/dat.gui.js";

const DRAWING_CONFIG = {
    HEIGHT: 80,
    WIDTH: 100,
    LAYOUT: {
        EDGE_TYPE_WEIGHTS: {
            REPLY_TO: 1.,
            SAME_ARTICLE: 1.,
            SIMILARITY: 1.,
            SAME_GROUP: 1.,
            SAME_COMMENT: 1.,
            TEMPORAL: 1.
        },
        CHARGE_STRENGTH:-2,
        CHARGE_MAX_DISTANCE: 150
    },
    style: function (key, setting, mode) {
        if (setting === undefined)
            return this.STYLES.DEFAULT[key];

        mode = mode ? 'pos' : 'neg';

        if (key in this.STYLES[setting][mode]) {
            return this.STYLES[setting][mode][key];
        }
        return this.STYLES.DEFAULT[key];
    },
    STYLES: {
        // set this to false, to vote-count-colouring depends on comment rather then split
        VOTE_COLOUR_BY_SPLIT: true,
        DEFAULT: {
            NODE_FILL: '#1F77B4',
            NODE_FILL_POS: '#2E8B57',
            NODE_FILL_NEG: '#B22222',
            NODE_OPACITY: 0.8,
            NODE_STROKE_WIDTH: 1.5,
            NODE_STROKE: '#fff',
            EDGE_STROKE: '#999',
            EDGE_OPACITY: 0.6,
            EDGE_MIN_STROKE_WIDTH: 1,
            EDGE_MAX_STROKE_WIDTH: 1,
            NODE_RADIUS: d => 100 * Math.sqrt(d.wgts.PAGERANK),
            NODE_PADDING: 1
        },
        HIGHLIGHT: {
            pos: {
                NODE_FILL: 'rgb(255,3,83)'
            },
            neg: {
                NODE_OPACITY: 0.3
            }
        },
        TIME_RANGE: {
            pos: {
                // stays default
            },
            neg: {
                NODE_RADIUS: d => 50 * Math.sqrt(d.wgts.PAGERANK),
                NODE_OPACITY: 0.3
            }
        },
        LASSO: {
            pos: {},
            neg: {}
        },
        SEARCH: {
            pos: {},
            neg: {}
        }
    },
    LINKS_VISIBLE: false
};

class ConfigPanel {
    constructor(parent) {
        this.gui = new GUI({ autoPlace: false });
        this.ROOT = this.gui.domElement;
        parent.appendChild(this.ROOT);


        this.add('reply_to wgt', 'LAYOUT.EDGE_TYPE_WEIGHTS.REPLY_TO', 0, 1, 0.1);
        this.add('same_article wgt', 'LAYOUT.EDGE_TYPE_WEIGHTS.SAME_ARTICLE', 0, 1, 0.1);
        this.add('same_comment wgt', 'LAYOUT.EDGE_TYPE_WEIGHTS.SAME_COMMENT', 0, 1, 0.1);
        this.add('charge strength', 'LAYOUT.CHARGE_STRENGTH', -100, 100, 1);
        this.add('charge dist', 'LAYOUT.CHARGE_MAX_DISTANCE', 1, 300, 1);
        this.add('show_links', 'LINKS_VISIBLE');
        this.addFunction('Stop Simulation', () => emitter.emit(E.SIMULATION_STOP));
        this.addFunction('Reset Drawing', () => emitter.emit(E.REDRAW));

        this.gui.close();
    }

    addFunction(name, callback) {
        let fakeObj = {};
        fakeObj[name] = callback;
        let controller = this.gui.add(fakeObj, name);
        controller.name(name);
        return controller;
    }

    add(name, key, min, max, step) {
        function getVar(key, base) {
            let path = key.split('.');
            if (path.length === 1) return [base, path[0]];
            else if (path.length > 1) return getVar(path.slice(1).join('.'), base[path[0]])
        }

        let [object, property] = getVar(key, DRAWING_CONFIG);
        let controller = this.gui.add(object, property, min, max, step);
        controller.name(name);
        controller.onFinishChange((val) => emitter.emit(E.DRAWING_CONFIG_CHANGED, key, val));
        return controller;
    }
}

export { DRAWING_CONFIG, ConfigPanel };

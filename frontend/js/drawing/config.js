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
            //SIMILARITY: 1.,
            //SAME_GROUP: 1.,
            SAME_COMMENT: 1.
        },
        CHARGE_STRENGTH: -10,
        CHARGE_MAX_DISTANCE: 150,
        FORCE_Y: .01,
        FORCE_X: .01
    },
    COLOURS: {
        NODE_FILL_DEFAULT: 'rgb(31, 119, 180)',
        EDGE_STROKE_DEFAULT: '#999',
        NODE_OPACITY_UNSELECTED: 0.3
    },
    LINKS_VISIBLE: true
};

class ConfigPanel {
    constructor(parent) {
        this.gui = new GUI({ autoPlace: false });
        this.ROOT = this.gui.domElement;
        parent.appendChild(this.ROOT);


        this.add('reply_to wgt', 'LAYOUT.EDGE_TYPE_WEIGHTS.REPLY_TO', 0, 1, 0.1);
        this.add('same_article wgt', 'LAYOUT.EDGE_TYPE_WEIGHTS.SAME_ARTICLE', 0, 1, 0.1);
        this.add('same_comment wgt', 'LAYOUT.EDGE_TYPE_WEIGHTS.SAME_COMMENT', 0, 1, 0.1);
        this.add('force_y', 'LAYOUT.FORCE_Y', 0, 1, 0.01);
        this.add('force_x', 'LAYOUT.FORCE_X', 0, 1, 0.01);
        this.add('charge strength', 'LAYOUT.CHARGE_STRENGTH', -100, 100, 1);
        this.add('charge dist', 'LAYOUT.CHARGE_MAX_DISTANCE', 1, 300, 1);
        this.add('show_links', 'LINKS_VISIBLE');
        this.addFunction('Stop Simulation', () => emitter.emit(E.SIMULATION_STOP));
        this.addFunction('Reset Drawing', () => emitter.emit(E.REDRAW));
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
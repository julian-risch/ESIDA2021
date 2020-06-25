import { DRAWING_CONFIG as CONFIG } from "./config.js";
import { EDGE_TYPES, EDGE_TYPES_REV } from "../env/data.js";
import { E, emitter } from "../env/events.js";
import { forceCluster } from "./force-cluster.js";
import { boxingForce } from "./force-box.js";

class Layout {
    constructor(nodes, edges) {
        this.nodes = nodes;
        this.edges = edges;
        /*
        NODE:
        -----
        index: 0
        orig_id: Array(2)
            0: "35950"
            1: 0
        text: "Die Temperaturen sind völlig normal für Australien."
        vx: 0.00012361933027607312
        vy: 0.0016372381510637232
        wgts:
            CLUSTER_ID: null
            DEGREE_CENTRALITY: 176
            MERGE_ID: -1
            PAGERANK: 0.0005180453073165081
            RECENCY: 0
            SIZE: 51
            TOXICITY: null
            VOTES: 38
        x: 845.8325291290723
        y: 408.67964563722035

        EDGE
        ------
        index: 4
        src: (2) [20, 0]
        tgt: (2) [22, 1]
        source: {orig_id: Array(2), text: "Keine Frage, der Mensch schafft sich sein Inferno selbst.", wgts: {…}, index: 59, x: 752.8335889578213, …}
        target:
            index: 67
            orig_id: (2) ["35972", 1]
            text: "↵"Kritiker werfen Morrison zudem vor, die Zunahme extremer Wetterereignisse infolge des Klimawandels heruntergespielt zu haben. Seine Regierung sei sich aber sehr wohl dieser Problematik bewusst, sagte Morrison am Sonnta"
            vx: 0.05382181829979985
            vy: 0.03795661685526
            wgts:
                CLUSTER_ID: null
                DEGREE_CENTRALITY: 48
                MERGE_ID: -66
                PAGERANK: 0.0021515213358733166
                RECENCY: 2283.354
                SIZE: 127
                TOXICITY: null
                VOTES: 11
            x: 798.8890025923064
            y: 264.4966316164899
        weights:
            REPLY_TO: null
            SAME_ARTICLE: null
            SAME_COMMENT: null
            SAME_GROUP: null
            SIMILARITY: null
            TEMPORAL: 0.415
         */

        this.forces = {
            // link: d3.forceLink(this.edges),
            bounds: boxingForce(this.nodes),
            center: d3.forceCenter(),
            collide: d3.forceCollide(),
            cluster: forceCluster(this.nodes),
            charge: d3.forceManyBody()
        };

        this.simulation = d3.forceSimulation(this.nodes);
        // FIXME remove again
        //this.simulation.stop();
        this.update();
        Object.entries(this.forces).forEach(([key, force]) => {
            this.simulation.force(key, force)
        });

        this.listeners = [
            emitter.on(E.DRAWING_CONFIG_CHANGED, (key) => {
                if (!key.startsWith('LAYOUT')) return;
                this.simulation.stop();
                this.update();
                this.simulation.alpha(1).restart();
            }),
            emitter.on(E.SIMULATION_STOP, () => {
                this.simulation.stop();
            })
        ];
    }

    update() {
        this.forces.cluster.iterations(1);
        if ('charge' in this.forces)
            this.forces.charge
                .strength(CONFIG.LAYOUT.CHARGE_STRENGTH)
        //.distanceMax(CONFIG.LAYOUT.CHARGE_MAX_DISTANCE);
        if ('collide' in this.forces)
            this.forces.collide
                .radius((d) => CONFIG.STYLES.DEFAULT.NODE_RADIUS(d) + CONFIG.STYLES.DEFAULT.NODE_PADDING)
                .strength(0.5);
        if ('bounds' in this.forces)
            this.forces.bounds
                .width(CONFIG.WIDTH)
                .height(CONFIG.HEIGHT)
                .margin(10)
                .invertDirection(true);
        this.forces.center.x(CONFIG.WIDTH / 2).y(CONFIG.HEIGHT / 2)
    }

    linkStrength(link) {
        let weightedWeight = (weight) => weight[1] * CONFIG.LAYOUT.EDGE_TYPE_WEIGHTS[weight[0]];

        return Object.entries(link.weights)
            .filter(weight => weight[1] !== null)
            .reduce((acc, weight) => acc + weightedWeight(weight), .0);
    }

    static drag(simulation) {
        return d3.drag()
            .on("start", (d) => {
                if (!d3.event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on("drag", (d) => {
                d.fx = d3.event.x;
                d.fy = d3.event.y;
            })
            .on("end", (d) => {
                if (!d3.event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            })
            .filter(() => d3.event.ctrlKey);
    }


    deconstructor() {
        this.simulation.stop();
        delete this.simulation;
        this.listeners.forEach((listener) => emitter.off(listener));
    }
}


export { Layout };

import { DRAWING_CONFIG as CONFIG } from "./config.js";
import { EDGE_TYPES, EDGE_TYPES_REV } from "../env/data.js";
import { E, emitter } from "../env/events.js";


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
            /*link: d3.forceLink(this.edges),
            charge: d3.forceManyBody(),
            bounds: this.boxingForce(),
            forceX: d3.forceX(CONFIG.WIDTH / 2),
            forceY: d3.forceY(CONFIG.HEIGHT / 2)*/
            center: d3.forceCenter(),//CONFIG.WIDTH / 2, CONFIG.HEIGHT / 2),
            collide: d3.forceCollide(),
            charge: d3.forceManyBody(),
            cluster: this.cluster(0.002),
            //collide: this.collide(0.002)
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
        /*
        this.forces.link
            .strength(this.linkStrength)
        //.strength(link => 1 / Math.min(data.nodes[link.source.index].count, data.nodes[link.target.index].count) + Math.sqrt(data.links[link.index].value / 574))
        // .iterations(1);
        */
        this.forces.charge
            .strength(CONFIG.LAYOUT.CHARGE_STRENGTH)
            .distanceMax(CONFIG.LAYOUT.CHARGE_MAX_DISTANCE);

       this.forces.collide
            .radius(CONFIG.STYLES.DEFAULT.NODE_RADIUS )//+ CONFIG.STYLES.DEFAULT.NODE_PADDING)
            .strength(1.0);
        this.forces.center.x(CONFIG.WIDTH/2).y(CONFIG.HEIGHT/2)
        /*
                        this.forces.forceY.strength(CONFIG.LAYOUT.FORCE_Y);
                        this.forces.forceX.strength(CONFIG.LAYOUT.FORCE_X);
                    */
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
            .filter(()=>d3.event.ctrlKey);
    }

    cluster(alpha) {

        // Find the largest node for each cluster.
        const centroids = this.nodes.reduce((acc, node) => {
            if (!(node.cluster in acc)) acc[node.cluster] = .0
            if (acc[node.cluster] < node.wgts.DEGREE_CENTRALITY) acc[node.cluster] = node;
            return acc;
        }, {});

        console.log(`Found ${Object.keys(centroids).length} centroids (MERGE_ID or CLUSTER_ID) for ${this.nodes.length} nodes.`);

        return () => this.nodes.forEach(node => {
            const centroid = centroids[node.cluster];
            if (centroid === node) return;

            const r = CONFIG.STYLES.DEFAULT.NODE_RADIUS(node);
            let x = node.x - centroid.x;
            let y = node.y - centroid.y;
            let l = Math.sqrt(x * x + y * y);
            if (l !== r) {
                l = (l - r) / l * alpha;
                node.vx -= x *= l;
                node.vy -= y *= l;
                centroid.vx += x;
                centroid.vy += y;
            }
        });
    }

    collide(alpha) {
        const quadTree = d3.quadtree().addAll(this.nodes);
        const that = this;
        return () => {
            this.nodes.forEach(node => {
                let r = CONFIG.STYLES.DEFAULT.NODE_RADIUS(node);
                const nx1 = node.x - r;
                const nx2 = node.x + r;
                const ny1 = node.y - r;
                const ny2 = node.y + r;
                quadTree.visit(function (quad, x1, y1, x2, y2) {
                    if (quad.point && (quad.point !== node)) {
                        let x = node.x - quad.point.x;
                        let y = node.y - quad.point.y;
                        let l = Math.sqrt(x * x + y * y);
                        r = CONFIG.STYLES.DEFAULT.NODE_RADIUS(quad.point) +
                            (node.wgts.CLUSTER_ID !== quad.point.wgts.CLUSTER_ID) * CONFIG.STYLES.DEFAULT.NODE_PADDING;
                        if (l < r) {
                            l = (-r) / l * alpha;
                            node.vx -= x *= l;
                            node.vy -= y *= l;
                            quad.point.vx += x;
                            quad.point.vy += y;
                        }
                    }
                    return x1 > nx2
                        || x2 < nx1
                        || y1 > ny2
                        || y2 < ny1;
                });
            });
        }
    }

    boxingForce() {
        return () => {
            let margin = 10;
            this.nodes.forEach(node => {
                // Of the positions exceed the box, set them to the boundary position.
                // You may want to include your nodes width to not overlap with the box.
                let newX = Math.max(margin, Math.min(CONFIG.WIDTH - margin, node.x));
                let newY = Math.max(margin, Math.min(CONFIG.HEIGHT - margin, node.y));
                if (newX !== node.x) {
                    node.x = newX;
                    node.vx = 0;
                }
                if (newY !== node.y) {
                    node.y = newY;
                    node.vy = 0;
                }
            });
        }
    }

    deconstructor() {
        this.simulation.stop();
        delete this.simulation;
        this.listeners.forEach((listener) => emitter.off(listener));
    }
}

export { Layout };
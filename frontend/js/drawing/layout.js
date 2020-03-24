import { DRAWING_CONFIG as CONFIG } from "./config.js";
import { EDGE_TYPES, EDGE_TYPES_REV } from "../env/data.js";
import { E, emitter } from "../env/events.js";

class Layout {
    constructor(nodes, edges) {
        this.nodes = nodes;
        this.edges = edges;

        this.forces = {
            link: d3.forceLink(this.edges),
            charge: d3.forceManyBody(),
            collide: d3.forceCollide(),
            center: d3.forceCenter(CONFIG.WIDTH / 2, CONFIG.HEIGHT / 2),
            bounds: this.boxingForce()
        };

        this.simulation = d3.forceSimulation(this.nodes);
        this.update();
        Object.entries(this.forces).forEach(([key, force]) => {
            this.simulation.force(key, force)
        });

        emitter.on(E.DRAWING_CONFIG_CHANGED, () => {
            this.simulation.stop();
            this.update();
            this.simulation.alpha(1).restart();
        });
    }

    update() {
        this.forces.link
            .strength(this.linkStrength)
            //.strength(link => 1 / Math.min(data.nodes[link.source.index].count, data.nodes[link.target.index].count) + Math.sqrt(data.links[link.index].value / 574))
            .iterations(1);

        this.forces.charge
            .strength(CONFIG.CHARGE_STRENGTH)
            .distanceMax(CONFIG.CHARGE_MAX_DISTANCE);

        this.forces.collide.radius(5);
        //.force("bounds", this.boxingForce());
    }

    linkStrength(link) {
        let weightedWeight = (weight) => weight[0] * CONFIG.EDGE_TYPE_WEIGHTS[EDGE_TYPES_REV[weight[1]]];
        return link.weights.reduce((acc, weight) => acc + weightedWeight(weight), .0);
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
            });
    }

    boxingForce() {
        return () => {
            let margin = 10;
            for (let node of this.nodes) {
                // Of the positions exceed the box, set them to the boundary position.
                // You may want to include your nodes width to not overlap with the box.
                node.x = Math.max(margin, Math.min(CONFIG.WIDTH - margin, node.x));
                node.y = Math.max(margin, Math.min(CONFIG.HEIGHT - margin, node.y));
            }
        }
    }
}

export { Layout };
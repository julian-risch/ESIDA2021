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
            bounds: this.boxingForce(),
            forceX: d3.forceX(CONFIG.WIDTH / 2),
            forceY: d3.forceY(CONFIG.HEIGHT / 2)
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
            })];
    }

    update() {
        this.forces.link
            .strength(this.linkStrength)
        //.strength(link => 1 / Math.min(data.nodes[link.source.index].count, data.nodes[link.target.index].count) + Math.sqrt(data.links[link.index].value / 574))
        // .iterations(1);

        this.forces.charge
            .strength(CONFIG.LAYOUT.CHARGE_STRENGTH)
            .distanceMax(CONFIG.LAYOUT.CHARGE_MAX_DISTANCE);

        this.forces.collide.radius(5);
        //.force("bounds", this.boxingForce());

        this.forces.forceY.strength(CONFIG.LAYOUT.FORCE_Y);
        this.forces.forceX.strength(CONFIG.LAYOUT.FORCE_X);
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
            });
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
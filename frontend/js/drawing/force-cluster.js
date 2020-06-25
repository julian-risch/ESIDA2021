// clustering: http://bl.ocks.org/mccannf/5548435
// collision detection: https://bl.ocks.org/mbostock/3231298
import { DRAWING_CONFIG as CONFIG } from "./config.js";

function jiggle() {
    return (Math.random() - 0.5) * 1e-6;
}

function constant(x) {
    return function () {
        return x;
    };
}

function forceCluster(nodes) {
    let radius,
        centroids,
        iterations = 1;

    function force2(alpha) {
        for (let k = 0; k < iterations; ++k) {
            nodes.forEach(node => {
                const centroid = centroids[node.cluster];
                if (centroid === node) return;

                const r = CONFIG.STYLES.DEFAULT.NODE_RADIUS(node) + CONFIG.STYLES.DEFAULT.NODE_RADIUS(centroid);
                let x = node.x - centroid.x || jiggle();
                let y = node.y - centroid.y || jiggle();
                let l = Math.sqrt(x * x + y * y);
                if (l !== r) {
                    l = ((l - r) / l) * alpha;
                    x *= l;
                    y *= l;
                    node.x -= x;
                    node.y -= y;
                    centroid.x += x;
                    centroid.y += y;
                }
            });
        }
    }

    function force(alpha) {
        for (let k = 0; k < iterations; ++k) {
            nodes.forEach(node => {
                const centroid = centroids[node.cluster];
                if (centroid === node) return;

                const r = CONFIG.STYLES.DEFAULT.NODE_RADIUS(node) + CONFIG.STYLES.DEFAULT.NODE_RADIUS(centroid);
                let x = node.x + node.vx - centroid.x - centroid.vx || jiggle();
                let y = node.y + node.vy - centroid.y - centroid.vy || jiggle();
                let l = Math.sqrt(x * x + y * y);
                if (l !== r) {
                    l = ((l - r) / l) * alpha;
                    x *= l;
                    y *= l;
                    node.vx -= x;
                    node.vy -= y;
                    centroid.vx += x;
                    centroid.vy += y;
                }
            });
        }
    }

    function initialize() {
        if (!nodes) return;

        // Find the largest node for each cluster.
        centroids = nodes.reduce((acc, node) => {
            if (!(node.cluster in acc)) acc[node.cluster] = node;
            if (node.wgts.DEGREE_CENTRALITY > acc[node.cluster].wgts.DEGREE_CENTRALITY)
                acc[node.cluster] = node;
            return acc;
        }, {});

        console.log(`Found ${Object.keys(centroids).length} centroids (MERGE_ID or CLUSTER_ID) for ${nodes.length} nodes.`);
    }

    force.initialize = function (_) {
        nodes = _;
        initialize();
    };

    force.iterations = function (_) {
        return arguments.length ? (iterations = +_, force) : iterations;
    };


    return force;
}

export { forceCluster }
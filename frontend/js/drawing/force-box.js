import { DRAWING_CONFIG as CONFIG } from "./config.js";

function constant(x) {
    return function () {
        return x;
    };
}

function boxingForce(nodes) {
    let margin = 10,
        height,
        width,
        invertDirection = true,
        iterations = 1;

    function force(alpha) {
        for (let k = 0; k < iterations; ++k) {
            nodes.forEach(node => {
                // Of the positions exceed the box, set them to the boundary position.
                // You may want to include your nodes width to not overlap with the box.
                let newX = Math.max(margin, Math.min(width - margin, node.x));
                let newY = Math.max(margin, Math.min(height - margin, node.y));
                if (newX !== node.x) {
                    node.x = newX;
                    if (invertDirection)
                        node.vx = node.vx * (-1);
                    else
                        node.vx = 0;
                }
                if (newY !== node.y) {
                    node.y = newY;
                    if (invertDirection)
                        node.vy = node.vy * (-1);
                    else
                        node.vy = 0;
                }
            });
        }
    }

    function initialize() {
        if (!nodes) return;
    }

    force.initialize = function (_) {
        nodes = _;
        initialize();
    };
    force.iterations = function (_) {
        return arguments.length ? (iterations = +_, force) : iterations;
    };
    force.margin = function (_) {
        return arguments.length ? (margin = +_, force) : margin;
    };
    force.width = function (_) {
        return arguments.length ? (width = +_, force) : width;
    };
    force.height = function (_) {
        return arguments.length ? (height = +_, force) : height;
    };
    force.invertDirection = function (_) {
        return arguments.length ? (invertDirection = +_, force) : invertDirection;
    };
    return force;
}

export { boxingForce };
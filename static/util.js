function maskInputAlphaNum(input) {
    input.addEventListener("keydown", e => {
        if (!isAlphanumeric(e.key) && e.key !== "Backspace" && e.key !== "Enter") {
            e.preventDefault();
        }
    })
}

function isAlphanumeric(c) {
    return "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_".indexOf(c) > -1;
}

// PIXI-tween
function shake(sprite, axis, amplitude) {
    sprite._tw = PIXI.tweenManager.createTween(sprite);

    let tw2 = PIXI.tweenManager.createTween(sprite);
    tw2.time = 1;
    tw2.from({[axis]: sprite[axis] + 1});
    tw2.to({[axis]: sprite[axis]});
    tw2.easing = constant();
    tw2.expire = true;

    let tw = sprite._tw;
    tw.time = 400;
    tw.expire = true;
    tw.easing = shakeFn(12, amplitude);
    tw.from({[axis]: sprite[axis]});
    tw.to({[axis]: sprite[axis] + 1});
    tw.chain(tw2);
    tw.start();
}

let shakeFn = function (duration, amplitude) {
    let counter = duration;

    return function (t) {
        if (counter <= 0) {
            return 1;
        }
        counter--;
        return (Math.random() - 0.5) * amplitude * (counter / duration);
    };
}

let constant = function () {
    return function (t) {
        return 1;
    }
}

// LocalStorage stuff
function selfOid() {
    return localStorage.getItem("oid")
}

function selfName() {
    return localStorage.getItem("name")
}

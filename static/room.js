const ROOM = window.location.pathname.slice(1);

let APP;

let STYLE;

let CARDS = {};
let TEXT;

let COLS, ROWS;
let EXTRA_COLS = 0, EXTRA_ROWS = 0;

let XSCALE, YSCALE;

const CELL_PAD = 4;
const CARD_PAD = 20;

let WIDTH;
let HEIGHT;
let PORTRAIT;

let CARD_WIDTH, CARD_HEIGHT;

function calculateDimensions() {

    WIDTH = window.innerWidth;
    HEIGHT = window.innerHeight;
    PORTRAIT = WIDTH < HEIGHT;

    COLS = 2 + EXTRA_COLS;
    ROWS = 2 + EXTRA_ROWS;

    if (PORTRAIT) {
        CARD_WIDTH = 0.65 * WIDTH;
        CARD_HEIGHT = (1 / 3) * HEIGHT;

        XSCALE = (WIDTH) / ((CARD_WIDTH + CARD_PAD) * COLS + CARD_PAD)
        YSCALE = (HEIGHT / 3) / ((CARD_HEIGHT + CARD_PAD * 2) * ROWS + CARD_PAD * 2)
    } else {
        CARD_WIDTH = (1 / 3) * WIDTH;
        CARD_HEIGHT = 0.70 * HEIGHT;

        XSCALE = (WIDTH / 3) / ((CARD_WIDTH + CARD_PAD) * COLS + CARD_PAD)
        YSCALE = (HEIGHT) / ((CARD_HEIGHT + CARD_PAD * 2) * ROWS + CARD_PAD * 2)
    }
}

maskInputAlphaNum(document.getElementById("name"));

function createGameModal() {
    document.getElementById("create-game").style.display = "block";
}

function onCreateGameSubmit() {
    const gameMode = document.getElementById("game-mode").value;
    const pool = document.getElementById("pool").value;
    const maximumSize = document.getElementById("maximum-size").value;
    const middleFree = document.getElementById("middle-free").value;

    SOCKET.emit("create_game", {
        "oid": selfOid(),
        "room": ROOM,
        "mode": gameMode,
        "maximum_size": maximumSize,
        "middle_free": middleFree,
        "pool": pool.split(/\s+/).map(w => w.trim())
    })
    return false;
}

function openCreateUserModal() {
    document.getElementById("create-user").style.display = "block";
}

function onCreateUserSubmit() {
    const name = document.getElementById("name").value;
    localStorage.setItem("name", name)

    SOCKET.emit("join", {
        room: ROOM,
        name: name
    });
    return false;
}


function initApp() {
    APP = new PIXI.Application({
        antialias: false,
        width: window.innerWidth,
        height: window.innerHeight,
        resolution: 2,
        resizeTo: window
    });

    document.body.appendChild(APP.view);
    APP.renderer.autoDensity = true;
    APP.renderer.resize(window.innerWidth, window.innerHeight);

    // pixi-tween init
    function animate() {
        window.requestAnimationFrame(animate);
        APP.renderer.render(APP.stage);
        PIXI.tweenManager.update();
    }

    animate();
}

function makeCell(cell, size, card_oid, xscale, yscale) {

    const g = new PIXI.Graphics();
    const sprite = new PIXI.Sprite();

    sprite._baseColor = cell.checked ? STYLE.cell.checked : STYLE.cell.base;
    sprite._color = sprite._baseColor;

    sprite._update = function () {
        g.clear();
        g.beginFill(this._color);
        g.drawRect(0, 0,
            ((xscale * CARD_WIDTH - CELL_PAD) / size - CELL_PAD),
            ((yscale * CARD_HEIGHT - CELL_PAD) / size - CELL_PAD)
        );
        g.endFill()

        if (g.children.length === 0) {
            const maxWidth = g.width - 4;
            const maxHeight = g.height - 4;

            const text = new PIXI.Text(cell.text, {
                    fontFamily: STYLE.font,
                    fontSize: xscale === 1 ? 16 : 10,
                    fill: STYLE.cell.text,
                    align: "center",
                    breakWords: true,
                    wordWrap: true,
                    wordWrapWidth: maxWidth,
                }
            );
            text.anchor.set(0.5, 0.5)
            text.x = g.width / 2;
            text.y = g.height / 2;

            if (text.height < maxHeight) {
                g.addChild(text);
            }
        }

        this.texture = APP.renderer.generateTexture(g, PIXI.SCALE_MODES.LINEAR, 3);
    }

    sprite._destroy = function () {
        if (this._tw) {
            this._tw.stop();
            this._tw.remove();
        }
        this.destroy({texture: true, baseTexture: true, children: true});
    }

    sprite._update()

    if (xscale === 1) {
        sprite.interactive = true;
        sprite.buttonMode = true;

        sprite.on("mouseover", () => {
            sprite._color = STYLE.cell.hover;
            sprite._update();
        })

        sprite.on("mouseout", () => {
            sprite._color = sprite._baseColor;
            sprite._update();
        })

        sprite.on("click", () => {
            SOCKET.emit("cell_click", {
                "oid": selfOid(),
                "cidx": cell.cidx,
                "card": card_oid,
                "room": ROOM
            })
        })
    }

    return sprite
}

function BingoCard(oid, parent, small = false) {

    let g = new PIXI.Graphics();

    g._update = function (card) {

        let xscale = small ? XSCALE : 1;
        let yscale = small ? YSCALE : 1;

        g.clear();
        g.setMatrix(new PIXI.Matrix().scale(xscale, yscale));
        g.lineStyle(3, STYLE.card.base);
        g.drawRect(0, 0, CARD_WIDTH, CARD_HEIGHT);

        if (!this._text) {
            this._text = new PIXI.Text(parent, {
                    fontFamily: STYLE.font,
                    fontSize: 16,
                    fill: STYLE.card.text,
                    align: "center",
                    strokeThickness: 3
                }
            );
            this._text.anchor.set(0.5, 0.35)
        } else {
            g.removeChild(this._text);
        }
        this._text.x = g.width / 2;
        this._text.y = g.height;
        g.addChild(this._text);

        this._self = card;
        let toDestroy = [];
        g.children.forEach(child => {
            if (child !== this._text) {
                toDestroy.push(child);
            }
        })
        toDestroy.forEach(x => {
            x._destroy();
        })

        let size = Math.floor(Math.sqrt(this._self.cells.length))

        for (let col = 0; col < size; col++) {
            for (let row = 0; row < size; row++) {

                let cidx = col * size + row;
                let cell = this._self.cells[cidx];
                cell.cidx = cidx;

                let c = makeCell(cell, size, oid, xscale, yscale)
                c.x = (c.width + CELL_PAD) * row + CELL_PAD + 1;
                c.y = (c.height + CELL_PAD) * col + CELL_PAD + 1;

                if (cell.shake) {
                    cell.shake = false;
                    shake(c, "x", 16 * xscale)
                    shake(c, "y", 16 * xscale)
                    shake(g, "x", 3 * xscale)
                    shake(g, "y", 3 * xscale)
                }

                g.addChild(c);
            }
        }
    }

    return g;
}

function makeText() {

    const PAD = 5;

    const t = new PIXI.Text("", {
        fontFamily: STYLE.font,
        fontSize: 38,
        fill: STYLE.cell.text,
        strokeThickness: 2,
        align: "left",
        breakWords: true,
        wordWrap: true,
        wordWrapWidth: WIDTH / 3 - PAD * 2,
    });

    t.x = WIDTH / 2;
    t.y = PORTRAIT ? HEIGHT / 2 : HEIGHT / 12;
    t.anchor.set(0.5, 0.5)

    t._display = function (text, timeout) {
        APP.stage.children.sort((a, _) => {
            return a === t ? 1 : 0;
        })
        t.text = text

        if (t._to) {
            window.clearTimeout(t._to);
        }
        t._to = window.setTimeout(() => {
            t.text = ""
        }, timeout)
    }

    return t;
}

function updateCards() {

    let nextRow = [0, 0];
    let nextCol = [0, 0];
    let counter = 0;

    // Increase room size
    if (Object.keys(CARDS).length - 2 > (ROWS * COLS * 2)) {
        if (ROWS > COLS) {
            EXTRA_COLS += 1;
        } else {
            EXTRA_ROWS += 1;
        }
        calculateDimensions();
        updateCards();
    }

    let toAdd = [];
    Object.keys(CARDS).forEach(key => {

        if (key === "SELF") {
            return;
        }
        counter += 1;

        let card = CARDS[key];

        if (CARDS["SELF"] === card) {
            //Self
            card.x = WIDTH / 2 - (CARD_WIDTH / 2);
            card.y = HEIGHT / 2 - (CARD_HEIGHT / 2);

        } else {
            // Other
            let nextSide = (counter + 1) % 2;
            card.x = ((CARD_WIDTH + CARD_PAD) * nextCol[nextSide] + CARD_PAD) * XSCALE;
            card.y = ((CARD_HEIGHT + CARD_PAD * 2) * nextRow[nextSide] + CARD_PAD * 2) * YSCALE;

            if (nextSide === 1) {
                if (PORTRAIT) {
                    card.y += HEIGHT * (2 / 3);
                } else {
                    card.x += WIDTH * (2 / 3);
                }
            }

            if (nextCol[nextSide] === COLS - 1) {
                nextCol[nextSide] = 0;
                nextRow[nextSide] += 1;
            } else {
                nextCol[nextSide] += 1;
            }
        }

        APP.stage.removeChild(card);
        card._update(card._self);
        toAdd.push(card);
    })

    // Add cards in reverse for z-index
    for (let i = toAdd.length - 1; i >= 0; i--) {
        APP.stage.addChild(toAdd[i]);
    }
}

window.onresize = function () {
    updateCards();
}

// DEBUG
let DEBUG = {
    dupCounter: 0,
};
DEBUG.dupCard = function () {
    DEBUG.dupCounter += 1;
    const card = new BingoCard(selfOid(), "DEBUG" + DEBUG.dupCounter, true);
    card._self = CARDS["SELF"]._self
    CARDS[DEBUG.dupCounter] = card;
    updateCards();
}


calculateDimensions();
initApp();
initNet();

let SOCKET;

function initNet() {
    SOCKET = io("/socket");

    SOCKET.on("connect", () => {
        let oid = selfOid();
        if (oid) {
            SOCKET.emit("join", {
                room: ROOM,
                name: selfName(),
                oid: oid,
            });
        } else {
            openCreateUserModal();
        }
    });

    SOCKET.on("message", msg => {
        TEXT._display(msg.text, msg.timeout)
    })

    SOCKET.on("end_message", msg => {
        alert(msg.text)
    })

    SOCKET.on("game_state", msg => {
        if (msg.state === "PLAYING") {
            document.getElementById("create-game").style.display = "none";

            SOCKET.emit("get_card", {
                "oid": selfOid(),
                "room": ROOM,
            })
        } else if (msg.state === "ENDED") {
            SOCKET.emit("get_end_message")
        }
    })

    SOCKET.on("card_state", msg => {
        if (CARDS.hasOwnProperty("SELF")) {
            if (CARDS.hasOwnProperty(msg.card.oid)) {
                CARDS[msg.card.oid]._update(msg.card)
            } else {
                const card = new BingoCard(msg.card.oid, msg.parent, true);
                card._self = msg.card
                CARDS[msg.card.oid] = card;
                updateCards();
            }
        }
    })

    SOCKET.on("get_card_rsp", msg => {
        // Add self card
        let card = new BingoCard(msg.card.oid, msg.parent);

        card._self = msg.card;
        CARDS[msg.card.oid] = card;
        CARDS["SELF"] = card;
        updateCards();
    })

    SOCKET.on("join_rsp", msg => {

        if (msg.ok === false) {
            openCreateUserModal();
            return;
        }

        document.getElementById("create-user").style.display = "none";

        localStorage.setItem("oid", msg.oid)
        document.title = msg.oid

        if (msg.state === "CREATING") {
            createGameModal();

        } else if (msg.state === "PLAYING") {
            SOCKET.emit("get_card", {
                "oid": selfOid(),
                "room": ROOM,
            })
        } else if (msg.state === "ENDED") {
            SOCKET.emit("get_end_message")
        }
    });

    SOCKET.on("room_join", msg => {
        // console.log(msg);
    })

    SOCKET.on("style_state", msg => {
        STYLE = msg.style
        APP.renderer.backgroundColor = STYLE.background;

        if (TEXT === undefined) {
            TEXT = makeText();
            APP.stage.addChild(TEXT);
        }
    })
}

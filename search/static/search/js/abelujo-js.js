
function sellUndo(id) {
    // Undo the sell of the given id.
    if (confirm("Voulez-vous annuler toute cette vente ?")){
        console.log("--- sellUndo id", id);
        fetch(`/api/sell/${id}/undo`, {
            method: 'POST',
        })
            .then((response) => {
                console.log(response);
                // console.log(response.text());
                return response.json();
            })
            .then((myJson) => {
                console.log("json: ", myJson);
                if (myJson.status == true) {
                    console.log('removing line.');
                    var lines = document.querySelectorAll(`#sell${id}`);
                    for (var i = 0; i < lines.length; i++) {
                        lines[i].remove();
                    }
                }
            })
            .catch((error) => {
                console.error('There has been a problem with your fetch operation:', error);
            });
    }
}

function card_add_one_to_default_place(card_id) {
    // Called from: card_show.jade.
    console.log("-- hello add 1 ", card_id);
    let places_ids_qties = "";

    let url = "/api/card/" + card_id + "/add";  // interpolation clunky…
    console.log("-- POSTing to ", url);
    fetch(url, {
        method: 'POST',
        body: "default_place: 1"  // JSON.stringify a bit picky…
    })
        .then((response) => {
            console.log("response is ", response);
            return response.json();
        })
        .then((myJson) => {
            if (myJson.status == 200) {
                console.log("-- success. New quantity: ", myJson.quantity);;
                // beware when default_place changes of name :S
                let elt = document.getElementById('default_place_quantity');
                if (elt) {
                    elt.innerText = myJson.quantity;
                    let in_stock = document.getElementById('in_stock');
                    let quantity_in_stock = in_stock.innerText;
                    quantity_in_stock = parseInt(quantity_in_stock);
                    in_stock.innerText = quantity_in_stock + 1;

                    Notiflix.Notify.Success('+1');
                }
            }
            else {
                console.log("status is not success: ", myJson.status);
            }
        })
        .catch((error) => {
            console.error('There has been a problem with your fetch operation:', error);
        });
}

function card_remove_one_from_default_place(card_id) {
    // copy-paste is aweful O_o
    console.log("-- hello remove 1 ", card_id);
    let places_ids_qties = "";

    let url = "/api/card/" + card_id + "/add";  // interpolation clunky…
    console.log("-- POSTing to ", url);
    fetch(url, {
        method: 'POST',
        body: "default_place: -1"  // JSON.stringify a bit picky…
    })
        .then((response) => {
            console.log("response is ", response);
            return response.json();
        })
        .then((myJson) => {
            if (myJson.status == 200) {
                console.log("-- success. New quantity: ", myJson.quantity);;
                // beware when default_place changes of name :S
                let elt = document.getElementById('default_place_quantity');
                if (elt) {
                    elt.innerText = myJson.quantity;
                    let in_stock = document.getElementById('in_stock');
                    let quantity_in_stock = in_stock.innerText;
                    quantity_in_stock = parseInt(quantity_in_stock);
                    in_stock.innerText = quantity_in_stock - 1;

                    Notiflix.Notify.Success('-1');
                }
            }
            else {
                console.log("status is not success: ", myJson.status);
            }
        })
        .catch((error) => {
            console.error('There has been a problem with your fetch operation:', error);
        });
}

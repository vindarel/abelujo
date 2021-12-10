//
// Add a select for shelves, populated with JS (not even needed…).
// Save the new shelf value.
//
// Used where there is a reservation button:
// - card_show.jade
// - searchresults.jade

function url_id (url) {
    // extract an id
    let re = /\/(\d+)/;
    let res = url.match(re);
    if (res && res.length == 2) {
        return res[1];
    }
    return null;
};

function is_isbn(text) {
    let reg = /^[0-9]{10,13}/g;
    return text.match(reg);
};

(function() {
    let shelves = [];
    let shelf_select = document.getElementById('shelf-select');

    // function url_id (url) {
    //     // extract an id
    //     let re = /\/(\d+)/;
    //     let res = url.match(re);
    //     if (res && res.length == 2) {
    //         return res[1];
    //     }
    //     return null;
    // };

    function get_shelves() {
        // Create a select with all shelves.
        // This is doable with the template…

        let current_shelf_name = document.getElementById('shelf-name');
        if (!current_shelf_name) {
            console.log("No shelf line on this page.");
            return;
        }

        fetch("/api/shelfs", {
            method: 'GET',
        })
            .then((response) => {
                return response.json();
            })
            .then((myJson) => {
                shelves = myJson;
                let select_td = document.getElementById('shelf-select-td');
                if (current_shelf_name && current_shelf_name.innerText !== "") {
                    current_shelf_name = current_shelf_name.innerText;
                    // Hide it in favour of the JS-generated select.
                    // current_shelf_name.display = 'none';
                }
                let elt = document.getElementById('shelf-select');
                // Create blank shelf.
                let option = document.createElement("option");;
                option.text = "";
                option.pk = -1;
                option.value = -1;
                elt.appendChild(option);
                for (var i = 0; i < shelves.length; i++) {
                    let option = document.createElement("option");;
                    option.text = shelves[i].fields.name;
                    // option.innerHTML = shelves[i].fields.name;
                    option.pk = shelves[i].pk;
                    option.value = i;
                    if (current_shelf_name.trim() === shelves[i].fields.name.trim()) {
                        option.selected = "selected";
                        elt.selectedIndex = i;
                    }
                    elt.appendChild(option);
                }
            })
            .catch((error) => {
                console.error('There has been a problem with your fetch operation:', error);
            });
    }

    if (shelf_select) {
        shelf_select.addEventListener('change', (event) => {
            let options = shelf_select.options;
            let pk = parseInt(event.target.value);
            if (pk !== -1 && shelves[pk] !== undefined) {
                let shelf = shelves[pk];
                pk = shelf.pk;
            }
            update_shelf(pk);
            console.log("new_shelf: ", event.target.value, pk);
        });
    }

    function update_shelf(shelf_id) {
        let card_id = url_id(window.location.pathname);
        let url = "/api/cards/update";
        let json_body = '{"card_id": ' + card_id + ', ' +
            '"shelf_id": ' + shelf_id +
            '}';
        fetch(url, {
            method: 'POST',
            body: json_body,  // JSON.stringify a bit picky…
        })
            .then((response) => {
                return response.json();
            })
            .then((myJson) => {
                if (myJson.status == 200) {
                    Notiflix.Notify.Success('OK');
                }
                else {
                    console.log("status is not success: ", myJson.status);
                }
            })
            .catch((error) => {
                console.error('There has been a problem with your fetch operation:', error);
            });

    };

    get_shelves();

}
)();

function do_focus() {
    // XXX: no effect?
    document.getElementById('#clients-input').trigger('focus');
}

function focus_input() {
    // XXX: no effect? :(
    console.log("--- focus!");
    // window.setTimeout(do_focus(), 2*1000);
}

function validate_reservation() {
    // Get the card id (or ISBN),
    // get the client id,
    // call the api,
    // reload the page (unless on searchresults).
    let elt = document.getElementById('clients-input');
    let clients_select = document.getElementById('clients-select')
    console.log("-- elt: ", elt);
    let name = elt.value;
    console.log("-- client name ? ", name);
    if (!name) {
        console.log("no client selected");
        return;
    }
    let client_id = undefined;
    // get id
    for (var i = 0; i < clients_select.options.length; i++) {
        if (clients_select.options[i].value == name) {
            client_id = clients_select.options[i].id;
            console.log("-- client id: ", client_id);
            break;
        }
    }

    if (client_id != undefined) {
        let card_id = url_id(window.location.pathname);

        if (!card_id) {
            // check in local storage (for searchresults page).
            card_id = window.localStorage.getItem('isbn_for_reservation');
            console.log("--- found isbn: ", card_id);
        }
        if (!card_id) {
            console.log("--- OOPS: we didn't find a card id or isbn to reserve.");
            return;
        }

        let url = "/api/card/" + card_id + "/reserve/" + client_id;
        console.log("url: ", url);
        fetch(url, {
            method: 'POST',
            headers: {'X-CSRFToken': getCSRFToken()}
        })
            .then((response) => {
                return response.json();
            })
            .then((myJson) => {
                console.log("response: ", myJson);
                if (myJson.status == "success") {
                    Notiflix.Notify.Success('OK');
                    // Close the modal.
                    // so we have JQuery.
                    $('#reserveModal').modal('toggle');

                    // Reload page (unless on searchresults page).
                    if (!is_isbn(card_id)) {
                        location.reload(true);
                    }
                }
                else {
                    console.log("status is not success: ", myJson.status);
                    Notiflix.Notify.Warning('mmh');
                }
            })
            .catch((error) => {
                console.error('There has been a problem with your fetch operation:', error);
            });

    }

};

function cancel_reservation(client_id) {
    console.log(" -- delete ", client_id);
    let card_id = url_id(window.location.pathname);

    if (!card_id) {
        // check in local storage (for searchresults page).
        card_id = window.localStorage.getItem('isbn_for_reservation');
        console.log("--- isbn localstorage: ", card_id);
    }
    if (card_id == undefined || card_id == null) {
        console.log("--- OOPS: we didn't find a card id or isbn to reserve.");
        return;
    }

    let url = "/api/card/" + card_id + "/cancelreservation/" + client_id;
    console.log("url: ", url);
    fetch(url, {
        method: 'POST',
        headers: {'X-CSRFToken': getCSRFToken()}
    })
        .then((response) => {
            return response.json();
        })
        .then((myJson) => {
            console.log("response: ", myJson);
            if (myJson.status == "success") {
                Notiflix.Notify.Success('OK');
                // Close the modal.
                // so we have JQuery.
                $('#reserveModal').modal('toggle');

                // data cleanup
                // cleanup localstorage or beware of async events ?

                // Reload page.
                location.reload(true);
            }
            else {
                console.log("status is not success: ", myJson.status);
                Notiflix.Notify.Warning('mmh');
            }
        })
        .catch((error) => {
            console.error('There has been a problem with your fetch operation:', error);
        });
};

function save_isbn_for_reservation (isbn) {
    // Save in local storage so that the modal can pick it up easily.
    // Can the modal know which button clicked it?
    console.log("--- saving isbn ", isbn);
    console.log(" -- this? ", this);
    window.localStorage.setItem('isbn_for_reservation', isbn);
};

function is_isbn(text) {
    let reg = /^[0-9]{10,13}/g
    return text.match(reg);
};

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
                let in_stock = document.getElementById('in_stock');
                let quantity_in_stock = in_stock.innerText;
                console.log("quantity_in_stock: ", quantity_in_stock);
                quantity_in_stock = parseInt(quantity_in_stock);
                in_stock.innerText = quantity_in_stock + 1;
                if (elt) {
                    elt.innerText = myJson.quantity;
                }
                Notiflix.Notify.Success('+1');
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
                let in_stock = document.getElementById('in_stock');
                let quantity_in_stock = in_stock.innerText;
                quantity_in_stock = parseInt(quantity_in_stock);
                in_stock.innerText = quantity_in_stock - 1;
                if (elt) {
                    elt.innerText = myJson.quantity;
                }
                Notiflix.Notify.Success('-1');
            }
            else {
                console.log("status is not success: ", myJson.status);
            }
        })
        .catch((error) => {
            console.error('There has been a problem with your fetch operation:', error);
        });
}

function card_command(card_id) {
    // Called from: card_show.jade.
    console.log("-- command 1 ", card_id);
    let places_ids_qties = "";

    let url = "/api/card/" + card_id + "/command";
    console.log("-- POSTing to ", url);
    fetch(url, {
        method: 'POST'
    })
        .then((response) => {
            console.log("response is ", response);
            return response.json();
        })
        .then((myJson) => {
            if (myJson.status == 200 || myJson.status == "success") {
                console.log("-- success.");;
                Notiflix.Notify.Success('OK');

                // Update quantity.
                let elt = document.getElementById('nb_to_command_' + card_id);
                elt.innerText = myJson.data.nb;
            }
            else {
                console.log("status is not success: ", myJson.status);
                Notiflix.Notify.Warning("OK ou pas ?");
            }
        })
        .catch((error) => {
            console.error('There has been a problem with your fetch operation:', error);
            Notiflix.Notify.Warning("An error occured, sorry. We have been notified.");
        });

}

function card_catalogue_select(card_id) {
    // Called from: card_show.jade.
    console.log("-- select for catalogue ", card_id);
    let places_ids_qties = "";

    let url = "/api/card/" + card_id + "/select_catalogue";
    console.log("-- POSTing to ", url);
    fetch(url, {
        method: 'POST'
    })
        .then((response) => {
            console.log("response is ", response);
            return response.json();
        })
        .then((myJson) => {
            if (myJson.status == 200 || myJson.status == "success") {
                // Update and toggle the heart colour.
                var heart_selector = "heart-" + card_id;
                let elt = document.getElementById(heart_selector);
                if (elt != null && elt != undefined) {
                    if (myJson.data.is_catalogue_selection) {
                        elt.style = "background-color: pink";
                    } else {
                        elt.style = "";
                    }
                    Notiflix.Notify.Success('OK');
                }
                else {
                    console.warn("warn: we did not find ", heart_selector);
                }
            }
            else {
                console.log("status is not success: ", myJson.status);
                Notiflix.Notify.Warning("OK ou pas ?");
            }
        })
        .catch((error) => {
            console.error('There has been a problem with your fetch operation:', error);
            Notiflix.Notify.Warning("An error occured, sorry. We have been notified.");
        });

}

function card_catalogue_exclude(card_id) {
    // Called from: card_show.jade.
    console.log("-- exclude from catalogue ", card_id);
    let places_ids_qties = "";

    let url = "/api/card/" + card_id + "/exclude_catalogue";
    console.log("-- POSTing to ", url);
    fetch(url, {
        method: 'POST'
    })
        .then((response) => {
            console.log("response is ", response);
            return response.json();
        })
        .then((myJson) => {
            if (myJson.status == 200 || myJson.status == "success") {
                // Update and toggle the exclude colour.
                var heart_selector = "exclude-" + card_id;
                let elt = document.getElementById(heart_selector);
                console.log("--- got elt: ", elt);
                if (elt != null && elt != undefined) {
                    if (myJson.data.is_excluded_for_website) {
                        elt.style = "background-color: pink";
                    } else {
                        elt.style = "";
                    }
                    Notiflix.Notify.Success('OK');
                }
                else {
                    console.warn("warn: we did not find ", heart_selector);
                }
            }
            else {
                console.log("status is not success: ", myJson.status);
                Notiflix.Notify.Warning("OK ou pas ?");
            }
        })
        .catch((error) => {
            console.error('There has been a problem with your fetch operation:', error);
            Notiflix.Notify.Warning("An error occured, sorry. We have been notified.");
        });

}

function getCookie(name) {
    // Used to get Django's CSRF token.
    // source: Django documentation.
    // Usage: getCookie('csrftoken') => getCSRFToken()
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};

function getCSRFToken(){
    return getCookie('csrftoken');
};

/* Hide and show the menu. */
// Doesn't work on Chrome 87 ? O_o Functions not loaded (on time).
function collapseMenu() {
    var menu  = document.getElementById('sidebar-wrapper');
    var wrapper = document.getElementById('wrapper');
    menu.style.width = 0;
    wrapper.style.paddingLeft = 0;
};

function showMenu() {
    var menu  = document.getElementById('sidebar-wrapper');
    var wrapper = document.getElementById('wrapper');
    menu.style.width = "250px";
    wrapper.style.paddingLeft = "250px";
};

function toggleMenu() {
    var menu  = document.getElementById('sidebar-wrapper');
    if (menu.getAttribute('data-menu-collapsed') == "true") {
        showMenu();
        menu.setAttribute('data-menu-collapsed', false);
    } else {
        collapseMenu();
        menu.setAttribute('data-menu-collapsed', true);
    }
};

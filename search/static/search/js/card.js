//
// Add a select for shelves, populated with JS (not even needed…).
// Save the new shelf value.
//

(function() {
    console.log("hello card");

    let shelves = [];
    let shelf_select = document.getElementById('shelf-select');

    function url_id (url) {
        // extract an id
        let re = /\/(\d+)/;
        let res = url.match(re);
        if (res && res.length == 2) {
            return res[1];
        }
        return null;
    };

    function get_shelves() {
        // Create a select with all shelves.
        // This is doable with the template…
        fetch("/api/shelfs", {
            method: 'GET',
        })
            .then((response) => {
                return response.json();
            })
            .then((myJson) => {
                shelves = myJson;
                let current_shelf_name = document.getElementById('shelf-name');
                let select_td = document.getElementById('shelf-select-td');
                if (current_shelf_name && current_shelf_name.innerText !== "") {
                    current_shelf_name = current_shelf_name.innerText;
                    // Hide it in favour of the JS-generated select.
                    // current_shelf_name.display = 'none';
                }
                let elt = document.getElementById('shelf-select');
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

    shelf_select.addEventListener('change', (event) => {
        let options = shelf_select.options;
        let new_shelf = shelves[parseInt(event.target.value)];
        update_shelf(new_shelf.pk);
    });

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

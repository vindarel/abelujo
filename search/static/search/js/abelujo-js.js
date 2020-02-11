
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
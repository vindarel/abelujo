//
// Add an event listener to not validate the form when the barcode scanner
// "hits" Enter.
//

(function() {
    console.log("hello card create");

    let elt = document.getElementById('id_isbn');
    let price = document.getElementById('id_price');
    elt.addEventListener('keydown', (event) => {
        console.log("-- event: ", event);
        if(event.keyCode==13){
            console.log("--dont!");
            event.keyCode=9;
            event.preventDefault();
            price.focus();
        }
    });

}
)();

//import { f } from "./platforms/zon.js"

//f()

let modalClose = document.querySelector('#add-source-modal .close');
let modal = document.getElementById('add-source-modal');

modalClose.onclick = () => {
    modal.style.display = 'none';
};
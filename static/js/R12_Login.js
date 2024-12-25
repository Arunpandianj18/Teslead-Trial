
var id;

document.querySelectorAll("tr").forEach((row) => {
  row.addEventListener("click", (e) => {
    console.log(e.target.parentElement.querySelector(".uniqueid").innerHTML)
    id = e.target.parentElement.querySelector(".uniqueid").innerHTML;
    var form = document.querySelector(".overlay form")
    var hiddeninput = document.createElement("input");
    hiddeninput.value = id;
    hiddeninput.setAttribute("name", "id")
    hiddeninput.setAttribute("type", "hidden");
    form.appendChild(hiddeninput);

  });
});

var closeButton = document.getElementById("close");
console.log(closeButton)
var overlay = document.getElementsByClassName("overlay")[0];
closeButton.addEventListener("click", () => {
  overlay.style.opacity = "0";
  setTimeout(() => {
    overlay.style.display = "none";
  }, 500);
});

// var viewdetailButton = document.getElementById("vdbutton");
// viewdetailButton.addEventListener("click", (event) => {
//   event.preventDefault();
//   viewDetail();
// });

var id;

function viewDetail(element) {
//   console.log(element.parentElement)
  overlay.style.display = "flex";
  overlay.style.opacity = "1";
  document.getElementById("passfield").focus();
}

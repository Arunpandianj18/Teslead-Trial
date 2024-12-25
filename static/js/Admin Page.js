// var panelcontent = document.querySelectorAll(".dashboardpanelcontent > div");
// console.log(panelcontent);
// panelcontent.forEach((element) => {
//   element.addEventListener("click", (event) => {
//     panelcontent.forEach((c) => (c.style.background = ""));
//     document.querySelectorAll(".board").forEach((board) => {
//       if (event.target.innerHTML.toLowerCase() == board.id.toLowerCase()) {
//         board.style.display = "Block";
//         event.target.style.background = "#2a0079";
//       } else {
//         board.style.display = "none";
//       }
//     });
//   });
// });

var csrfToken = null;
csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

try {
  const csrfToken = document.querySelector(
    'input[name="csrfmiddlewaretoken"]'
  ).value;
} catch (error) {
  console.log("[Error] : " + error);
}

var adminoptions = [
  "Dashboard",
  "Product",
  "Alarm System",
  "Configuration",
  "Reports",
  "Analytics",
];
var useroptions = ["Dashboard"];
var r12options = ["Dashboard", "Reports"];

var type = "{{ type }}"; // Correctly getting the value of 'type'
console.log("My type: " + type);

document.querySelectorAll(".dashboardpanelcontent > div").forEach((element) => {
  var text = element.innerHTML;
  if (type === "admin") {
    if (adminoptions.includes(text)) {
      element.style.display = "block";
    } else {
      element.style.display = "none";
    }
  } else if (type === "user") {
    if (useroptions.includes(text)) {
      element.style.display = "block";
    } else {
      element.style.display = "none";
    }
  }
});

function setDate() {
  let currentDate = new Date();
  let day = String(currentDate.getDate()).padStart(2, "0");
  let month = String(currentDate.getMonth() + 1).padStart(2, "0");
  let year = currentDate.getFullYear();
  let hours = currentDate.getHours();
  let minutes = String(currentDate.getMinutes()).padStart(2, "0");
  let seconds = String(currentDate.getSeconds()).padStart(2, "0"); // Get seconds and pad to two digits
  let ampm = hours >= 12 ? "PM" : "AM";
  hours = hours % 12;
  hours = hours ? hours : 12; // Adjust 12-hour format

  let formattedDateTime = `${day}-${month}-${year} ${hours}:${minutes}:${seconds} ${ampm}`; // Include seconds

  document.getElementsByClassName("dt")[0].innerHTML = formattedDateTime;
}

setDate();

setInterval(setDate, 1000);

var productbody = document.querySelectorAll(".product-body");
var additem = document.getElementsByClassName("additem")[0];

document.getElementById("productadd").addEventListener("click", () => {
  productbody.forEach((element) => {
    element.style.display = "none";
  });
  additem.style.display = "flex";
  console.log("overflow change : ")
  console.log(productbody[1].parentElement)
  productbody[1].parentElement.style.overflowY = "visible";
});

async function deleteproduct(element) {
  console.log(parseInt(element.parentElement.classList[0]));
  var id = parseInt(element.parentElement.classList[0]);
  var formdata = new FormData();
  formdata.append("id", id);
  var response = await fetch("deleteproduct", {
    method: "post",
    headers: {
      "x-CSRFToken": csrfToken,
    },
    body: formdata,
  });
  var data = await response.text();
  if (data == "deleted") {
    window.location.href = "admin_product";
  }
}

async function updateproduct(element) {
  var formdata = new FormData();
  console.log(
    "================================================================================================="
  );
  formdata.append("id", element.parentElement.classList[0]);
  console.log("this is the id:" + element.parentElement.classList[0]);

  var response = await fetch("getproductbyid", {
    method: "post",
    headers: {
      "X-CSRFToken": csrfToken,
    },
    body: formdata,
  });
  var data = await response.json();
  console.log(data);
  var inputlist = [
    "product_id",
    "product_name",
    "product_description",
    "size",
    "class",
    "type",
    "hshell_set_pressure",
    "hshell_set_holding_time",
    "hshell_set_duration",
    "hseat_set_pressure",
    "hseat_set_holding_time",
    "hseat_set_duration",
    "ashell_set_pressure",
    "ashell_set_holding_time",
    "ashell_set_duration",
    "aseat_set_pressure",
    "aseat_set_holding_time",
    "aseat_set_duration",
  ];
  // inputlist.forEach(item => {
  //   console.log(data.product_id)
  //   document.getElementById(item).value = data[item]
  // })

  console.log("executing for loop");
  for (var item in data[0]) {
    console.log(item);
    console.log(data[0][item]);
    document.getElementById(item).value = data[0][item];
  }

  productbody.forEach((element) => {
    element.style.display = "none";
  });
  additem.style.display = "flex";
  productbody[1].parentElement.style.overflowY = "visible";
}

var additemsave = document.getElementById("additemsavebutton");
var additemcancel = document.getElementById("additemcancelbutton");

// additemsave.addEventListener("click", () => {
//   productbody[0].style.display = "flex";
//   productbody[1].style.display = "table";
//   additem.style.display = "none";
// });

// additemcancel.addEventListener("click", () => {
//   productbody[0].style.display = "flex";
//   productbody[1].style.display = "table";
//   additem.style.display = "none";
// });

var alarmadd = document.getElementById("alarmadd");
var alarmbody = document.querySelectorAll(".alarm-body");
var alarmadditem = document.getElementsByClassName("alarmadditem")[0];
console.log(alarmbody);

alarmadd.addEventListener("click", () => {
  alarmbody.forEach((element) => {
    element.style.display = "none";
  });
  alarmadditem.style.display = "flex";
});

async function deletealarm(element) {
  console.log(element.parentElement.classList[0]);
  var id = parseInt(element.parentElement.classList[0]);
  var formdata = new FormData();
  formdata.append("id", id);
  var response = await fetch("deletealarm", {
    method: "post",
    headers: {
      "X-CSRFToken": csrfToken,
    },
    body: formdata,
  });

  var data = await response.text();
  if (data == "deleted") {
    window.location.href = "admin_alarm_system";
  }
}

async function updatealarm(element) {
  console.log(element.parentElement.classList[0]);
  console.log(
    "=============================================================================="
  );
  var id = element.parentElement.classList[0];
  var formdata = new FormData();
  formdata.append("id", id);
  var response = await fetch("getalarmbyid", {
    method: "post",
    headers: {
      "X-CSRFToken": csrfToken,
    },
    body: formdata,
  });

  var data = await response.json();

  console.log(data);

  for (let key in data) {
    console.log("key:" + key);
    document.getElementById(key).value = data[key];
    console.log(document.getElementById(key));
  }

  alarmbody.forEach((element) => {
    element.style.display = "none";
  });
  alarmadditem.style.display = "flex";
}

var alarmsave = document.getElementById("alarmsave");
var alarmcancel = document.getElementById("alarmcancel");

// alarmsave.addEventListener("click", async () => {
//   console.log("alarm save");
//   const alarmID = document.querySelector('input[name="alarm_id"]').value;
//   const alarmName = document.querySelector('input[name="alarm_name"]').value;

//   const csrfToken = document.querySelector(
//     'input[name="csrfmiddlewaretoken"]'
//   ).value;

//   try {
//     // Send the data to the Django backend using fetch
//     const response = await fetch("/alarm_system/", {
//       // Ensure the port is correct (8000 by default)
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//         "X-CSRFToken": csrfToken,
//       },
//       body: JSON.stringify({
//         alarm_id: alarmID,
//         alarm_name: alarmName,
//       }),
//     });

//     if (!response.ok) {
//       throw new Error("Network response was not ok");
//     }
//     console.log("before json response");
//     var data = await response.text();
//     console.log(data);
//     data = JSON.parse(data);
//     console.log("after json response");
//     // If successfully saved to the database, update the alarm-body table
//     const table = document.querySelector(".alarmbodydata");
//     const newRow = document.createElement("tr");
//     newRow.innerHTML = `
//       <td>${data.alarm_id}</td>
//       <td>${data.alarm_name}</td>
//       <td>
//         <img src="static/css/images/pencil.png" alt="Edit" />
//         <img src="static/css/images/cross.png" alt="Delete" />
//       </td>
//     `;
//     table.appendChild(newRow);

//     // Clear the input fields after submission
//     document.querySelector('input[name="alarm_id"]').value = "";
//     document.querySelector('input[name="alarm_name"]').value = "";
//   } catch (error) {
//     console.error("Error:", error);
//   }

//   alarmbody[0].style.display = "flex";
//   alarmbody[1].style.display = "table";
//   alarmadditem.style.display = "none";
// });

// alarmcancel.addEventListener("click", () => {
//   alarmbody[0].style.display = "flex";
//   alarmbody[1].style.display = "table";
//   alarmadditem.style.display = "none";
// });

function addProduct(event) {
  event.preventDefault();
}

const ctx = document.getElementById("myLineChart").getContext("2d");

async function getgraphdata() {
  console.log("fetching from database");
  var response = await fetch("getgraphdata");
  console.log("fetching complete");
  var result = await response.json();
  console.log("converted to json");
  var pressure = [];
  var time = [];
  result.forEach((row) => {
    pressure.push(row.pressure);
    time.push(row.date_time.split("T")[1]);
  });

  console.log(pressure.length + ":" + time.length);
  var res = [pressure, time, result];
  console.log("returning res");
  return res;
}

async function writegraph() {
  console.log("before function");
  var [pressure, time, result] = await getgraphdata();
  console.log("after function");

  console.log(pressure);
  console.log(time);
  const myLineChart = new Chart(ctx, {
    type: "line", // Specify chart type
    data: {
      // labels: ["January","February","March","April","May","June","July","August",], // X-axis labels
      labels: time,
      datasets: [
        {
          label: "Sales Data", // Label for the dataset
          // data: [30, 40, 45, 50, 49, 60, 90, 180], // Data points
          data: pressure,
          borderColor: "rgba(75, 192, 192, 1)", // Line color
          backgroundColor: "rgba(75, 192, 192, 0.2)", // Fill color under the line
          borderWidth: 2, // Line thickness
          fill: true, // Fill the area under the line
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true, // Start the y-axis at 0
        },
      },
    },
  });
  console.log("==========================================");
  console.log(result);
}
//   var graphdata = [];
//   result.forEach(row => {
//     xy = {};
//     xy["x"]=row.pressure;
//     xy["y"]=row.date_time.split("T")[1]
//     graphdata.push(xy)
//   })

//   var xyValues = graphdata;

//   new Chart(ctx, {
//     type: "line",
//     data: {
//       datasets: [{
//         pointRadius: 4,
//         pointBackgroundColor: "rgb(0,0,255)",
//         data: xyValues
//       }]
//     },
//     options: {
//       legend: {display: false},
//       scales: {
//         xAxes: [{ticks: {min: 40, max:160}}],
//         yAxes: [{ticks: {min: 6, max:16}}],
//       }
//     }
//   });
// }

writegraph();

// alarmdetails

// document.getElementById('alarmsave').addEventListener('click', function(e) {
//   e.preventDefault();

//   const alarmID = document.querySelector('input[name="alarm_id"]').value;
//   const alarmName = document.querySelector('input[name="alarm_name"]').value;

//   const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

//   fetch('/alarm_system/', {
//       method: 'POST',
//       headers: {
//           'Content-Type': 'application/json',
//           'X-CSRFToken': csrfToken
//       },
//       body: JSON.stringify({
//           alarm_id: alarmID,
//           alarm_name: alarmName
//       })
//   })
//   .then(response => response.json())
//   .then(data => {
//       // Update the table with the new data
//       const table = document.querySelector('.alarm-body');
//       const newRow = document.createElement('tr');
//       newRow.innerHTML = `
//           <td>${data.alarm_id}</td>
//           <td>${data.alarm_name}</td>
//           <td>
//               <img src="{% static 'css/images/pencil.png' %}" alt="" />
//               <img src="{% static 'css/images/cross.png' %}" alt="" />
//           </td>
//       `;
//       table.appendChild(newRow);

//       // Clear the input fields
//       document.querySelector('input[name="alarm_id"]').value = '';
//       document.querySelector('input[name="alarm_name"]').value = '';
//   });
// });

function closetab() {
  alert("closing");
  window.close();
}

async function checkhmiconnection() {
  var response = await fetch("/checkhmiconnection");
  var data = await response.text();
  console.log(data);
  try {
    if (data == "green") {
      document.getElementById("hmiconnectioncircle").style.backgroundColor =
        data;
      document.getElementById("hmiconnectioncircle").innerHTML = "";
      document.getElementById("startbutton").disabled = false;
    } else {
      document.getElementById("hmiconnectioncircle").style.backgroundColor =
        data;
      document.getElementById("hmiconnectioncircle").innerHTML = "!";
      document.getElementById("startbutton").disabled = true;
    }
  } catch (error) {
    console.log("[Error] : " + error);
  }
}

setInterval(checkhmiconnection, 1000);

async function checkr12connection() {
  var response = await fetch("/checkr12connection");
  var data = await response.text();
  console.log(data);
  try {
    if (data == "green") {
      document.getElementById("r12connectioncircle").style.backgroundColor =
        data;
      document.getElementById("r12connectioncircle").innerHTML = "";
    } else {
      document.getElementById("r12connectioncircle").style.backgroundColor =
        data;
      document.getElementById("r12connectioncircle").innerHTML = "!";
    }
  } catch (error) {
    console.log("[Error] : " + error);
  }
}

setInterval(checkr12connection, 1000);

async function checkalarmsystemconnection() {
  var response = await fetch("/checkalarmsystemconnection");
  var data = await response.text();
  console.log(data);
  try {
    if (data == "green") {
      document.getElementById(
        "alarmsystemconnectioncircle"
      ).style.backgroundColor = data;
      document.getElementById("alarmsystemconnectioncircle").innerHTML = "";
    } else {
      document.getElementById(
        "alarmsystemconnectioncircle"
      ).style.backgroundColor = data;
      document.getElementById("alarmsystemconnectioncircle").innerHTML = "!";
    }
  } catch (error) {
    console.log("[Error] : " + error);
  }
}

setInterval(checkalarmsystemconnection, 1000);

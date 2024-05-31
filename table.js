// Define the IDs of your checkboxes
const checkboxIds = ["toggleCalculation", "toggleRealMoney"];

// Initialize checkboxes based on saved settings
checkboxIds.forEach((id) => {
  const checkbox = document.getElementById(id);
  const isChecked = JSON.parse(localStorage.getItem(id)); // Convert string back to boolean

  // Check if there was a saved state; if not, default to false
  checkbox.checked = isChecked === null ? false : isChecked;
});

document.addEventListener("DOMContentLoaded", async () => {
  // Fetch data initially if needed
  await fetchDataAndDisplay();

  // Add event listeners for checkboxes
  document.getElementById("toggleCalculation").addEventListener("change", function () {
    const table = document.querySelector("#price-table");
    if (this.checked) {
      table.classList.add("show-calculation");
      table.classList.add("hide-calculation");
    } else {
      table.classList.remove("show-calculation");
      table.classList.remove("hide-calculation");
    }
    // Save state to localStorage
    localStorage.setItem("toggleCalculation", this.checked);
  });

  document.getElementById("toggleRealMoney").addEventListener("change", function () {
    const table = document.querySelector("#price-table");
    if (this.checked) {
      table.classList.remove("hide-money");
    } else {
      table.classList.add("hide-money");
    }
    // Save state to localStorage
    localStorage.setItem("toggleRealMoney", this.checked);
  });

  // Initialize checkboxes based on saved settings
  checkboxIds.forEach((id) => {
    const checkbox = document.getElementById(id);

    // Trigger the change event to apply initial state
    checkbox.dispatchEvent(new Event("change"));
  });
});

async function fetchDataAndDisplay() {
  // Example fetch function, replace URL with your actual data source
  //const response = await fetch("https://backend.koodattu.dev/api/data/current");
  const response = await fetch("./data/current.json");
  const data = await response.json();

  // Update the timestamp display
  document.getElementById("timestamp").textContent = formatTimestamp(data.timestamp);

  createTable(data);
  displayTokens(data); // Add WoW Token ratio row
  displayCurrencies(data); // Add currency selection dropdown row
}

// Helper function to format the timestamp (optional)
function formatTimestamp(timestamp) {
  // Assuming the timestamp is in ISO format, e.g., "2024-02-08T23:52:02.887160"
  // Convert to a more readable format
  const date = new Date(timestamp);
  return date.toLocaleString("fi-FI"); // Adjust formatting as needed
}

function displayTokens(data) {
  const tbody = document.querySelector("#price-table tbody");
  const row = document.createElement("tr");
  row.id = "wow-token";
  const id = "122284";
  const itemCell = `<td><div class="item-icon-name"><img class="item-icon" src="images/${id
    .split("-")
    .pop()}.jpg"/><a href="https://www.wowhead.com/item=${id.split("-").pop()}" class="${getQualityClass(
    ""
  )}" data-wowhead="item=${id.split("-").pop()}">WoW Token</a></div></td>`;

  // Define the preferred order of regions
  const order = ["eu", "us", "tw", "kr"];

  // Sort the data based on the preferred order
  const sortedData = data.data.sort((a, b) => order.indexOf(a.region) - order.indexOf(b.region));
  let regionCells = "";
  sortedData.forEach((regionData) => {
    wow_token_ratio = regionData.wow_token_ratio;
    regionCells += `<td><div class="item-icon-name"><span >${wow_token_ratio} 
    </span>
<img class="gold-icon" src="images/122284.png"/></div></td>`;
  });
  row.innerHTML = itemCell + regionCells;
  tbody.appendChild(row);
}

function displayCurrencies(data) {
  const tbody = document.querySelector("#price-table tbody");
  const row = document.createElement("tr");
  row.id = "real-money";

  const dropdown = `<select id="currency-select">
                      <option value="own">Own Currencies</option>
                      <option value="eu">In Euros</option>
                      <option value="us">In US Dollars</option>
                      <option value="tw">In NT Dollars</option>
                      <option value="kr">In Korean Won</option>
                    </select>`;
  const itemCell = `<td><div class="item-icon-name"><img class="item-icon" src="images/credit.png"/> ${dropdown}</td>`;

  const currencies = {
    eu: { currency: "€", amount: "20" },
    us: { currency: "$", amount: "20" },
    tw: { currency: "NT$", amount: "500" },
    kr: { currency: "₩", amount: "22000" },
  };

  // Conversion ratios between currencies, hypothetical values for demonstration
  const conversionRatios = {
    eu: { eu: 1, us: 1.1, tw: 38, kr: 1300 }, // Example: 1 Euro = 1.1 USD, etc.
    us: { eu: 0.9, us: 1, tw: 34.5, kr: 1180 }, // Example: 1 USD = 0.9 Euro, etc.
    tw: { eu: 0.026, us: 0.029, tw: 1, kr: 34 }, // Example: 1 NT$ = 0.026 Euro, etc.
    kr: { eu: 0.00077, us: 0.00085, tw: 0.029, kr: 1 }, // Example: 1 Won = 0.00077 Euro, etc.
  };

  // Define the preferred order of regions
  const order = ["eu", "us", "tw", "kr"];

  // Sort the data based on the preferred order
  const sortedData = data.data.sort((a, b) => order.indexOf(a.region) - order.indexOf(b.region));
  let regionCells = "";
  sortedData.forEach((regionData) => {
    const { region, wow_token_ratio } = regionData;
    const baseCurrency = currencies[region];
    regionCells += `<td>`;
    // Handle 'own' currency display separately
    if (baseCurrency) {
      regionCells += `<span class="currency currency-own">${(baseCurrency.amount * wow_token_ratio)
        .toFixed(2)
        .toLocaleString()}&nbsp;${baseCurrency.currency}</span>`;
    }
    // Convert and display for other currencies
    Object.keys(conversionRatios).forEach((key) => {
      if (key !== "own") {
        // 'own' handled separately
        const rate = conversionRatios[region][key];
        const convertedAmount = (baseCurrency.amount * wow_token_ratio * rate).toFixed(2).toLocaleString();
        const currencySymbol = currencies[key].currency;
        regionCells += `<span class="currency currency-${key}" style="display:none;">${convertedAmount}&nbsp;${currencySymbol}</span>`;
      }
    });
    regionCells += `</td>`;
  });

  row.innerHTML = itemCell + regionCells;
  tbody.appendChild(row);

  document.getElementById("currency-select").addEventListener("change", function () {
    const selectedValue = this.value;
    document.querySelectorAll(".currency").forEach((el) => (el.style.display = "none"));
    if (selectedValue === "own") {
      document.querySelectorAll(".currency-own").forEach((el) => (el.style.display = ""));
    } else {
      document.querySelectorAll(`.currency-${selectedValue}`).forEach((el) => (el.style.display = ""));
    }
  });

  document.getElementById("currency-select").dispatchEvent(new Event("change"));
}

function createTable(data) {
  const itemsSet = new Set();
  data.data.forEach((region) => region.items.forEach((item) => itemsSet.add(item.name)));
  const items = Array.from(itemsSet);

  const table = document.getElementById("price-table");
  table.innerHTML = ""; // Clear the table first
  const thead = document.createElement("thead");
  const tbody = document.createElement("tbody");
  table.appendChild(thead);
  table.appendChild(tbody);

  // Header row with regions
  const headerRow = document.createElement("tr");
  headerRow.innerHTML = "<th>Items</th>";
  data.data.forEach((region) => {
    const th = document.createElement("th");
    th.textContent = region.region.toUpperCase();
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);

  // Rows for each item
  items.forEach((itemName) => {
    const row = document.createElement("tr");
    const itemCell = document.createElement("td");
    const item = data.data.map((region) => region.items.find((i) => i.name === itemName)).filter((i) => i)[0];
    const check = item["amount_needed"] !== undefined;
    itemCell.innerHTML = `<div class="item-icon-name"><img src="images/${
      item.id
    }.jpg" class="item-icon"/><a href="https://www.wowhead.com/item=${item.id}" class="${getQualityClass(
      item.id
    )}" data-wowhead="item=${item.id}" target="_blank">${itemName}</a>${
      check ? `<span class="white-text calculation">&nbsp;x ${item["amount_needed"] || "</span>"}` : ""
    }</div>`;
    row.appendChild(itemCell);
    data.data.forEach((region) => {
      const cell = document.createElement("td");
      const item = region.items.find((i) => i.name === itemName);
      if (item) {
        if (check) {
          cell.innerHTML = `<div class="item-icon-name"><span class="not-calculation">${Math.floor(
            item.price / 10000
          ).toLocaleString("fi-FI")}</span>
          <span class="calculation">${Math.floor((item.price / 10000) * item["amount_needed"]).toLocaleString(
            "fi-FI"
          )}</span>
          <img class="gold-icon" src="images/money-gold.gif"/></div>`;
        } else {
          cell.innerHTML = `<div class="item-icon-name">${Math.floor(item.price / 10000).toLocaleString("fi-FI")}
          <img class="gold-icon" src="images/money-gold.gif"/></div>`;
        }
      } else {
        cell.textContent = "N/A";
      }
      row.appendChild(cell);
    });

    tbody.appendChild(row);
  });
}

function getQualityClass(quality) {
  const qualityClasses = {
    common: "common",
    uncommon: "uncommon",
    rare: "rare",
    200113: "epic",
    206448: "legendary",
    artifact: "artifact",
  };
  return qualityClasses[quality] || "rare";
}

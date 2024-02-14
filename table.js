// Define the IDs of your checkboxes
const checkboxIds = ["toggleCalculation", "toggleComponents", "toggleRealMoney"];

// Initialize checkboxes based on saved settings
checkboxIds.forEach((id) => {
  const checkbox = document.getElementById(id);
  const isChecked = JSON.parse(localStorage.getItem(id)); // Convert string back to boolean

  // Check if there was a saved state; if not, default to false
  checkbox.checked = isChecked === null ? false : isChecked;
});

document.addEventListener("DOMContentLoaded", async () => {
  // Fetch data initially if needed
  await fetchData();

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

  document.getElementById("toggleComponents").addEventListener("change", function () {
    const table = document.querySelector("#price-table");
    if (this.checked) {
      table.classList.remove("hide-components");
    } else {
      table.classList.add("hide-components");
    }
    // Save state to localStorage
    localStorage.setItem("toggleComponents", this.checked);
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

async function fetchData() {
  // Simulating a fetch request - replace with actual fetch from your backend
  const response = await fetch("https://backend.koodattu.dev/api/data/current");
  const data = await response.json();

  // Update the timestamp display
  document.getElementById("timestamp").textContent = formatTimestamp(data.timestamp);

  processAndDisplayData(data);
}

// Helper function to format the timestamp (optional)
function formatTimestamp(timestamp) {
  // Assuming the timestamp is in ISO format, e.g., "2024-02-08T23:52:02.887160"
  // Convert to a more readable format
  const date = new Date(timestamp);
  return date.toLocaleString("fi-FI"); // Adjust formatting as needed
}

function processAndDisplayData(data) {
  const itemsMap = new Map();

  // Directly process each region's top-level item and its parts
  data.data.forEach((regionData) => {
    const topLevelItem = regionData.data;
    // Ensure the top-level item is correctly identified and processed
    processTopLevelItem(topLevelItem, itemsMap, regionData.region);
    // Process parts of the top-level item
    processParts(topLevelItem.parts, itemsMap, regionData.region);
  });

  displayItems(itemsMap);
  displayTokens(data);
  displayCurrencies(data);
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

function processTopLevelItem(item, itemsMap, region) {
  const itemKey = `item-${item.id}`;
  if (!itemsMap.has(itemKey)) {
    itemsMap.set(itemKey, {
      name: item.name,
      quality: item.quality,
      prices: {},
      amountNeeded: {}, // Top-level might not need this, but keeping structure consistent
    });
  }
  // Assign the top-level item's price for the current region
  itemsMap.get(itemKey).prices[region] = item.price;
}

function processParts(parts, itemsMap, region) {
  parts.forEach((part) => {
    const partKey = `item-${part.id}`;
    if (!itemsMap.has(partKey)) {
      itemsMap.set(partKey, createItemEntry(part, region));
    } else {
      itemsMap.get(partKey).prices[region] = part.price;
      if (part.amount_needed) {
        itemsMap.get(partKey).amountNeeded[region] = part.amount_needed;
      }
    }

    if (part.parts) {
      processParts(part.parts, itemsMap, region);
    }
  });
}

function createItemEntry(part, region) {
  const entry = {
    name: part.name,
    quality: part.quality,
    prices: { [region]: part.price },
    amountNeeded: {},
  };
  if (part.amount_needed) {
    entry.amountNeeded[region] = part.amount_needed;
  }
  return entry;
}

function displayItems(itemsMap) {
  const tbody = document.querySelector("#price-table tbody");

  itemsMap.forEach((details, id) => {
    const row = document.createElement("tr");
    row.id = id;
    row.innerHTML = `<td><div class="item-icon-name"><img class="item-icon" src="images/${id
      .split("-")
      .pop()}.jpg"/><a href="https://www.wowhead.com/item=${id.split("-").pop()}" class="${getQualityClass(
      details.quality
    )}" data-wowhead="item=${id.split("-").pop()}">${details.name}</a>${
      Object.values(details.amountNeeded).some((amount) => amount)
        ? `<span class="white-text calculation">&nbsp;x ${
            Object.values(details.amountNeeded).find((amount) => amount) || "</span>"
          }`
        : ""
    }</div></td>
                    ${["eu", "us", "tw", "kr"]
                      .map((region) => {
                        const price = details.prices[region] || 0;
                        const amountNeeded = details.amountNeeded[region];
                        const totalPrice = amountNeeded ? price * amountNeeded : price;
                        if (amountNeeded) {
                          return `<td><div class="item-icon-name"><span class="not-calculation">${formatGold(
                            price
                          )} </span>${
                            amountNeeded ? `<span class="calculation">${formatGold(totalPrice)} </span>` : ""
                          }<img class="gold-icon" src="images/money-gold.gif"/></div></td>`;
                        } else {
                          return `<td><div class="item-icon-name">${formatGold(
                            price
                          )}<img class="gold-icon" src="images/money-gold.gif"/></div></td>`;
                        }
                      })
                      .join("")}`;
    tbody.appendChild(row);
  });
}

function formatGold(price) {
  return Math.floor(price / 10000).toLocaleString("fi-FI");
}

function getQualityClass(quality) {
  const qualityClasses = {
    common: "common",
    uncommon: "uncommon",
    rare: "rare",
    epic: "epic",
    legendary: "legendary",
    artifact: "artifact",
  };
  return qualityClasses[quality] || "artifact";
}

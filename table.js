document.addEventListener("DOMContentLoaded", () => {
  fetchData();
  document.getElementById("toggleCalculation").addEventListener("change", function () {
    const table = document.querySelector("#price-table");
    if (this.checked) {
      table.classList.add("show-calculation");
      table.classList.add("hide-calculation");
    } else {
      table.classList.remove("show-calculation");
      table.classList.remove("hide-calculation");
    }
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
  const id = "122284";
  const itemCell = `<td><div class="item-icon-name"><img class="item-icon" src="images/${id
    .split("-")
    .pop()}.jpg"/><a href="https://www.wowhead.com/item=${id.split("-").pop()}" class="${getQualityClass(
    ""
  )}" data-wowhead="item=${id.split("-").pop()}">WoW Token</a></div></td>`;
  let regionCells = "";
  data.data.forEach((regionData) => {
    wow_token_ratio = regionData.wow_token_ratio;
    regionCells += `<td><div class="item-icon-name"><span class="not-calculation">${wow_token_ratio} 
    </span>
<img class="gold-icon" src="images/122284.png"/></div></td>`;
  });
  row.innerHTML = itemCell + regionCells;
  tbody.appendChild(row);
}

function displayCurrencies(data) {
  const tbody = document.querySelector("#price-table tbody");
  const row = document.createElement("tr");
  const id = "122284";
  const itemCell = `<td>💸 Pay-to-Win</td>`;
  let regionCells = "";
  const currencies = {
    us: { currency: "$", amount: "20" },
    eu: { currency: "€", amount: "20" },
    tw: { currency: "NT$", amount: "500" },
    kr: { currency: "₩", amount: "22000" },
  };
  data.data.forEach((regionData) => {
    const wow_token_ratio = regionData.wow_token_ratio;
    const region = regionData.region;
    regionCells += `<td>${(
      Math.round(currencies[region].amount * wow_token_ratio * 100) / 100
    ).toLocaleString()}&nbsp;${currencies[region].currency}</td>`;
  });
  row.innerHTML = itemCell + regionCells;
  tbody.appendChild(row);
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

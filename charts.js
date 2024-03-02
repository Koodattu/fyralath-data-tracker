document.addEventListener("DOMContentLoaded", () => {
  const cachedData = {}; // Cache fetched data
  const timeRangeDropdown = document.getElementById("timeRangeSelect");
  const regionDropdown = document.getElementById("regionSelect");
  const chartContext = document.getElementById("myChart").getContext("2d");
  let myChart; // Chart.js chart instance

  // Fetch initial data
  fetchDataAndUpdateChart("all", "all");

  timeRangeDropdown.addEventListener("change", () => {
    const timeRange = timeRangeDropdown.value;
    const region = regionDropdown.value;
    fetchDataAndUpdateChart(timeRange, region);
  });

  regionDropdown.addEventListener("change", () => {
    const timeRange = timeRangeDropdown.value;
    const region = regionDropdown.value;
    const transformedData = transformDataForChart(cachedData[timeRange], region);
    updateChart(transformedData);
  });

  function fetchDataAndUpdateChart(timeRange, region) {
    const endpoint = `https://backend.koodattu.dev/api/data/history/${timeRange}`;

    if (!cachedData[timeRange]) {
      fetch(endpoint)
        .then((response) => response.json())
        .then((data) => {
          cachedData[timeRange] = data; // Cache the fetched data
          const transformedData = transformDataForChart(data, region); // Transform the data for the chart
          updateChart(transformedData); // Update the chart with the transformed data
        });
    } else {
      const transformedData = transformDataForChart(cachedData[timeRange], region); // Transform the cached data for the chart
      updateChart(transformedData); // Update the chart with the transformed data
    }
  }

  function transformDataForChart(data, selectedRegion) {
    // Assuming all regions are selected with 'all', otherwise filter by selected region
    const filteredData = selectedRegion === "all" ? data : data.filter((item) => item.region === selectedRegion);
    // Transform the filtered data based on your requirements (e.g., specific item prices across regions)
    return transformDataToChartFormat(filteredData, selectedRegion);
  }

  function updateChart(transformedData) {
    if (window.myChart && typeof window.myChart.destroy === "function") {
      window.myChart.destroy();
    }

    const ctx = document.getElementById("myChart").getContext("2d");
    window.myChart = new Chart(ctx, {
      type: "line", // Line chart type
      data: {
        labels: transformedData.labels,
        datasets: transformedData.datasets,
      },
      options: {
        interaction: {
          mode: "index",
          intersect: false,
        },
        maintainAspectRatio: false,
        responsive: true,
        scales: {
          x: {
            type: "time",
            time: {
              unit: "day",
              displayFormats: {
                day: "MMM d",
              },
            },
            title: {
              display: true,
              text: "Date",
              color: "gray", // Set label color to white
            },
            grid: {
              color: "gray", // Set grid color to white
            },
            ticks: {
              color: "gray", // Set label color to white
            },
          },
          y: {
            title: {
              display: true,
              text: "Average Cost (gold)",
              color: "gray", // Set label color to white
            },
            grid: {
              color: "gray", // Set grid color to white
            },
            ticks: {
              color: "gray", // Set label color to white
            },
          },
        },
      },
    });
  }

  function transformDataToChartFormat(data, selectedRegion = "all") {
    const labels = []; // Timestamps for x-axis
    const datasets = []; // Data for each region or item

    data.forEach((region) => {
      if (selectedRegion !== "all" && region.region !== selectedRegion) {
        return; // Skip regions not selected
      }

      region.data.forEach((point) => {
        point.items.forEach((item) => {
          // If region is "all", only add "Fyr'alath the Dreamrender"; otherwise, add all items
          if (selectedRegion === "all" && item.name !== "Fyr'alath the Dreamrender") {
            return;
          }

          const itemLabel = `${item.name} (${region.region})`;
          if (!datasets.some((ds) => ds.label === itemLabel)) {
            datasets.push({
              label: itemLabel,
              data: [],
              borderColor: getRandomColor(),
              fill: false,
            });
          }

          const dataset = datasets.find((ds) => ds.label === itemLabel);
          dataset.data.push({ x: point.timestamp, y: item.price / 10000 }); // Assuming price is in 'cents' and converting to 'gold'

          if (!labels.includes(point.timestamp)) {
            labels.push(point.timestamp);
          }
        });
      });
    });

    // Ensure labels are sorted in chronological order
    labels.sort((a, b) => new Date(a) - new Date(b));
    datasets.forEach((dataset) => {
      dataset.data.sort((a, b) => new Date(a.x) - new Date(b.x));
    });

    return { labels, datasets };
  }

  function getRandomColor() {
    var letters = "0123456789ABCDEF";
    var color = "#";
    for (var i = 0; i < 6; i++) {
      color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
  }
});

// Function to generate color based on region
function getColorByRegion(region) {
  switch (region) {
    case "eu":
      return "green";
    case "us":
      return "blue";
    case "kr":
      return "orange";
    case "tw":
      return "purple";
    default:
      return "black";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  fetch("https://backend.koodattu.dev/api/data/acquisitions")
    .then((response) => response.json())
    .then((data) => {
      createPieCharts(data.summary);
      createLineChart(data.daily, "dailyLineChart");
      createLineChart(data.cumulative, "cumulativeLineChart", true);
      createKillsSummaryBarCharts(data.summary[0]["kills_summary"]);
    });
});

function createPieCharts(summaryData) {
  const chartMappings = {
    "death-knight": document.getElementById("pieChartDeathKnight").getContext("2d"),
    paladin: document.getElementById("pieChartPaladin").getContext("2d"),
    total: document.getElementById("pieChartTotal").getContext("2d"),
    warrior: document.getElementById("pieChartWarrior").getContext("2d"),
  };

  const chartColors = {
    "death-knight": "rgb(196, 30, 58)",
    paladin: "rgb(244, 140, 186)",
    warrior: "rgb(198, 155, 109)",
    total: "rgb(255, 128, 0)",
  };

  const falseColor = "rgba(100, 100, 100, 0.6)";

  // Assuming summaryData is the array containing the summary object
  const summary = summaryData[0]; // Adjusted to access the first object in the array

  Object.keys(summary).forEach((key, index) => {
    if (key !== "kills_summary") {
      // Exclude 'kills_summary' from pie charts
      const item = summary[key];
      let data, backgroundColors, labels;

      if (key === "total") {
        data = [summary["paladin"].true, summary["warrior"].true, summary["death-knight"].true, item.false];
        backgroundColors = [chartColors["paladin"], chartColors["warrior"], chartColors["death-knight"], falseColor];
        labels = ["Paladin", "Warrior", "Death Knight", "Hasn't"];
      } else {
        data = [item.true || 0, item.false || 0];
        backgroundColors = [chartColors[key], falseColor];
        labels = ["Has", "Hasn't"];
      }

      data = data.map((value) => ((value / (item.true + item.false)) * 100).toFixed(2));

      const correctedTitle = key.replace("death-knight", "Death Knight").replace(/\b\w/g, (l) => l.toUpperCase());

      new Chart(chartMappings[key], {
        type: "pie",
        data: {
          labels: labels,
          datasets: [
            {
              label: key,
              data: data,
              backgroundColor: backgroundColors,
              borderColor: ["rgba(0, 0, 0, 0.1)", "rgba(0, 0, 0, 0.1)"],
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "top",
            },
            title: {
              display: true,
              text: correctedTitle,
              color: chartColors[key], // Use dynamic key for title color
            },
            tooltip: {
              callbacks: {
                label: function (context) {
                  let label = context.label || "";
                  if (label) {
                    label += ": ";
                  }
                  if (context.parsed !== null) {
                    label += context.parsed + "%";
                  }
                  return label;
                },
              },
            },
          },
        },
      });
    }
  });
}

function createLineChart(data, chartId, isCumulative = false) {
  // Sort data by date
  data.sort((a, b) => new Date(a.date) - new Date(b.date));
  const labels = data.map((item) => item.date);
  let datasetLabels = ["Total", "Paladin", "Warrior", "Death Knight"];

  const colors = ["rgb(255, 128, 0)", "rgb(244, 140, 186)", "rgb(198, 155, 109)", "rgb(196, 30, 58)"]; // Added a color for totals

  const datasets = datasetLabels.map((label, index) => {
    const key = label.toLowerCase().replace(" ", "-"); // Normalize key to match JSON fields
    const max = label.toLowerCase() === "total" ? 30000 : 10000;
    return {
      label: label,
      data: data.map((item) => (((item[key] || 0) / max) * 100).toFixed(2)),
      borderColor: colors[index],
      fill: false,
      cubicInterpolationMode: "monotone",
      pointStyle: false,
    };
  });

  const ctx = document.getElementById(chartId).getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
      interaction: {
        mode: "index",
        intersect: false,
      },
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: "time",
          time: {
            parser: "yyyy-MM-dd",
            unit: "day",
            tooltipFormat: "MMM d, yyyy",
          },
          title: {
            display: true,
            text: "Date",
            color: "gray", // Set label color to white
          },
          grid: {
            color: "gray", // Set grid color to white
          },
          ticks: {
            color: "gray", // Set label color to white
          },
        },
        y: {
          beginAtZero: true,
          max: isCumulative ? 100 : 3.5, // Set max value to 100 for cumulative, 30 for daily
          title: {
            display: true,
            text: isCumulative ? "Cumulative Acquisitions" : "Daily Acquisitions",
            color: "gray", // Set label color to white
          },
          grid: {
            color: "gray", // Set grid color to white
          },
          ticks: {
            color: "gray", // Set label color to white
            callback: function (value) {
              return value + "%";
            },
          },
        },
      },
    },
  });
}

function createKillsSummaryBarCharts(killsSummary) {
  const chartIds = {
    chars_with_weapon_hc: "barChartCharsWithWeaponHC",
    chars_with_weapon_m: "barChartCharsWithWeaponM",
    chars_without_weapon_hc: "barChartCharsWithoutWeaponHC",
    chars_without_weapon_m: "barChartCharsWithoutWeaponM",
  };

  Object.keys(killsSummary).forEach((category) => {
    const canvasContext = document.getElementById(chartIds[category]).getContext("2d");
    const data = Object.keys(killsSummary[category]).map((key) => ({
      x: key,
      y: killsSummary[category][key],
    }));

    new Chart(canvasContext, {
      type: "bar",
      data: {
        datasets: [
          {
            label: category.replace(/_/g, " ").replace(/hc|m/g, (match) => match.toUpperCase()) + " Fyrakk kills",
            data: data,
            backgroundColor: "rgba(54, 162, 235, 0.2)",
            borderColor: "rgba(54, 162, 235, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        interaction: {
          mode: "index",
          intersect: false,
        },
        scales: {
          x: {
            type: "category",
            labels: Object.keys(killsSummary[category]),
          },
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  });
}

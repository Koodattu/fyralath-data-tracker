document.addEventListener("DOMContentLoaded", () => {
  // Fetch the JSON data
  fetch("https://backend.koodattu.dev/api/data/history")
    .then((response) => response.json())
    .then((data) => {
      // Initialize arrays to hold labels (dates) and datasets (region prices)
      let labels = [];
      let datasets = [];

      // Iterate over each region
      data.forEach((region) => {
        // Extract region name and initialize an array to hold data points
        const regionName = region.region;
        const regionData = [];

        // Iterate over each data point in the region
        region.data.forEach((dataPoint) => {
          // Push date and average cost to the region data array
          regionData.push({
            x: new Date(dataPoint.date), // Parse date string into Date object
            y: dataPoint.average_cost / 10000,
          });

          // Add the date to labels array if not already present
          if (!labels.includes(dataPoint.date)) {
            labels.push(dataPoint.date);
          }
        });

        // Push the dataset for this region to datasets array
        datasets.push({
          label: regionName,
          data: regionData,
          borderColor: getColorByRegion(regionName), // Function to generate random color
          fill: false,
        });
      });

      // Sort labels array in ascending order
      labels.sort();

      // Create Chart.js line chart
      const ctx = document.getElementById("myChart").getContext("2d");
      new Chart(ctx, {
        type: "line",
        data: {
          labels: labels,
          datasets: datasets,
        },
        options: {
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
    });
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

// acquisition charts

document.addEventListener("DOMContentLoaded", () => {
  fetch("https://backend.koodattu.dev/api/data/acquisitions")
    .then((response) => response.json())
    .then((data) => {
      createPieCharts(data.summary);
      createLineChart(data.daily, "dailyLineChart");
      createLineChart(data.cumulative, "cumulativeLineChart", true); // Note the added parameter for cumulative data handling
    });
});

function createPieCharts(summaryData) {
  const contexts = [
    document.getElementById("pieChartDeathKnight").getContext("2d"),
    document.getElementById("pieChartPaladin").getContext("2d"),
    document.getElementById("pieChartWarrior").getContext("2d"),
    document.getElementById("pieChartTotal").getContext("2d"),
  ];

  // Define colors for each chart type
  const chartColors = {
    "death-knight": "rgb(196, 30, 58)", // Color for Death Knight
    paladin: "rgb(244, 140, 186)", // Color for Paladin
    warrior: "rgb(198, 155, 109)", // Color for Warrior
  };

  const falseColor = "rgba(100, 100, 100, 0.6)"; // Consistent color for "false" portion

  summaryData.forEach((item, index) => {
    let data, backgroundColors, labels;

    if (item.date === "total") {
      // Special handling for the "Total" chart
      data = [summaryData[1].true, summaryData[2].true, summaryData[0].true, item.false]; // Death Knight, Paladin, Warrior true counts, and false part from total
      backgroundColors = [chartColors["paladin"], chartColors["warrior"], chartColors["death-knight"], falseColor];
      labels = ["Paladin", "Warrior", "Death Knight", "Hasn't"];
    } else {
      data = [item.true || 0, item.false || 0];
      backgroundColors = [chartColors[item.date], falseColor];
      labels = ["Has", "Hasn't"];
    }

    const correctedTitle = item.date.replace("death-knight", "Death Knight").replace(/\b\w/g, (l) => l.toUpperCase()); // Correct title

    new Chart(contexts[index], {
      type: "pie",
      data: {
        labels: labels,
        datasets: [
          {
            label: item.date,
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
          },
        },
      },
    });
  });
}

function createPieCharts2(summaryData) {
  const contexts = [
    document.getElementById("pieChartDeathKnight").getContext("2d"),
    document.getElementById("pieChartPaladin").getContext("2d"),
    document.getElementById("pieChartWarrior").getContext("2d"),
    document.getElementById("pieChartTotal").getContext("2d"),
  ];

  // Define colors for each chart type
  const chartColors = {
    "death-knight": "rgb(196, 30, 58)", // Color for Death Knight
    paladin: "rgb(244, 140, 186)", // Color for Paladin
    warrior: "rgb(198, 155, 109)", // Color for Warrior
    total: "rgb(255, 128, 0)", // Color for Total
  };

  const falseColor = "rgba(100, 100, 100, 0.6)"; // Consistent color for "false" portion

  summaryData.forEach((item, index) => {
    const trueColor = chartColors[item.date]; // Get the color based on the chart type
    const correctedTitle = item.date.replace("death-knight", "Death Knight").replace(/\b\w/g, (l) => l.toUpperCase()); // Correct title

    new Chart(contexts[index], {
      type: "pie",
      data: {
        labels: ["Has", "Hasn't"],
        datasets: [
          {
            label: item.date,
            data: [item.true || 0, item.false || 0],
            backgroundColor: [trueColor, falseColor],
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
            color: trueColor, // This line might also need adjustment based on version
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const label = context.label || "";
                const value = context.parsed;
                const total = context.dataset.data.reduce((acc, value) => acc + value, 0);
                const percentage = ((value / total) * 100).toFixed(2) + "%";
                return `${label}: ${percentage}`;
              },
            },
          },
        },
      },
    });
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
    return {
      label: label,
      data: data.map((item) => item[key] || 0),
      borderColor: colors[index],
      fill: false,
    };
  });

  const ctx = document.getElementById(chartId).getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: { labels, datasets },
    options: {
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
          title: {
            display: true,
            text: isCumulative ? "Cumulative Count" : "Daily Count",
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

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

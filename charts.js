document.addEventListener("DOMContentLoaded", () => {
  // Fetch the JSON data
  fetch("python-backend/aggregated_data/daily_averages.json")
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
            y: dataPoint.average_cost / 1000,
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
          borderColor: getRandomColor(), // Function to generate random color
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
              },
            },
            y: {
              title: {
                display: true,
                text: "Average Cost (gold)",
              },
            },
          },
        },
      });
    });
});

// Function to generate random color
function getRandomColor() {
  const letters = "0123456789ABCDEF";
  let color = "#";
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

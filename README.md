<div align="center">
    <br />
    <img src="https://i.imgur.com/kOhczFq.png" alt="Logo" width="80" height="80">

  <h3 align="center"><a href="https://fyralath.koodattu.dev">Fyr'alath Data Tracker</a></h3>
  <h4 align="center">World of Warcraft legendary axe Fyr'alath price tracking and acquisition data analysis</h4>
    <br />
    <br />
</div>

## Description

The goal of this project is to create a website which displays World of Warcraft Fyr'alath legendary axe price and acquisition data. 
The main two main features are to display how much the legendary axe costs to craft and how many people have acquired it. 
For first feature the current total price-to-craft and individual item prices are shown with a graph which displays total craft price history, both for all regions.  
The second feature is to approximate how many people have acquired the legendary and when, with graphs and charts for when characters have acquired the axe with data for total and per class.

## Features

- Shows current price craft legendary weapon per region and individual material prices
- Shows price history of total price to craft per region
- Shows acquisition data, daily and cumulative and per class

## Tech

Currently the backend is a python flask server which is hosted in a digitalocean droplet, which runs the data acquisition scripts hourly for auction house data and weekly for acquisition data. The website is hosted in github pages in this repository and the charts are drawn using [Chart.js](https://www.chartjs.org/). The auction house data is fetched from Blizzard's [game data api](https://develop.battle.net/documentation/world-of-warcraft/game-data-apis). Acquisition data is from using [raider.io api](https://raider.io/api) to find character's wielding the legendary and Blizzard's achivements api endpoint for the acquisition dates. 

- Platform: Web, Server
- Languages: Python, JavaScript
- Frontend: HTML, CSS
- Backend: Flask, MongoDB
- Tools: Visual Studio Code

## Version History

- 0.0.1
    - Working on first version

## Authors

Juha Ala-Rantala ([Koodattu](https://github.com/Koodattu/))

## Acknowledgments

* [Chart.js](https://www.chartjs.org/)
* [Raider.io](https://raider.io/)
* [Blizzard](https://develop.battle.net/)

## License

Distributed under the MIT License. See `LICENSE` file for more information.

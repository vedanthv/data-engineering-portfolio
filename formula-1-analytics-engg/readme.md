## Formula 1 Race Analytics with Databricks and Azure

Formula 1, often abbreviated as F1, is one of the most prestigious and popular forms of motorsport in the world. It's a high-octane racing series that blends cutting-edge technology, exceptional driving skill, and global glamour into an exhilarating sporting spectacle.

![charles-leclerc-ferrari-sf-23-](https://github.com/vedanthv/data-engineering-projects/assets/44313631/4e8c3e14-0652-4ebc-b418-3e906526c6e4)

## A Brief Introduction to Formula 1

**Cars**: Formula 1 cars are cutting-edge, single-seat racing machines with advanced aerodynamics and powerful engines. They are designed for maximum speed and agility.

**Races**: F1 races take place on a variety of tracks, including purpose-built circuits and temporary street circuits in cities around the world.

**Teams**: Multiple teams, each with two drivers, compete in the championship. Prominent teams include Mercedes, Ferrari, Red Bull Racing, and McLaren.

**Drivers**: F1 attracts some of the world's best racing talents, and drivers like Lewis Hamilton, Sebastian Vettel, and Max Verstappen have become household names.

**Points and Championships**: Drivers and teams earn points based on their performance in each race. At the end of the season, the driver with the most points wins the Drivers' Championship, and the team with the most points wins the Constructors' Championship.

## How does the Formula 1 Season Work

A Formula 1 championship season refers to a specific year in which a series of Formula 1 races are held, and points are accumulated by drivers and teams to determine the champions in various categories. Here's an explanation of how a Formula 1 championship season works:

**Race Calendar**: Each Formula 1 season typically consists of a calendar of races, known as Grand Prix events. These races are held at various locations around the world, ranging from traditional circuits to temporary street tracks.

**Teams and Drivers**: Multiple teams participate in the championship, with each team fielding two drivers. These drivers compete throughout the season to earn points for themselves and their teams.

**Points System**: Formula 1 uses a points system to determine the championship standings. The points are awarded to drivers based on their finishing positions in each race. The points system can vary slightly over the years, but a common system is to award points to the top 10 finishers, with the winner earning the most points (e.g., 25 points) and the 10th-place finisher earning the fewest (e.g., 1 point).

**Drivers' Championship**: The primary focus of a Formula 1 season is the Drivers' Championship. Drivers accumulate points from each race throughout the season. The driver with the most points at the end of the season is crowned the Drivers' Champion and often receives the prestigious "World Champion" title.

**Constructors' Championship**: In addition to the Drivers' Championship, there is also a Constructors' Championship. This championship considers the combined points earned by both drivers of each team. The team with the most points at the end of the season wins the Constructors' Championship.

## Project Requirements

### Data Ingestion 

- Extract Data from the Ergast API.

- Ingested Data must have the correct schema applied.

- Ingested Data must have the audit columns.

- Ingested data must be in the Parquet Format.

- Analyse the ingested data via SQL

- Ingested Data must be able to handle incremental load.

### Data Transformation

- Join key information required to report anything.

- Transformed Data must be stored in column format.

### Analysis Requirements

- Dominant Drivers

- Dominant Teams

- Create Databricks Dashboards

### Scheduling Requirements

- Schedule to run at 10pm every Friday

- Ability to monitor pipelines.

- Rerun failed pipelines.

- Set up Alerts on Failures.

## Solution Architecture

<img src = "https://github.com/vedanthv/data-engineering-projects/blob/main/formula-1-analytics-engg/static/formula1-solution-architecture.png">


### Visualizations

#### Dominant Drivers

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/aef0dacf-3cd8-494d-b1d7-e2249a5f7652)

### Dominant Teams

![image](https://github.com/vedanthv/data-engineering-portfolio/assets/44313631/3995a206-950d-470b-a525-8f1845ed7cca)

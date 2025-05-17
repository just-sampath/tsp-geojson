# 🗺️ Travelling Salesman City-Tour Optimizer

This project implements a solution to the Travelling Salesman Problem (TSP) 
for a list of geographical locations, providing an optimized tour that visits 
each location once.

## Features

- **CSV Input**: Reads locations (Name, Latitude, Longitude) from a CSV file.
- **Distance Calculation**: Uses the Haversine formula to calculate distances between locations.
- **TSP Solvers**:
    - Greedy heuristic.
    - 2-opt improvement heuristic.
    - Simulated Annealing heuristic.
- **Modular Design**: Code is structured into reusable modules (`distance.py`, `tsp_solver.py`).
- **GeoJSON Output**: Exports the calculated tour as a GeoJSON `LineString` file, which can be visualized on mapping platforms like Google Maps or geojson.io.
- **Command-Line Interface**: Easy-to-use CLI for specifying input, starting location, and other options.
- **Matplotlib Plotting**: Optional tour visualization using Matplotlib.
- **Basic Time Window Support**: Optional enforcement of time windows for the greedy algorithm.

## File Structure

```
.
├── tsp.py             # Main CLI script
├── distance.py        # Module for Place data structure and Haversine distance calculations
├── tsp_solver.py      # Module for TSP algorithms (Greedy, 2-Opt)
├── places.csv         # Sample input file (or your own)
├── route.geojson      # Default output file for the tour
├── requirements.txt   # Python dependencies (currently none beyond standard library)
└── README.md          # This file
```

## Prerequisites

- Python 3.7+
- Matplotlib (for plotting): `pip install matplotlib`
- Seaborn (for enhanced plot aesthetics, optional): `pip install seaborn`

No external libraries are strictly required for the core functionality if plotting is not used.

## Setup

1.  **Clone the repository (if applicable) or download the files.**
2.  **Prepare your input CSV file.**
    Create a CSV file (e.g., `places.csv`) with the following columns: `Name`, `Lat`, `Lon`.
    Optionally, you can include `Open` and `Close` columns for time window support (values should be hours from midnight, e.g., 9.5 for 9:30 AM).

    *Example `places.csv` content with time windows:*
    ```csv
    Name,Lat,Lon,Open,Close
    Eiffel Tower,48.8584,2.2945,9.0,23.0
    Louvre Museum,48.8606,2.3376,9.0,18.0
    Notre-Dame Cathedral,48.8530,2.3499,8.0,17.5
    Arc de Triomphe,48.8738,2.2950,, 
    Sacré-Cœur Basilica,48.8867,2.3431,7.0,
    ```
    (Empty values for Open/Close mean no restriction for that side of the window)

## Usage

Run the main script `tsp.py` from your terminal.

When run with multiple locations in the CSV, the script will first list the available places and then **interactively prompt you to select a starting place** by its name or number.

### Command-Line Arguments

-   `--csv FILE_PATH`: Optional. Path to the CSV file containing places (e.g., `places.csv`). **Defaults to `places.csv` in the same directory as the script.**
-   `--return`: Optional. If specified, the tour will return to the starting place, forming a closed loop. Otherwise, it calculates an open path.
-   `--algo {greedy|2opt|simulated-annealing}`: Optional. TSP algorithm to use. Defaults to `2opt`. 
    -   `greedy`: Uses a simple nearest neighbor heuristic. Can consider time windows if `--enforce-time-windows` is used.
    -   `2opt`: Uses the 2-opt heuristic to improve an initial greedy solution.
    -   `simulated-annealing`: Uses a simulated annealing heuristic.
-   `--output FILE_PATH`: Optional. Path to save the GeoJSON route. Defaults to `route.geojson`. If the file already exists and is a valid GeoJSON FeatureCollection, the new route is added; otherwise, the file is created/overwritten.
-   `--plot`: Optional. Generate a scatter plot of the tour and save it (default: `tour_plot.png`). Requires Matplotlib.
-   `--plot-output FILE_PATH`: Optional. Filename for the output plot if `--plot` is used. Defaults to `tour_plot.png`.
-   `--speed KMPH`: Optional. Average travel speed in km/h for time window calculations. Default: 40.0 km/h. Used only if `--enforce-time-windows` is specified.
-   `--enforce-time-windows`: Optional. If specified, time windows from the CSV (Open, Close columns) will be considered. 
    **Currently, only the `greedy` algorithm respects these time windows.** 
    If used with `2opt` or `simulated-annealing`, a warning is issued as these algorithms are not yet fully time-window aware and might produce routes violating these constraints.

### Examples

1.  **Calculate an optimal tour using Simulated Annealing, returning to start, and plot it. The script will prompt for the starting city from `places.csv`:**

    ```bash
    python tsp.py --return --algo simulated-annealing --plot
    ```

2.  **Calculate an open path using the greedy algorithm, enforcing time windows from `my_cities_tw.csv` (assuming it has Open/Close columns) with an average speed of 30 km/h:**

    ```bash
    python tsp.py --csv my_cities_tw.csv --algo greedy --enforce-time-windows --speed 30
    ```

3.  **Specify a different output file for the GeoJSON and the plot:**

    ```bash
    python tsp.py --csv places.csv --return --output optimized_tour.geojson --plot --plot-output my_route_viz.png
    ```

### Output

The script will:
1.  If multiple places are loaded, prompt you to select a starting place.
2.  Print the ordered list of places in the tour to the console, along with the total distance in kilometers.
3.  Generate or update a GeoJSON file (e.g., `route.geojson`). If the file existed and was a valid GeoJSON FeatureCollection, the new route is added as a new feature. Otherwise, a new file is created. Each feature in the GeoJSON will have properties including `calculated_at`, `point_count`, `start_place`, and `end_place`. You can drag and drop this file into tools like [geojson.io](http://geojson.io/) or import it into Google My Maps to visualize the route(s).

*Example Console Interaction & Output:*
```
Available places:
  1) Eiffel Tower
  2) Louvre Museum
  3) Notre-Dame Cathedral
  4) Arc de Triomphe
  5) Sacré-Cœur Basilica
Enter the name or number of the starting place (e.g., 'Eiffel Tower' or 1, default: Eiffel Tower): Eiffel Tower
Selected starting place: Eiffel Tower
------------------------------
Calculating route using '2opt' algorithm, starting from 'Eiffel Tower'...
The tour will return to the starting place.
Initial greedy path distance: 20.74 km. Improving with 2-opt...

------------------------------
Optimal tour:
1) Eiffel Tower
2) Arc de Triomphe
3) Louvre Museum
4) Sacré-Cœur Basilica
5) Notre-Dame Cathedral
6) Eiffel Tower
Total distance: 19.34 km
Loaded 0 existing features from 'route.geojson'.
Route data appended to or created in route.geojson
```

## Further Development (Extra Points from Prompt)

-   **Simulated Annealing**: Implemented.
-   **Matplotlib Plot**: Implemented.
-   **Time Window Filtering**: Basic implementation for greedy solver added. Full support for 2-opt and SA with time windows is a more complex task involving significant changes to their core logic to ensure all generated neighbor solutions are time-window valid.

## How to Create `places.csv`

1.  Open a plain text editor (like Notepad, VS Code, Sublime Text, etc.).
2.  On the first line, enter the headers. Minimum: `Name,Lat,Lon`. For time windows, add `Open,Close`.
    *Example with time windows:*
    ```csv
    Name,Lat,Lon,Open,Close
    Eiffel Tower,48.8584,2.2945,9,23
    Louvre Museum,48.8606,2.3376,9,18
    "Notre-Dame Cathedral, Paris",48.8530,2.3499,8,17.5 
    Arc de Triomphe,48.8738,2.2950,,
    Some Late Night Spot,48.8500,2.3500,18,2  # Open 6 PM to 2 AM (next day) - Note: current simple implementation might not handle overnight windows perfectly without adjustments.
    ```
    (Note: The current CSV reader in `tsp.py` is basic. For names with commas, you might need a more robust CSV parsing or ensure your names don't contain commas if not quoted. For time windows, provide hours from midnight. Empty values for Open/Close indicate no restriction on that side. The current simple time window logic in greedy might not perfectly handle overnight windows e.g. Close time < Open time without further refinement in how current_time and comparison are handled across midnight.)
4.  Save the file as `places.csv` (or any other `.csv` name) in the same directory as `tsp.py` or provide the correct path when running the script. 
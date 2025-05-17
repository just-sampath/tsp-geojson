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
- **Modular Design**: Code is structured into reusable modules (`distance.py`, `tsp_solver.py`).
- **GeoJSON Output**: Exports the calculated tour as a GeoJSON `LineString` file, which can be visualized on mapping platforms like Google Maps or geojson.io.
- **Command-Line Interface**: Easy-to-use CLI for specifying input, starting location, and other options.

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

No external libraries are strictly required for the core functionality as the Haversine formula is implemented manually. If you wish to use a dedicated `haversine` library, you can install it (`pip install haversine`) and modify `distance.py` accordingly, then add `haversine` to `requirements.txt`.

## Setup

1.  **Clone the repository (if applicable) or download the files.**
2.  **Prepare your input CSV file.**
    Create a CSV file (e.g., `places.csv`) with the following columns: `Name`, `Lat`, `Lon`.

    *Example `places.csv` content:*
    ```csv
    Name,Lat,Lon
    Eiffel Tower,48.8584,2.2945
    Louvre Museum,48.8606,2.3376
    Notre-Dame Cathedral,48.8530,2.3499
    Arc de Triomphe,48.8738,2.2950
    Sacré-Cœur Basilica,48.8867,2.3431
    ```

## Usage

Run the main script `tsp.py` from your terminal.

When run with multiple locations in the CSV, the script will first list the available places and then **interactively prompt you to select a starting place** by its name or number.

### Command-Line Arguments

-   `--csv FILE_PATH`: Optional. Path to the CSV file containing places (e.g., `places.csv`). **Defaults to `places.csv` in the same directory as the script.**
-   `--return`: Optional. If specified, the tour will return to the starting place, forming a closed loop. Otherwise, it calculates an open path.
-   `--algo {greedy|2opt}`: Optional. TSP algorithm to use. Defaults to `2opt`. 
    -   `greedy`: Uses a simple nearest neighbor heuristic.
    -   `2opt`: Uses the 2-opt heuristic to improve an initial greedy solution. This generally provides better results than plain greedy but takes longer.
-   `--output FILE_PATH`: Optional. Path to save the GeoJSON route. Defaults to `route.geojson`. **If the file already exists and is a valid GeoJSON FeatureCollection, the new route will be added as an additional feature; otherwise, the file is created or overwritten.**

### Examples

1.  **Calculate an optimal tour returning to the start, using 2-opt (default). The script will prompt for the starting city from `places.csv` (default input):**

    ```bash
    python tsp.py --return
    ```

2.  **Calculate an optimal open path using the greedy algorithm from `my_cities.csv`. The script will prompt for the starting city:**

    ```bash
    python tsp.py --csv my_cities.csv --algo greedy
    ```

3.  **Specify a different output file. The script will prompt for the starting city from `places.csv`:**

    ```bash
    python tsp.py --csv places.csv --return --output optimized_tour.geojson
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

-   **Simulated Annealing**: Implement `simulated-annealing` as an option for `--algo`.
-   **Matplotlib Plot**: Add a command-line flag (e.g., `--plot`) to generate a Matplotlib scatter plot of the cities with arrows indicating the tour path.
-   **Time Window Filtering**: Add functionality to consider time windows for visiting places (this would significantly increase complexity).

## How to Create `places.csv`

1.  Open a plain text editor (like Notepad, VS Code, Sublime Text, etc.).
2.  On the first line, enter the headers: `Name,Lat,Lon`
3.  On subsequent lines, add your places, one per line, with values separated by commas. Ensure names with commas are enclosed in double quotes if your CSV parser expects it, though the current script handles simple names well.
    *Example:*
    ```csv
    Name,Lat,Lon
    Eiffel Tower,48.8584,2.2945
    Louvre Museum,48.8606,2.3376
    "Notre-Dame Cathedral, Paris",48.8530,2.3499 
    ```
    (Note: The current CSV reader in `tsp.py` is basic. For names with commas, you might need a more robust CSV parsing or ensure your names don't contain commas if not quoted).
4.  Save the file as `places.csv` (or any other `.csv` name) in the same directory as `tsp.py` or provide the correct path when running the script. 
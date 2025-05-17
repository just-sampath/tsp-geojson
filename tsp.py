import argparse
import csv
import json
import sys
import os
import datetime

# Try to import matplotlib, but don't make it a hard requirement if --plot is not used.
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
    try:
        import seaborn as sns
        SEABORN_AVAILABLE = True
    except ImportError:
        SEABORN_AVAILABLE = False
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    SEABORN_AVAILABLE = False

from distance import Place, calculate_distance_matrix
from tsp_solver import solve_tsp_greedy, solve_tsp_2opt, solve_tsp_simulated_annealing

DEFAULT_INPUT_CSV = "places.csv"
DEFAULT_OUTPUT_GEOJSON = "route.geojson"
DEFAULT_PLOT_FILENAME = "tour_plot.png"

def read_places_from_csv(csv_filepath: str) -> list[Place]:
    places = []
    try:
        with open(csv_filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            # Expected columns: Name, Lat, Lon. Optional: Open, Close
            required_cols = ['Name', 'Lat', 'Lon']
            if not reader.fieldnames or not all(f in reader.fieldnames for f in required_cols):
                 raise ValueError(f"CSV file '{csv_filepath}' must have at least 'Name', 'Lat', 'Lon' columns.")
            
            has_open_time = "Open" in reader.fieldnames
            has_close_time = "Close" in reader.fieldnames

            for row_num, row in enumerate(reader, 1):
                try:
                    name = row['Name'].strip()
                    lat = float(row['Lat'])
                    lon = float(row['Lon'])
                    if not name:
                        raise ValueError(f"Place name cannot be empty (row {row_num} in '{csv_filepath}').")
                    
                    open_time_val = None
                    if has_open_time and row["Open"] and row["Open"].strip():
                        try:
                            open_time_val = float(row["Open"])
                        except ValueError:
                            raise ValueError(f"Invalid format for 'Open' time (row {row_num}): '{row['Open']}'. Must be a number (hours).")

                    close_time_val = None
                    if has_close_time and row["Close"] and row["Close"].strip():
                        try:
                            close_time_val = float(row["Close"])
                        except ValueError:
                            raise ValueError(f"Invalid format for 'Close' time (row {row_num}): '{row['Close']}'. Must be a number (hours).")

                    if open_time_val is not None and close_time_val is not None and open_time_val >= close_time_val:
                        raise ValueError(f"'Open' time ({open_time_val}) must be before 'Close' time ({close_time_val}) (row {row_num}).")

                    places.append(Place(name, lat, lon, open_time_val, close_time_val))
                except ValueError as e:
                    if f"(row {row_num})" not in str(e):
                         raise ValueError(f"Error parsing row {row_num} in CSV '{csv_filepath}': {row}. Details: {e}")
                    else:
                        raise
                except KeyError as e:
                    raise ValueError(f"Missing column {e} in CSV row {row_num} in '{csv_filepath}'.")
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: CSV file not found at '{csv_filepath}'")
    except Exception as e:
        raise RuntimeError(f"Could not read CSV file '{csv_filepath}': {e}")
    
    if not places:
        raise ValueError(f"No places found in CSV file '{csv_filepath}'. The file might be empty or incorrectly formatted.")
    return places

def write_route_to_geojson(route_places: list[Place], output_filepath: str) -> None:
    """Writes the tour route to a GeoJSON file, updating if exists."""
    coordinates = [[place.lon, place.lat] for place in route_places]
    
    new_feature = {
        "type": "Feature",
        "properties": {
            "calculated_at": datetime.datetime.now().isoformat(),
            "point_count": len(route_places),
            "start_place": route_places[0].name if route_places else "N/A",
            "end_place": route_places[-1].name if route_places else "N/A"
        },
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates
        }
    }

    if not coordinates:
        print("Warning: No coordinates to write to GeoJSON. Attempting to write an empty feature.", file=sys.stderr)
        new_feature["geometry"]["coordinates"] = []


    geojson_data = {
        "type": "FeatureCollection",
        "features": []
    }

    if os.path.exists(output_filepath):
        try:
            with open(output_filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, dict) and \
                   existing_data.get("type") == "FeatureCollection" and \
                   isinstance(existing_data.get("features"), list):
                    geojson_data["features"] = existing_data["features"]
                    print(f"Loaded {len(geojson_data['features'])} existing features from '{output_filepath}'.")
                else:
                    print(f"Warning: Existing file '{output_filepath}' is not a valid GeoJSON FeatureCollection. It will be overwritten.", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"Warning: Existing file '{output_filepath}' is not valid JSON. It will be overwritten.", file=sys.stderr)
        except IOError as e:
            print(f"Warning: Could not read existing file '{output_filepath}' ({e}). It may be overwritten.", file=sys.stderr)

    if not coordinates and not geojson_data["features"]:
         print(f"No route data to write to '{output_filepath}'. File will not be created/updated if empty.", file=sys.stderr)
         pass


    if coordinates:
        geojson_data["features"].append(new_feature)
    elif not geojson_data["features"]:
         print(f"No route data to write to '{output_filepath}'. File will not be created.", file=sys.stderr)
         return


    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, indent=2)
    except IOError as e:
        print(f"Error writing GeoJSON to '{output_filepath}': {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred while writing GeoJSON: {e}", file=sys.stderr)

def plot_tour(places_in_tour: list[Place], output_plot_filepath: str):
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib is not installed. Skipping plot generation. Please install it with: pip install matplotlib", file=sys.stderr)
        return

    if SEABORN_AVAILABLE:
        sns.set_theme(style="whitegrid", palette="pastel")
    else:
        print("Seaborn not found. Using default Matplotlib styling. For enhanced visuals, install Seaborn: pip install seaborn", file=sys.stderr)

    if not places_in_tour:
        print("No places in the tour to plot.", file=sys.stderr)
        return

    lats = [p.lat for p in places_in_tour]
    lons = [p.lon for p in places_in_tour]
    names = [p.name for p in places_in_tour]

    plt.figure(figsize=(10, 8))
    
    annotation_offset = 0.0003

    unique_lons = [p.lon for p in dict.fromkeys(places_in_tour)]
    unique_lats = [p.lat for p in dict.fromkeys(places_in_tour)]
    plt.scatter(unique_lons, unique_lats, c='blue', label='Cities', zorder=2)

    for i, p_tour in enumerate(places_in_tour):
        plt.text(p_tour.lon + annotation_offset, 
                 p_tour.lat + annotation_offset, 
                 f"{i+1}. {p_tour.name}", 
                 fontsize=9, zorder=4)

    if len(places_in_tour) > 1:
        for i in range(len(places_in_tour) - 1):
            p1 = places_in_tour[i]
            p2 = places_in_tour[i+1]
            if p1.lat == p2.lat and p1.lon == p2.lon:
                continue
            plt.arrow(p1.lon, p1.lat, p2.lon - p1.lon, p2.lat - p1.lat,
                      width=0.00010,
                      head_width=0.0004,
                      head_length=0.0007,
                      fc='dimgray', ec='dimgray', 
                      length_includes_head=True, 
                      zorder=1)
    
    if places_in_tour:
        plt.scatter([lons[0]], [lats[0]], 
                    c='green', s=120, label='Start Point', 
                    marker='*', zorder=3, edgecolors='black')

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title("Tour Route")
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    plt.tight_layout()
    
    try:
        plt.savefig(output_plot_filepath)
        print(f"Tour plot saved to {output_plot_filepath}")
    except Exception as e:
        print(f"Error saving plot to '{output_plot_filepath}': {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Travelling Salesman City-Tour Optimizer. Interactively prompts for start city if not a single city.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--csv", 
        type=str, 
        default=DEFAULT_INPUT_CSV,
        help=f"Path to the CSV file containing places (Name,Lat,Lon).\nDefault: '{DEFAULT_INPUT_CSV}'"
    )
    parser.add_argument(
        "--return", 
        action="store_true", 
        dest="must_return_to_start",
        help="If specified, the tour will return to the starting place."
    )
    parser.add_argument(
        "--algo",
        type=str,
        choices=["greedy", "2opt", "simulated-annealing"],
        default="2opt",
        help="TSP algorithm to use: 'greedy', '2opt', or 'simulated-annealing'.\nDefault: '2opt'."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_GEOJSON,
        help=f"Path to save the GeoJSON route. If file exists, new routes are added.\\nDefault: '{DEFAULT_OUTPUT_GEOJSON}'."
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help=f"Generate a scatter plot of the tour and save it to '{DEFAULT_PLOT_FILENAME}'. Requires Matplotlib."
    )
    parser.add_argument(
        "--plot-output",
        type=str,
        default=DEFAULT_PLOT_FILENAME,
        help=f"Filename for the output plot. Default: '{DEFAULT_PLOT_FILENAME}'."
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=40.0,
        help="Average travel speed in km/h for time window calculations. Default: 40.0 km/h."
    )
    parser.add_argument(
        "--enforce-time-windows",
        action="store_true",
        help="Enforce time windows specified in the CSV (Open, Close columns). \\nCurrently only respected by the 'greedy' algorithm. \\nOther algorithms will ignore time windows but a warning will be issued."
    )

    args = parser.parse_args()

    if args.plot and not MATPLOTLIB_AVAILABLE:
        print("Error: --plot was specified, but Matplotlib is not installed. Please install it: pip install matplotlib", file=sys.stderr)
        sys.exit(1)

    try:
        places = read_places_from_csv(args.csv)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not places:
        print("No places loaded. Exiting.", file=sys.stderr)
        sys.exit(1)

    start_node_idx = 0

    if len(places) > 1:
        print("\nAvailable places:")
        for i, p in enumerate(places):
            print(f"  {i+1}) {p.name}")
        
        while True:
            try:
                raw_input_str = input(f"Enter the name or number of the starting place (e.g., '{places[0].name}' or 1, default: {places[0].name}): ").strip()
                if not raw_input_str:
                    start_node_idx = 0
                    print(f"Starting at default: {places[start_node_idx].name}")
                    break
                
                try:
                    choice_idx = int(raw_input_str) - 1 
                    if 0 <= choice_idx < len(places):
                        start_node_idx = choice_idx
                        print(f"Selected starting place: {places[start_node_idx].name}")
                        break
                    else:
                        print(f"Invalid number. Please choose a number between 1 and {len(places)}.")
                except ValueError:
                    found_match = False
                    for i, p in enumerate(places):
                        if p.name.lower() == raw_input_str.lower():
                            start_node_idx = i
                            print(f"Selected starting place: {places[start_node_idx].name}")
                            found_match = True
                            break
                    if found_match:
                        break
                    else:
                        print(f"Place name '{raw_input_str}' not found. Please enter a valid name or number from the list.")
            except EOFError:
                print("\nNo input received. Exiting.", file=sys.stderr)
                sys.exit(1)
            except KeyboardInterrupt:
                print("\nOperation cancelled by user. Exiting.", file=sys.stderr)
                sys.exit(1)
        print("-" * 30)
    elif places:
        print(f"Only one place loaded: {places[0].name}. This will be the start and end point.")
        start_node_idx = 0
    
    if len(places) == 1:
        print("\nOnly one place provided.")
        place_obj = places[0]
        ordered_places_objects = [place_obj]
        total_distance = 0.0
        
        if args.must_return_to_start:
            ordered_places_objects.append(place_obj)
            print("Tour (returning to start):")
            print(f"1) {place_obj.name}")
            print(f"2) {place_obj.name}")
        else:
            print("Path:")
            print(f"1) {place_obj.name}")
            
        print(f"Total distance: {total_distance:.2f} km")
        write_route_to_geojson(ordered_places_objects, args.output)
        print(f"Route data written to {args.output}")
        if args.plot:
            plot_tour(ordered_places_objects, args.plot_output)
        sys.exit(0)

    dist_matrix = calculate_distance_matrix(places)

    optimal_path_indices = []
    total_distance = 0.0

    print(f"Calculating route using '{args.algo}' algorithm, starting from '{places[start_node_idx].name}'...")
    if args.must_return_to_start:
        print("The tour will return to the starting place.")
    else:
        print("The path will be open (not returning to start).")

    travel_time_matrix = None
    if args.enforce_time_windows:
        if args.speed <= 0:
            print("Error: --speed must be positive if --enforce-time-windows is used.", file=sys.stderr)
            sys.exit(1)
        travel_time_matrix = [[(dist / args.speed if args.speed > 0 else float('inf')) for dist in row] for row in dist_matrix]
        print(f"Time windows will be enforced using an average speed of {args.speed} km/h.")
        if args.algo != "greedy":
            print(f"Warning: Time windows are enforced, but algorithm '{args.algo}' is not fully time-window aware. Resulting path may violate time constraints.", file=sys.stderr)


    if args.algo == "greedy":
        optimal_path_indices, total_distance = solve_tsp_greedy(
            dist_matrix, 
            start_node_idx, 
            args.must_return_to_start,
            places=places if args.enforce_time_windows else None, # Pass places for time windows
            travel_time_matrix=travel_time_matrix if args.enforce_time_windows else None # Pass time matrix
        )
    elif args.algo == "2opt":
        initial_greedy_path, initial_greedy_distance = solve_tsp_greedy(
            dist_matrix, start_node_idx, args.must_return_to_start
        )
        
        if not initial_greedy_path:
            print("Error: Could not generate an initial greedy path for 2-opt.", file=sys.stderr)
            sys.exit(1)
        
        print(f"Initial greedy path distance: {initial_greedy_distance:.2f} km. Improving with 2-opt...")
        optimal_path_indices, total_distance = solve_tsp_2opt(
            dist_matrix, 
            initial_path=initial_greedy_path, 
            must_return_to_start=args.must_return_to_start
        )
    elif args.algo == "simulated-annealing":
        initial_greedy_path, initial_greedy_distance = solve_tsp_greedy(
            dist_matrix, start_node_idx, args.must_return_to_start
        )
        if not initial_greedy_path:
            print("Error: Could not generate an initial greedy path for Simulated Annealing.", file=sys.stderr)
            sys.exit(1)
        
        print(f"Initial greedy path distance: {initial_greedy_distance:.2f} km. Optimizing with Simulated Annealing...")
        optimal_path_indices, total_distance = solve_tsp_simulated_annealing(
            dist_matrix,
            initial_path=initial_greedy_path,
            must_return_to_start=args.must_return_to_start
            # SA specific parameters can be exposed via CLI later if needed (temp, cooling, etc.)
        )
    # else: # Placeholder for other algorithms
    #     print(f"Algorithm {args.algo} not yet implemented.", file=sys.stderr)
    #     sys.exit(1)

    if not optimal_path_indices:
        print("Could not determine a tour/path.", file=sys.stderr)
        sys.exit(1)

    ordered_places_objects = [places[i] for i in optimal_path_indices]

    print("\n" + ("-" * 30))
    print("Optimal tour:" if args.must_return_to_start else "Optimal tour:")
    for i, place in enumerate(ordered_places_objects):
        print(f"{i+1}) {place.name}")
    
    print(f"Total distance: {total_distance:.2f} km")

    write_route_to_geojson(ordered_places_objects, args.output)
    print(f"Route data appended to or created in {args.output}")

    if args.plot:
        plot_tour(ordered_places_objects, args.plot_output)

if __name__ == "__main__":
    main() 
import argparse
import csv
import json
import sys
import os
import datetime

from distance import Place, calculate_distance_matrix
from tsp_solver import solve_tsp_greedy, solve_tsp_2opt

DEFAULT_INPUT_CSV = "places.csv"
DEFAULT_OUTPUT_GEOJSON = "route.geojson"

def read_places_from_csv(csv_filepath: str) -> list[Place]:
    """Reads place data from a CSV file."""
    places = []
    try:
        with open(csv_filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames or not all(f in reader.fieldnames for f in ['Name', 'Lat', 'Lon']):
                 raise ValueError(f"CSV file '{csv_filepath}' must have 'Name', 'Lat', 'Lon' columns.")
            for row_num, row in enumerate(reader, 1):
                try:
                    name = row['Name'].strip()
                    lat = float(row['Lat'])
                    lon = float(row['Lon'])
                    if not name:
                        raise ValueError(f"Place name cannot be empty (row {row_num} in '{csv_filepath}').")
                    places.append(Place(name, lat, lon))
                except ValueError as e:
                    raise ValueError(f"Error parsing row {row_num} in CSV '{csv_filepath}': {row}. Details: {e}")
                except KeyError as e:
                    raise ValueError(f"Missing column {e} in CSV row {row_num} in '{csv_filepath}': {row}. Ensure 'Name', 'Lat', 'Lon' columns exist.")
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
        choices=["greedy", "2opt"],
        default="2opt",
        help="TSP algorithm to use: 'greedy' or '2opt'.\nDefault: '2opt'."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_GEOJSON,
        help=f"Path to save the GeoJSON route. If file exists, new routes are added.\nDefault: '{DEFAULT_OUTPUT_GEOJSON}'."
    )

    args = parser.parse_args()

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
        sys.exit(0)

    dist_matrix = calculate_distance_matrix(places)

    optimal_path_indices = []
    total_distance = 0.0

    print(f"Calculating route using '{args.algo}' algorithm, starting from '{places[start_node_idx].name}'...")
    if args.must_return_to_start:
        print("The tour will return to the starting place.")
    else:
        print("The path will be open (not returning to start).")


    if args.algo == "greedy":
        optimal_path_indices, total_distance = solve_tsp_greedy(
            dist_matrix, start_node_idx, args.must_return_to_start
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
    # else: # Placeholder for other algorithms like simulated-annealing
    #     print(f"Algorithm {args.algo} not yet implemented.", file=sys.stderr)
    #     sys.exit(1)

    if not optimal_path_indices:
        print("Could not determine a tour/path.", file=sys.stderr)
        sys.exit(1)

    ordered_places_objects = [places[i] for i in optimal_path_indices]

    print("\n" + ("-" * 30))
    print("Optimal tour:" if args.must_return_to_start else "Optimal path:")
    for i, place in enumerate(ordered_places_objects):
        print(f"{i+1}) {place.name}")
    
    print(f"Total distance: {total_distance:.2f} km")

    write_route_to_geojson(ordered_places_objects, args.output)
    print(f"Route data appended to or created in {args.output}")

if __name__ == "__main__":
    main() 
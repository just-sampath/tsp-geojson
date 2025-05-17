import random
import math
import sys

def solve_tsp_greedy(
    dist_matrix: list[list[float]],
    start_node_idx: int = 0,
    must_return_to_start: bool = True,
    places: list | None = None,
    travel_time_matrix: list[list[float]] | None = None
) -> tuple[list[int], float]:
    num_nodes = len(dist_matrix)
    if num_nodes == 0:
        return [], 0.0
    if not (0 <= start_node_idx < num_nodes):
        raise ValueError("Invalid start_node_idx")

    path = [start_node_idx]
    visited = {start_node_idx}
    current_node_idx = start_node_idx
    total_distance = 0.0
    
    current_time = 0.0 # Hours from start, assuming tour starts at time 0
    if places and places[start_node_idx].open_time is not None:
        current_time = max(current_time, places[start_node_idx].open_time) # Wait if start place opens later

    # Check if start node is visitable at all if it has a close time
    if places and places[start_node_idx].close_time is not None and current_time > places[start_node_idx].close_time:
        print(f"Warning: Start place '{places[start_node_idx].name}' cannot be visited as its close time ({places[start_node_idx].close_time}) is before earliest start time ({current_time}). No valid tour.", file=sys.stderr)
        return [], 0.0 # Cannot even start

    while len(path) < num_nodes:
        nearest_neighbor_idx = -1
        min_metric = float('inf') # Can be distance or time-adjusted metric
        best_arrival_at_next = float('inf')
        best_departure_from_current = current_time

        possible_next_steps = []

        for neighbor_idx in range(num_nodes):
            if neighbor_idx not in visited:
                distance_to_neighbor = dist_matrix[current_node_idx][neighbor_idx]
                
                arrival_at_neighbor = current_time # Default if no time matrix
                wait_time_at_neighbor = 0.0

                if travel_time_matrix and places:
                    travel_time_to_neighbor = travel_time_matrix[current_node_idx][neighbor_idx]
                    arrival_at_neighbor = current_time + travel_time_to_neighbor
                    
                    neighbor_place = places[neighbor_idx]
                    if neighbor_place.open_time is not None and arrival_at_neighbor < neighbor_place.open_time:
                        wait_time_at_neighbor = neighbor_place.open_time - arrival_at_neighbor
                        arrival_at_neighbor = neighbor_place.open_time # Arrive and wait till open
                    
                    if neighbor_place.close_time is not None and arrival_at_neighbor > neighbor_place.close_time:
                        # print(f"DEBUG: Cannot visit {neighbor_place.name}. Arrive: {arrival_at_neighbor}, Closes: {neighbor_place.close_time}")
                        continue # Cannot visit this neighbor in time
                
                # Metric for greedy choice: normally distance. Could be arrival time if time is critical.
                # For now, stick to distance, time windows are hard constraints.
                metric = distance_to_neighbor 

                if metric < min_metric:
                    min_metric = metric
                    nearest_neighbor_idx = neighbor_idx
                    best_arrival_at_next = arrival_at_neighbor
                    # best_departure_from_current remains current_time (departure time from current node)
                
                # possible_next_steps.append((neighbor_idx, distance_to_neighbor, arrival_at_neighbor))
        
        if nearest_neighbor_idx == -1:
            if places and travel_time_matrix:
                print(f"Warning: Could not find a valid next place satisfying time windows from '{places[current_node_idx].name}'. Path might be incomplete.", file=sys.stderr)
            else:
                print("Warning: No unvisited neighbor found. Path might be incomplete.", file=sys.stderr)
            break 

        path.append(nearest_neighbor_idx)
        visited.add(nearest_neighbor_idx)
        total_distance += dist_matrix[current_node_idx][nearest_neighbor_idx]
        current_node_idx = nearest_neighbor_idx
        current_time = best_arrival_at_next

    if must_return_to_start:
        if len(path) == num_nodes:
            distance_to_return = dist_matrix[path[-1]][start_node_idx]
            can_return_leg = True

            if travel_time_matrix and places:
                travel_time_for_return_leg = travel_time_matrix[path[-1]][start_node_idx]
                arrival_at_start_node_final = current_time + travel_time_for_return_leg
                
                start_place_object = places[start_node_idx]
                if start_place_object.close_time is not None and arrival_at_start_node_final > start_place_object.close_time:
                    print(f"Warning: Cannot return to start place '{start_place_object.name}' in time. "
                          f"Arrival: {arrival_at_start_node_final:.2f} > Close: {start_place_object.close_time:.2f}. Path will not be closed.", file=sys.stderr)
                    can_return_leg = False
            
            if can_return_leg:
                total_distance += distance_to_return
                path.append(start_node_idx)
            # If not can_return_leg, the path remains open, and total_distance does not include the final leg.
        
        # else if len(path) < num_nodes:
            # Path is incomplete (not all nodes visited, possibly due to time windows).
            # It will be returned as is (open and incomplete). The must_return_to_start objective is not met.
        # else if len(path) == num_nodes + 1 and path[0] == path[-1]:
            # Path is already a complete cycle of num_nodes unique visits. No action needed.
            # This might occur if num_nodes was 0, or some other edge case in path construction.
            pass
            
    return path, total_distance

def calculate_path_distance(path: list[int], dist_matrix: list[list[float]]) -> float:
    distance = 0.0
    for i in range(len(path) - 1):
        distance += dist_matrix[path[i]][path[i+1]]
    return distance

def solve_tsp_2opt(
    dist_matrix: list[list[float]],
    initial_path: list[int] | None = None,
    must_return_to_start: bool = True,
    max_iterations: int = 1000
) -> tuple[list[int], float]:
    num_nodes = len(dist_matrix)
    if num_nodes == 0:
        return [], 0.0

    if initial_path:
        current_path = list(initial_path)
        if must_return_to_start:
            if not current_path or current_path[0] != current_path[-1]:
                raise ValueError("If must_return_to_start is True, initial_path must start and end at the same node.")
    else:
        greedy_path, _ = solve_tsp_greedy(dist_matrix, 0, must_return_to_start)
        greedy_path, _ = solve_tsp_greedy(dist_matrix, 0, must_return_to_start)
        current_path = greedy_path

    best_path = list(current_path)
    best_distance = calculate_path_distance(best_path, dist_matrix)

    path_to_optimize = best_path[:-1] if must_return_to_start and len(best_path) > 1 and best_path[0] == best_path[-1] else best_path
    
    if len(path_to_optimize) < 4:
        return best_path, best_distance

    improved = True
    iter_count = 0
    while improved and iter_count < max_iterations:
        improved = False
        iter_count += 1
        for i in range(1, len(path_to_optimize) - 2):
            for j in range(i + 1, len(path_to_optimize)):
                if j - i == 1: continue
                new_path_segment = path_to_optimize[i:j+1]
                new_path_segment.reverse()
                
                temp_path_optimized = path_to_optimize[:i] + new_path_segment + path_to_optimize[j+1:]
                
                if must_return_to_start:
                    full_temp_path = temp_path_optimized + [path_to_optimize[0]]
                else:
                    full_temp_path = temp_path_optimized

                current_segment_distance = calculate_path_distance(full_temp_path, dist_matrix)

                if current_segment_distance < best_distance:
                    path_to_optimize = temp_path_optimized
                    if must_return_to_start:
                        best_path = path_to_optimize + [path_to_optimize[0]]
                    else:
                        best_path = path_to_optimize
                    best_distance = current_segment_distance
                    improved = True
        
    return best_path, best_distance

def solve_tsp_simulated_annealing(
    dist_matrix: list[list[float]],
    initial_path: list[int] | None = None,
    start_node_idx: int = 0,
    must_return_to_start: bool = True,
    initial_temp: float = 10000.0,
    cooling_rate: float = 0.995,
    min_temp: float = 0.1,
    max_iterations_per_temp: int = 100
) -> tuple[list[int], float]:
    num_nodes = len(dist_matrix)
    if num_nodes == 0:
        return [], 0.0
    if num_nodes < 2:
        if must_return_to_start and num_nodes == 1:
             return [0,0], 0.0
        elif num_nodes ==1:
             return [0], 0.0

    if initial_path:
        current_path = list(initial_path)
        if must_return_to_start and (not current_path or current_path[0] != current_path[-1]):
            raise ValueError("If must_return_to_start, initial_path must be a cycle.")
    else:
        current_path, _ = solve_tsp_greedy(dist_matrix, start_node_idx, must_return_to_start)
        if not current_path:
             current_path = list(range(num_nodes))
             if must_return_to_start:
                 current_path.append(current_path[0])
             random.shuffle(current_path[1:-1] if must_return_to_start and len(current_path) > 2 else current_path)


    current_distance = calculate_path_distance(current_path, dist_matrix)
    best_path = list(current_path)
    best_distance = current_distance
    
    temp = initial_temp

    path_core = current_path[:-1] if must_return_to_start and len(current_path) > 1 and current_path[0] == current_path[-1] else list(current_path)
    if not path_core:
        return current_path, current_distance # Should not happen with earlier checks

    unique_start_node = path_core[0]

    while temp > min_temp:
        for _ in range(max_iterations_per_temp):
            if len(path_core) < 2:
                break

            if len(path_core) < 2:
                continue
            
            i = random.randrange(0, len(path_core))
            j = random.randrange(0, len(path_core))
            while i == j:
                j = random.randrange(0, len(path_core))
            
            if i > j:
                i, j = j, i

            neighbor_core = list(path_core)
            segment_to_reverse = neighbor_core[i:j+1]
            segment_to_reverse.reverse()
            neighbor_core = neighbor_core[:i] + segment_to_reverse + neighbor_core[j+1:]

            if must_return_to_start:
                neighbor_full_path = neighbor_core + [unique_start_node]
            else:
                neighbor_full_path = neighbor_core
            
            neighbor_distance = calculate_path_distance(neighbor_full_path, dist_matrix)

            delta_distance = neighbor_distance - current_distance

            if delta_distance < 0 or random.random() < math.exp(-delta_distance / temp):
                path_core = neighbor_core
                current_distance = neighbor_distance
                
                if must_return_to_start:
                    current_path = path_core + [unique_start_node]
                else:
                    current_path = path_core

                if current_distance < best_distance:
                    best_path = list(current_path)
                    best_distance = current_distance
        
        temp *= cooling_rate
        if len(path_core) < 2:
             break

    return best_path, best_distance

if __name__ == '__main__':
    # Example for testing
    example_dist_matrix = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0]
    ]

    print("Solving TSP with Greedy Heuristic (starting at node 0, returning to start):")
    greedy_path, greedy_distance = solve_tsp_greedy(example_dist_matrix, start_node_idx=0, must_return_to_start=True)
    print(f"Greedy Path: {greedy_path}, Distance: {greedy_distance:.2f}")

    print("\nSolving TSP with Greedy Heuristic (starting at node 0, not returning to start):")
    greedy_path_open, greedy_distance_open = solve_tsp_greedy(example_dist_matrix, start_node_idx=0, must_return_to_start=False)
    print(f"Greedy Path (Open): {greedy_path_open}, Distance: {greedy_distance_open:.2f}")

    print("\nImproving Greedy Path with 2-Opt (returning to start):")
    improved_path, improved_distance = solve_tsp_2opt(example_dist_matrix, initial_path=greedy_path, must_return_to_start=True)
    print(f"2-Opt Path: {improved_path}, Distance: {improved_distance:.2f}")

    print("\nImproving a different initial path with 2-Opt (returning to start):")
    custom_initial_path_closed = [0, 2, 1, 3, 0]
    custom_initial_dist = calculate_path_distance(custom_initial_path_closed, example_dist_matrix)
    print(f"Custom Initial Path: {custom_initial_path_closed}, Distance: {custom_initial_dist:.2f}")
    improved_custom_path, improved_custom_distance = solve_tsp_2opt(
        example_dist_matrix, 
        initial_path=custom_initial_path_closed, 
        must_return_to_start=True
    )
    print(f"2-Opt from Custom Path: {improved_custom_path}, Distance: {improved_custom_distance:.2f}")

    print("\nSolving TSP with 2-Opt from scratch (greedy internally, returning to start):")
    path_2opt_auto, dist_2opt_auto = solve_tsp_2opt(example_dist_matrix, must_return_to_start=True)
    print(f"2-Opt Path (auto-greedy): {path_2opt_auto}, Distance: {dist_2opt_auto:.2f}")

    print("\nSolving TSP with 2-Opt from scratch (greedy internally, NOT returning to start):")
    path_2opt_auto_open, dist_2opt_auto_open = solve_tsp_2opt(example_dist_matrix, must_return_to_start=False)
    print(f"2-Opt Path (auto-greedy, open): {path_2opt_auto_open}, Distance: {dist_2opt_auto_open:.2f}")

    small_dist_matrix = [
        [0, 1],
        [1, 0]
    ]
    small_greedy_path, small_greedy_dist = solve_tsp_greedy(small_dist_matrix, 0, True)
    print(f"\nSmall Greedy Path: {small_greedy_path}, Distance: {small_greedy_dist}")
    small_2opt_path, small_2opt_dist = solve_tsp_2opt(small_dist_matrix, initial_path=small_greedy_path, must_return_to_start=True)
    print(f"Small 2-Opt Path: {small_2opt_path}, Distance: {small_2opt_dist}")

    three_node_matrix = [
        [0, 1, 5],
        [1, 0, 2],
        [5, 2, 0]
    ]
    three_node_matrix_clear = [
        [0, 1, 10],
        [1, 0, 2],
        [10,2, 0]
    ]

    print("\nTesting 2-opt with 3 nodes (should typically return initial path or equivalent for symmetric costs)")
    three_nodes_dist_matrix = [
        [0, 10, 15],
        [10, 0, 35],
        [15, 35, 0]
    ]
    initial_3_path, _ = solve_tsp_greedy(three_nodes_dist_matrix, 0, True)
    print(f"Initial 3-node path: {initial_3_path}")
    path_3_2opt, dist_3_2opt = solve_tsp_2opt(three_nodes_dist_matrix, initial_path=initial_3_path, must_return_to_start=True)
    print(f"3-Node 2-Opt Path: {path_3_2opt}, Distance: {dist_3_2opt:.2f}")

    print("\nSolving TSP with Simulated Annealing (from greedy, returning to start):")
    sa_path, sa_distance = solve_tsp_simulated_annealing(
        example_dist_matrix, 
        initial_path=greedy_path, 
        must_return_to_start=True
    )
    print(f"SA Path (from greedy): {sa_path}, Distance: {sa_distance:.2f}")

    print("\nSolving TSP with Simulated Annealing (from scratch, returning to start):")
    sa_path_auto, sa_distance_auto = solve_tsp_simulated_annealing(
        example_dist_matrix, 
        start_node_idx=0, 
        must_return_to_start=True
    )
    print(f"SA Path (auto-greedy): {sa_path_auto}, Distance: {sa_distance_auto:.2f}")

    print("\nSolving TSP with Simulated Annealing (from scratch, NOT returning to start):")
    sa_path_auto_open, sa_distance_auto_open = solve_tsp_simulated_annealing(
        example_dist_matrix, 
        start_node_idx=0, 
        must_return_to_start=False
    )
    print(f"SA Path (auto-greedy, open): {sa_path_auto_open}, Distance: {sa_distance_auto_open:.2f}")

    print("\nTesting Greedy with Time Windows:")
    class MockPlace:
        def __init__(self, name, open_time, close_time):
            self.name = name
            self.open_time = open_time
            self.close_time = close_time

    test_places_tw = [
        MockPlace("P0", 0, 100),
        MockPlace("P1", 0, 1),
        MockPlace("P2", 5, 100),
        MockPlace("P3", 0, 100)
    ]
    speed_kmh = 10.0
    example_time_matrix = [[d/speed_kmh for d in row] for row in example_dist_matrix]

    print("Greedy with time windows (Start P0, speed 10km/h): P1 closes at 1h, P2 opens at 5h")
    greedy_tw_path, greedy_tw_dist = solve_tsp_greedy(
        example_dist_matrix, 
        start_node_idx=0, 
        must_return_to_start=True, 
        places=test_places_tw, 
        travel_time_matrix=example_time_matrix
    )
    print(f"Greedy TW Path: {greedy_tw_path}, Distance: {greedy_tw_dist:.2f} km")

    test_places_tw_impossible = [
        MockPlace("P0", 0, 100),
        MockPlace("P1", 0, 0.5),
        MockPlace("P2", 0, 100),
        MockPlace("P3", 0, 100)
    ]
    print("\nGreedy with impossible time window (P1 closes at 0.5h, travel 0->1 is 1h)")
    greedy_tw_path_imp, greedy_tw_dist_imp = solve_tsp_greedy(
        example_dist_matrix, 
        start_node_idx=0, 
        must_return_to_start=True, 
        places=test_places_tw_impossible, 
        travel_time_matrix=example_time_matrix
    )
    print(f"Greedy TW Path (impossible): {greedy_tw_path_imp}, Distance: {greedy_tw_dist_imp:.2f} km")
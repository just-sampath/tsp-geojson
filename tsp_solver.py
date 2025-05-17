def solve_tsp_greedy(
    dist_matrix: list[list[float]],
    start_node_idx: int = 0,
    must_return_to_start: bool = True
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

    while len(path) < num_nodes:
        nearest_neighbor_idx = -1
        min_distance = float('inf')

        for neighbor_idx in range(num_nodes):
            if neighbor_idx not in visited:
                distance = dist_matrix[current_node_idx][neighbor_idx]
                if distance < min_distance:
                    min_distance = distance
                    nearest_neighbor_idx = neighbor_idx
        
        if nearest_neighbor_idx == -1:
            break 

        path.append(nearest_neighbor_idx)
        visited.add(nearest_neighbor_idx)
        total_distance += min_distance
        current_node_idx = nearest_neighbor_idx

    if must_return_to_start and len(path) == num_nodes:
        total_distance += dist_matrix[path[-1]][start_node_idx]
        path.append(start_node_idx)
    
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
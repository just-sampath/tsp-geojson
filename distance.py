from collections import namedtuple
import math

Place = namedtuple("Place", ["name", "lat", "lon", "open_time", "close_time"])

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371 
    return c * r

def calculate_distance_matrix(places: list[Place]) -> list[list[float]]:
    num_places = len(places)
    dist_matrix = [[0.0] * num_places for _ in range(num_places)]
    for i in range(num_places):
        for j in range(i + 1, num_places):
            place1 = places[i]
            place2 = places[j]
            distance = haversine(place1.lat, place1.lon, place2.lat, place2.lon)
            dist_matrix[i][j] = distance
            dist_matrix[j][i] = distance
    return dist_matrix

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    eiffel_tower = Place("Eiffel Tower", 48.8584, 2.2945, None, None) # No time windows
    louvre_museum = Place("Louvre Museum", 48.8606, 2.3376, 9.0, 18.0) # Open 9 AM to 6 PM
    notre_dame = Place("Notre-Dame", 48.8530, 2.3499, 8.0, 17.5) # Open 8 AM to 5:30 PM

    test_places = [eiffel_tower, louvre_museum, notre_dame]

    print(f"Calculating distance between {eiffel_tower.name} and {louvre_museum.name}:")
    dist = haversine(eiffel_tower.lat, eiffel_tower.lon, louvre_museum.lat, louvre_museum.lon)
    print(f"{dist:.2f} km")

    print("\nCalculating distance matrix:")
    matrix = calculate_distance_matrix(test_places)
    for i, place1 in enumerate(test_places):
        for j, place2 in enumerate(test_places):
            print(f"Dist({place1.name}, {place2.name}): {matrix[i][j]:.2f} km")
        print("---") 
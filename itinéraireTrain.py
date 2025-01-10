import csv
from collections import defaultdict
import heapq

def parse_time(hms_str):
    """
    Convertit une chaîne 'HH:MM:SS' en nombre de secondes depuis minuit.
    Retourne None si la chaîne est vide ou invalide.
    """
    if not hms_str or hms_str == "":
        return None
    h, m, s = map(int, hms_str.split(':'))
    return h * 3600 + m * 60 + s

def read_stops(stops_filename):
    """
    Lit stops.txt et retourne:
      stops_dict[stop_id] = stop_name
      name_to_id[stop_name] = [stop_id1, stop_id2,...]
    Ne conserve que les StopPoint:OCETrain (exemple).
    """
    stops_dict = {}
    name_to_id = defaultdict(list)

    with open(stops_filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stop_id = row['stop_id']
            stop_name = row['stop_name']

            # On ignore les StopArea
            if stop_id.startswith("StopArea:"):
                continue

            # On ne garde que certains stops (exemple: StopPoint:OCETrain)
            if stop_id.startswith("StopPoint:OCETrain"):
                stops_dict[stop_id] = stop_name
                name_to_id[stop_name].append(stop_id)

    return stops_dict, name_to_id

def read_stop_times(stop_times_filename):
    """
    Lit stop_times.txt et construit un dict :
      trip_stop_map[trip_id] = [(stop_id, stop_sequence, arr_sec, dep_sec), ...]
    trié par stop_sequence.
    """
    trip_stop_map = defaultdict(list)
    with open(stop_times_filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trip_id = row['trip_id']
            stop_id = row['stop_id']
            stop_sequence = int(row['stop_sequence'])
            arr_sec = parse_time(row['arrival_time'])
            dep_sec = parse_time(row['departure_time'])

            trip_stop_map[trip_id].append((stop_id, stop_sequence, arr_sec, dep_sec))

    # On trie chaque trip par stop_sequence
    for t_id in trip_stop_map:
        trip_stop_map[t_id].sort(key=lambda x: x[1])
    return trip_stop_map

def build_graph_with_duration(trip_stop_map):
    """
    Construit un graphe pondéré (durée en secondes).
    graph[stop_id] = list of (autre_stop_id, duree_en_secondes).
    """
    graph = defaultdict(list)

    for trip_id, stops_info in trip_stop_map.items():
        # stops_info est trié par stop_sequence
        for i in range(len(stops_info) - 1):
            s1, seq1, arr1, dep1 = stops_info[i]
            s2, seq2, arr2, dep2 = stops_info[i+1]

            # Calcul de la durée s1 -> s2
            if (arr2 is not None) and (dep1 is not None):
                duration_s1_s2 = arr2 - dep1
                if duration_s1_s2 < 0:
                    # on ignore si incohérent
                    continue
            else:
                # pas de data fiable
                continue

            # Ajout arc s1->s2
            graph[s1].append((s2, duration_s1_s2))

            # Ajout arc s2->s1 (bidirectionnel, hypothèse)
            # On pourrait recalculer, ex arr1 - dep2, si la durée n’est pas symétrique
            if (arr1 is not None) and (dep2 is not None):
                duration_s2_s1 = arr1 - dep2
                if duration_s2_s1 >= 0:
                    graph[s2].append((s1, duration_s2_s1))
            else:
                # sinon on suppose la même durée
                graph[s2].append((s1, duration_s1_s2))

    return graph

def dijkstra(graph, start_stop_id, goal_stop_id):
    """
    Trouve le plus court chemin (en temps) entre start_stop_id et goal_stop_id, via Dijkstra.
    Retourne (chemin, cout_total) ou (None, inf) si pas trouvé.
    """
    distances = defaultdict(lambda: float('inf'))
    distances[start_stop_id] = 0

    heap = [(0, start_stop_id, [start_stop_id])]
    visited = set()

    while heap:
        current_dist, current_stop, path = heapq.heappop(heap)

        if current_stop in visited:
            continue
        visited.add(current_stop)

        if current_stop == goal_stop_id:
            return path, current_dist

        for (neighbor, cost) in graph[current_stop]:
            new_dist = current_dist + cost
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                new_path = path + [neighbor]
                heapq.heappush(heap, (new_dist, neighbor, new_path))

    return None, float('inf')

def next_departure_from_stop(stop_times_filename, stop_id, current_time_str):
    """
    Renvoie l'horaire (au format HH:MM:SS) du prochain départ (théorique)
    depuis stop_id après current_time_str, basé uniquement sur stop_times.txt.
    """
    current_secs = parse_time(current_time_str)
    if current_secs is None:
        print("Heure invalide.")
        return None

    possible_departures = []

    with open(stop_times_filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['stop_id'] == stop_id:
                dep_str = row['departure_time']
                dep_sec = parse_time(dep_str)
                if dep_sec is not None:
                    # on garde ce départ
                    possible_departures.append((dep_sec, dep_str))

    # On filtre les départs après current_secs
    future = [(dep_sec, dep_str) for (dep_sec, dep_str) in possible_departures
              if dep_sec >= current_secs]

    # On trie par l'heure de départ
    future.sort(key=lambda x: x[0])

    if not future:
        return None  # pas de départ plus tard dans la journée
    else:
        # prochain départ
        return future[0][1]  # la chaîne HH:MM:SS

def itineraireTrain(stops_filename, stop_times_filename, departure_name, arrival_name):
    """
    Renvoie (path_names, duree_str) pour l'itinéraire le plus rapide (Dijkstra)
    entre departure_name et arrival_name.
    """
    # 1) Lecture des stops
    stops_dict, name_to_id = read_stops(stops_filename)

    # 2) Lecture de stop_times
    trip_stop_map = read_stop_times(stop_times_filename)

    # 3) Construit le graphe pondéré
    graph = build_graph_with_duration(trip_stop_map)

    # 4) Contrôle existence
    if departure_name not in name_to_id:
        print(f"Le nom de gare '{departure_name}' est introuvable dans stops.txt.")
        return None, None
    if arrival_name not in name_to_id:
        print(f"Le nom de gare '{arrival_name}' est introuvable dans stops.txt.")
        return None, None

    departure_id = name_to_id[departure_name][0]
    arrival_id   = name_to_id[arrival_name][0]

    # 5) Algorithme de plus court chemin (en temps)
    path, total_time = dijkstra(graph, departure_id, arrival_id)

    if path is None:
        return None, None

    # Convertir la durée en HH:MM:SS
    hours = total_time // 3600
    mins  = (total_time % 3600) // 60
    secs  = total_time % 60
    duree_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

    # Conversion en noms de gares
    path_names = [stops_dict[s] for s in path]
    return path_names, duree_str

def main():
    # Paramètres
    stops_filename = 'dataSncf/stops.txt'
    stop_times_filename = 'dataSncf/stop_times.txt'

    departure_name = "Saverne"
    arrival_name   = "Sarreguemines"

    # 1) Calcul de l'itinéraire le plus rapide (simple)
    path_names, duree_str = itineraireTrain(
        stops_filename, 
        stop_times_filename, 
        departure_name, 
        arrival_name
    )
    if path_names is None:
        print("Aucun itinéraire trouvé.")
    else:
        print("Itinéraire (noms de gares) :", " -> ".join(path_names))
        print("Durée totale estimée :", duree_str)

    # 2) Récupérer le prochain train depuis un arrêt, après une heure donnée
    # On suppose qu’on connaît déjà le stop_id ou on récupère un via 'name_to_id'.
    # Ex : On prend le premier stop_id de "Saverne"
    stops_dict, name_to_id = read_stops(stops_filename)
    saverne_id = name_to_id[departure_name][0]

    # L'heure courante
    current_time_str = "03:00:00"

    next_dep = next_departure_from_stop(stop_times_filename, saverne_id, current_time_str)
    if next_dep is None:
        print(f"Aucun départ ultérieur après {current_time_str} pour cet arrêt.")
    else:
        print(f"Prochain départ après {current_time_str} = {next_dep}")

if __name__ == "__main__":
    main()


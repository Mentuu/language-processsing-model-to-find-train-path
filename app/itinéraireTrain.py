import csv
from collections import defaultdict
import heapq
import os 
from datetime import datetime, timedelta

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
            stop_name = row['stop_name'].lower()  # Transforme en minuscule

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

def prochain_depart(stop_times_filename, stop_id, current_time_sec):
    """
    Recherche le prochain départ depuis `stop_id` après `current_time_sec`.
    """
    prochain_horaire = None
    prochain_depart = None
    prev_departure_time = 0

    with open(stop_times_filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['stop_id'] == stop_id:
                if row['pickup_type'] == 1 and row['drop_off_type'] == 1:
                    continue
                  # Vérification des horaires
                if row['arrival_time'] is None or row['departure_time'] is None:
                    continue
                if row['departure_time'] < row['arrival_time']:
                    continue
                dep_sec = parse_time(row['departure_time'])
                if dep_sec and dep_sec >= current_time_sec:  # Prochain horaire après l'heure actuelle
                    if prochain_horaire is None or dep_sec < prochain_horaire:
                        prochain_horaire = dep_sec
                        prochain_depart = row

    return prochain_depart

def itineraireTrain(stops_filename, stop_times_filename, departure_name, arrival_name, intermediate_names=None):
    """
    Renvoie (path_names, duree_str, prochain_depart_time) pour l'itinéraire le plus rapide
    à partir de maintenant entre departure_name et arrival_name, en passant par des villes intermédiaires.
    """
    # Lecture des fichiers
    stops_dict, name_to_id = read_stops(stops_filename)

    # Conversion des noms en minuscules pour correspondre à ceux de stops.txt
    departure_name = departure_name.lower()
    arrival_name = arrival_name.lower()
    intermediate_names = [name.lower() for name in intermediate_names] if intermediate_names else []

    # Rechercher les IDs des gares pour chaque étape
    departure_ids = [stop_id for stop_name, stop_ids in name_to_id.items() if departure_name in stop_name for stop_id in stop_ids]
    arrival_ids = [stop_id for stop_name, stop_ids in name_to_id.items() if arrival_name in stop_name for stop_id in stop_ids]
    intermediate_ids_list = [
        [stop_id for stop_name, stop_ids in name_to_id.items() if name in stop_name for stop_id in stop_ids]
        for name in intermediate_names
    ]

    # Vérification des gares
    if not departure_ids:
        print("Gare de départ introuvable.")
        return None, None, None
    if not arrival_ids:
        print("Gare d'arrivée introuvable.")
        return None, None, None
    if intermediate_names and any(not ids for ids in intermediate_ids_list):
        print("Une ou plusieurs gares intermédiaires sont introuvables.")
        return None, None, None

    # Heure actuelle (en secondes depuis minuit)
    now = datetime.now()
    current_time_sec = now.hour * 3600 + now.minute * 60 + now.second

    # Lecture de stop_times pour reconstruire le graphe
    trip_stop_map = read_stop_times(stop_times_filename)
    graph = build_graph_with_duration(trip_stop_map)

    # Étapes successives (départ -> intermédiaires -> arrivée)
    all_stops = [departure_ids] + intermediate_ids_list + [arrival_ids]
    full_path = []
    total_duration = 0
    next_departure_time = None

    for i in range(len(all_stops) - 1):
        start_ids = all_stops[i]
        end_ids = all_stops[i + 1]

        best_path = None
        best_duration = float('inf')
        best_departure = None

        for start_id in start_ids:
            for end_id in end_ids:
                # Trouver le prochain départ
                print(start_id)
                departure_info = prochain_depart(stop_times_filename, start_id, current_time_sec)


                if not departure_info:
                    continue

                dep_time_sec = parse_time(departure_info['departure_time'])
                path, duration = dijkstra(graph, start_id, end_id)

                if path and dep_time_sec + duration < best_duration:
                    best_path = path
                    best_duration = duration
                    best_departure = departure_info

        if not best_path:
            print(f"Aucun itinéraire trouvé pour l'étape {i + 1}.")
            return None, None, None

        # Mise à jour pour la prochaine étape
        full_path.extend(best_path[:-1])  # Éviter de répéter le dernier arrêt
        total_duration += best_duration
        next_departure_time = best_departure['departure_time']
        current_time_sec += best_duration

    # Ajouter le dernier arrêt
    full_path.append(all_stops[-1][0])

    # Convertir la durée totale en HH:MM:SS
    hours = total_duration // 3600
    minutes = (total_duration % 3600) // 60
    seconds = total_duration % 60
    duree_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Convertir les stops en noms de gares
    path_names = [stops_dict.get(s, s) for s in full_path]

    return path_names, duree_str, next_departure_time


def main():
    # Paramètres par défaut ou récupérés depuis les paramètres de requête
    stops_filename = os.path.join(os.path.dirname(__file__), '../dataSncf/stops.txt')
    stop_times_filename = os.path.join(os.path.dirname(__file__), '../dataSncf/stop_times.txt')

    departure_name = "Strasbourg"
    arrival_name = "Mulhouse"
    intermediate_names = []

    # 1) Calcul de l'itinéraire le plus rapide (simple)
    path_names, duree_str, next_dep_time  = itineraireTrain(
        stops_filename, 
        stop_times_filename, 
        departure_name, 
        arrival_name,
        intermediate_names
    )

    if path_names is None:
        print("Aucun itinéraire trouvé.")
    else:
        print("Itinéraire (noms de gares) :", " -> ".join(path_names))
        print("Durée totale estimée :", duree_str)
        print("Prochain départ :", next_dep_time)


if __name__ == "__main__":
    main()


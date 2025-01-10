import csv
from collections import defaultdict, deque
import folium

def read_stops(stops_filename):
    stops_dict = {}
    name_to_id = defaultdict(list)
    with open(stops_filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stop_id = row['stop_id']
            stop_name = row['stop_name']
            
            # Filtrer pour ignorer les StopArea
            if stop_id.startswith("StopArea:"):
                continue
            
            if(stop_id.startswith("StopPoint:OCETrain")):
                # Sinon, c'est un StopPoint ou autre
                stops_dict[stop_id] = stop_name
                name_to_id[stop_name].append(stop_id)
            else:
                continue
    return stops_dict, name_to_id


def read_stops_map(stops_filename):
    """
    Lit le fichier stops.txt et renvoie :
      - stops_dict : dict[stop_id -> stop_name]
      - name_to_id : dict[stop_name -> list de stop_id]
      - stop_coords: dict[stop_id -> (lat, lon)]
    On filtre les 'StopArea:' et ne garde que 'StopPoint:OCETrain'.
    """
    stops_dict = {}
    name_to_id = defaultdict(list)
    stop_coords = {}

    with open(stops_filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stop_id = row['stop_id']
            stop_name = row['stop_name']

            # Filtrer pour ignorer StopArea
            if stop_id.startswith("StopArea:"):
                continue

            # On ne garde que les StopPoint:OCETrain
            if stop_id.startswith("StopPoint:OCETrain"):
                stops_dict[stop_id] = stop_name
                name_to_id[stop_name].append(stop_id)

                # Récupérer latitude / longitude
                # (Assurez-vous que stops.txt contient bien stop_lat, stop_lon)
                lat = row.get('stop_lat')
                lon = row.get('stop_lon')

                # Convertir en float si possible
                if lat and lon:
                    try:
                        lat_f = float(lat)
                        lon_f = float(lon)
                        stop_coords[stop_id] = (lat_f, lon_f)
                    except ValueError:
                        # Si on ne peut pas convertir, on ignore
                        pass
            else:
                continue

    return stops_dict, name_to_id, stop_coords

def read_stop_times(stop_times_filename):
    """
    Lit le fichier stop_times.txt.
    Renvoie un dict[trip_id -> liste (stop_id, stop_sequence)] triée par stop_sequence.
    """
    trip_stop_map = defaultdict(list)
    with open(stop_times_filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            trip_id = row['trip_id']
            stop_id = row['stop_id']
            # Convertir stop_sequence en entier
            stop_sequence = int(row['stop_sequence'])
            trip_stop_map[trip_id].append((stop_id, stop_sequence))

    # Tri par stop_sequence pour chaque trip
    for t_id in trip_stop_map:
        trip_stop_map[t_id].sort(key=lambda x: x[1])
    return trip_stop_map

def build_graph(trip_stop_map):
    """
    Construit un graphe bidirectionnel : dict[stop_id -> set(stop_id)].
    Pour chaque trip, on relie les arrêts consécutifs (stop_sequence i -> i+1),
    dans les deux sens.
    """
    graph = defaultdict(set)
    for trip_id, stops_info in trip_stop_map.items():
        for i in range(len(stops_info) - 1):
            current_stop = stops_info[i][0]
            next_stop = stops_info[i+1][0]
            # Arête "aller"
            graph[current_stop].add(next_stop)
            # Arête "retour" (pour voyager dans l'autre sens)
            graph[next_stop].add(current_stop)
    return graph

def bfs_shortest_path(graph, start_stop_id, goal_stop_id):
    """
    Recherche en largeur (BFS) pour trouver le plus court chemin
    en nombre d'arêtes entre start_stop_id et goal_stop_id.
    Renvoie la liste [stop_id1, stop_id2, ...] ou None si pas trouvé.
    """
    if start_stop_id == goal_stop_id:
        return [start_stop_id]

    visited = set()
    # queue contient des tuples (stop_actuel, chemin_pour_y_arriver)
    queue = deque([(start_stop_id, [start_stop_id])])

    while queue:
        current_stop, path = queue.popleft()

        if current_stop == goal_stop_id:
            return path

        for neighbor in graph[current_stop]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None

def create_map(stop_coords, graph, stops_dict):
    """
    Construit et renvoie un objet folium.Map représentant le réseau.
    - stop_coords : dict[stop_id -> (lat, lon)]
    - graph       : dict[stop_id -> set of stop_id]
    - stops_dict  : dict[stop_id -> stop_name]
    """

    # 1) Trouver un centre approximatif (moyenne des lat/lon ou un centre fixe)
    if stop_coords:
        all_lats = [coord[0] for coord in stop_coords.values()]
        all_lons = [coord[1] for coord in stop_coords.values()]
        avg_lat = sum(all_lats) / len(all_lats)
        avg_lon = sum(all_lons) / len(all_lons)
    else:
        # Si aucune coordonnée, on centre la carte sur Paris (par exemple)
        avg_lat, avg_lon = 48.8566, 2.3522

    # 2) Créer la carte centrée sur (avg_lat, avg_lon), zoom 6 ou 7 pour la France
    folium_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)

    # 3) Ajouter un marker pour chaque arrêt connu
    for stop_id, (lat, lon) in stop_coords.items():
        stop_name = stops_dict.get(stop_id, "Inconnu")
        folium.Marker(
            location=[lat, lon],
            popup=f"{stop_name}\n({stop_id})",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(folium_map)

    # 4) Tracer les arêtes (lignes) pour visualiser les trajets
    #    Attention : cela peut faire beaucoup de lignes si la base est grande !
    for s1, neighbors in graph.items():
        if s1 not in stop_coords:
            continue  # On ne trace que si on a les coords
        lat1, lon1 = stop_coords[s1]

        for s2 in neighbors:
            # Pour éviter de tracer deux fois la même ligne (s1->s2 et s2->s1),
            # on peut tracer uniquement si s2 > s1 (ou un autre critère).
            # Ou alors on trace tout (ce qui double les segments).
            if s2 not in stop_coords:
                continue
            lat2, lon2 = stop_coords[s2]

            # Tracer la polyligne
            folium.PolyLine(
                locations=[(lat1, lon1), (lat2, lon2)],
                color="red",
                weight=2,
                opacity=0.6
            ).add_to(folium_map)

    return folium_map

def main():
    # ----------------------------------------------------------------------
    # 1. Lecture des fichiers
    # ----------------------------------------------------------------------
    stops_filename = 'dataSncf/stops.txt'
    stop_times_filename = 'dataSncf/stop_times.txt'

    # Lecture de stops.txt => (stop_id -> stop_name), (stop_name -> stop_ids)
    stops_dict, name_to_id = read_stops(stops_filename)
    # Lecture de stop_times.txt => trip_stop_map (trip_id -> liste d'arrêts ordonnés)
    trip_stop_map = read_stop_times(stop_times_filename)
    # Construction du graphe bidirectionnel
    graph = build_graph(trip_stop_map)

    # ----------------------------------------------------------------------
    # 2. Définition du départ et de l'arrivée (par nom de gare)
    # ----------------------------------------------------------------------
    departure_name = "Saverne"
    arrival_name   = "Steinbourg"

    # Vérification que les noms existent dans name_to_id
    if departure_name not in name_to_id:
        print(f"Le nom de gare '{departure_name}' n'existe pas dans stops.txt.")
        return
    if arrival_name not in name_to_id:
        print(f"Le nom de gare '{arrival_name}' n'existe pas dans stops.txt.")
        return

    # Récupération des stop_ids possibles pour ce nom de gare
    departure_ids = name_to_id[departure_name]  # liste de stop_id
    arrival_ids   = name_to_id[arrival_name]    # liste de stop_id

    # On ne va gérer qu'un seul stop_id départ et un seul stop_id arrivée
    departure_id = departure_ids[0]
    arrival_id   = arrival_ids[0]

    print(f"SAVERNE => stop_id = {departure_id}")
    print(f"STEINBOURG => stop_id = {arrival_id}")

    # ----------------------------------------------------------------------
    # 3. Recherche du plus court chemin (BFS)
    # ----------------------------------------------------------------------
    path = bfs_shortest_path(graph, departure_id, arrival_id)

    if path is None:
        print(f"Aucun itinéraire trouvé entre '{departure_name}' et '{arrival_name}'.")
        return

    # ----------------------------------------------------------------------
    # 4. Affichage du résultat
    # ----------------------------------------------------------------------
    print("Itinéraire trouvé (en stop_id) :", " -> ".join(path))

    # Conversion en noms de gares pour un affichage lisible
    path_names = [stops_dict[sid] for sid in path]
    print("Itinéraire (noms de gares) :", " -> ".join(path_names))

    # ----------------------------------------------------------------------
    # 5. Création de la carte avec Folium (visualisation)
    # ----------------------------------------------------------------------
    # stops_dict, name_to_id, stop_coords = read_stops_map(stops_filename)
    # trip_stop_map = read_stop_times(stop_times_filename)
    # # Graphe
    # graph = build_graph(trip_stop_map)

    # # Construction de la carte
    # folium_map = create_map(stop_coords, graph, stops_dict)

    # # Sauvegarde dans un fichier HTML
    # folium_map.save("sncf_map.html")
    # print("Carte générée : sncf_map.html")

if __name__ == "__main__":
    main()

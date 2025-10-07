from django.shortcuts import render
from django.http import JsonResponse
import json
import requests
import osmnx as ox
import networkx as nx
import math
import scipy
# --- NOTE: We no longer need a Google Maps API key ---

# --- Module 1: Decision Tree Logic (This remains the same) ---
class TreeNode:
    def __init__(self, value, is_question):
        self.value = value
        self.is_question = is_question
        self.children = {}

def build_symptom_tree():
    root = TreeNode("Is your primary symptom related to your chest or head?", True)
    chest = TreeNode("Are you experiencing sharp pain or a dull ache?", True)
    root.children["Chest"] = chest
    sharp_pain = TreeNode("Is it accompanied by shortness of breath?", True)
    chest.children["Sharp Pain"] = sharp_pain
    sharp_pain.children["Yes"] = TreeNode("Cardiologist", False)
    sharp_pain.children["No"] = TreeNode("General Physician", False)
    head = TreeNode("Are you experiencing a headache or dizziness?", True)
    root.children["Head"] = head
    headache = TreeNode("Is the headache accompanied by a fever?", True)
    head.children["Headache"] = headache
    headache.children["Yes"] = TreeNode("General Physician", False)
    headache.children["No"] = TreeNode("Neurologist", False)
    return root

SYMPTOM_TREE = build_symptom_tree()

# --- Main view to render the HTML page (This remains the same) ---
def index(request):
    return render(request, 'core/index.html')

# --- API view for the symptom checker (This remains the same) ---
def symptom_check_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        answers = data.get('answers', [])
        
        current_node = SYMPTOM_TREE
        for answer in answers:
            if answer in current_node.children:
                current_node = current_node.children[answer]
            else:
                return JsonResponse({'error': 'Invalid path'}, status=400)

        if current_node.is_question:
            response_data = { 'type': 'question', 'text': current_node.value, 'options': list(current_node.children.keys()) }
        else:
            response_data = { 'type': 'diagnosis', 'specialty': current_node.value }
        return JsonResponse(response_data)


# --- API view for finding pharmacies (UPDATED FOR OPENSTREETMAP) ---
def find_pharmacies_api(request):
    lat_str = request.GET.get('lat')
    lon_str = request.GET.get('lon')

    if not lat_str or not lon_str:
        return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)

    try:
        user_point = (float(lat_str), float(lon_str))
        user_point = (12.9716, 77.5946) # Test location: Bengaluru City Center
        G = ox.graph_from_point(user_point, dist=10000, network_type='drive')
 
        # --- 2. DEFINE THE HEURISTIC FUNCTION FOR A* ---
        # This function calculates the straight-line distance between two nodes
        def euclidean_dist_heuristic(u, v):
            # Get the coordinates for the two nodes
            u_coords = (G.nodes[u]['y'], G.nodes[u]['x'])
            v_coords = (G.nodes[v]['y'], G.nodes[v]['x'])
            # Calculate the Euclidean distance
            return math.dist(u_coords, v_coords)
        
        tags = {"amenity": "pharmacy"}
        pharmacies_gdf = ox.features_from_point(user_point, tags, dist=25000)
        pharmacies_gdf = pharmacies_gdf[pharmacies_gdf.geom_type == 'Point']
        if pharmacies_gdf.empty:
            return JsonResponse({'pharmacies': []}) 
        
        user_node = ox.nearest_nodes(G, user_point[1], user_point[0])
        pharmacy_nodes = ox.nearest_nodes(G, pharmacies_gdf['geometry'].x, pharmacies_gdf['geometry'].y)

        results = []
        for i, node in enumerate(pharmacy_nodes):
            try:
                # --- 3. USE A* ALGORITHM INSTEAD OF DIJKSTRA ---
                # We call astar_path_length and pass our heuristic function
                distance = nx.astar_path_length(
                    G, 
                    source=user_node, 
                    target=node, 
                    heuristic=euclidean_dist_heuristic, 
                    weight='length'
                )
                
                pharmacy_name = pharmacies_gdf.iloc[i]['name']
                if pharmacy_name and not isinstance(pharmacy_name, float):
                    results.append({
                        'name': pharmacy_name,
                        'vicinity': f"{distance:.0f} meters away"
                    })
            except (nx.NetworkXNoPath, KeyError):
                continue
        
        sorted_results = sorted(results, key=lambda p: float(p['vicinity'].split()[0]))
        return JsonResponse({'pharmacies': sorted_results[:5]})

    except Exception as e:
    # This will print the real, detailed error to your terminal
        print("--- DETAILED ERROR IN API ---")
        import traceback
        traceback.print_exc() # This prints the full traceback
        print("-----------------------------")
        return JsonResponse({'error': f"An error occurred: {str(e)}"}, status=500)
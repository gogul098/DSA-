from django.shortcuts import render, redirect
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .queue_manager import (
    add_to_queue, get_queue_position, get_queue_count, 
    remove_from_queue, get_queue_number, assign_specialty,
    is_in_any_queue, PATIENT_QUEUES
)
import osmnx as ox
import networkx as nx
import time

def home_view(request):
    return render(request, 'core/home.html')

def patient_form_view(request):
    symptoms = ['Chest Pain', 'Shortness of Breath', 'Headache', 'Dizziness', 'Fever', 'Cough']
    return render(request, 'core/patient_form.html', {'symptoms': symptoms})

def patient_submit_view(request):
    if request.method == 'POST':
        selected_symptoms = request.POST.getlist('symptoms')
        specialty = assign_specialty(selected_symptoms)

        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        if not is_in_any_queue(session_key):
            queue_number = add_to_queue(specialty, session_key)
            broadcast_queue_update(specialty)

        return redirect('patient_status', specialty=specialty)
    return redirect('patient_form')

def patient_status_view(request, specialty):
    session_key = request.session.session_key
    position = get_queue_position(specialty, session_key)
    total = get_queue_count(specialty)
    queue_number = get_queue_number(session_key) if session_key else None
    
    context = {
        'specialty': specialty,
        'position': position,
        'total': total,
        'queue_number': queue_number,
        'session_key': session_key
    }
    return render(request, 'core/patient_status.html', context)

def doctor_specialty_select_view(request):
    specialties = PATIENT_QUEUES.keys()
    return render(request, 'core/doctor_specialty_select.html', {'specialties': specialties})

def doctor_dashboard_view(request, specialty):
    queue = PATIENT_QUEUES.get(specialty, [])
    queue_list = []
    for idx, session_key in enumerate(queue):
        queue_number = get_queue_number(session_key)
        queue_list.append({
            'position': idx + 1,
            'queue_number': queue_number,
            'session_key': session_key
        })
    
    context = {
        'specialty': specialty,
        'patient_queue': queue_list,
        'queue_count': len(queue_list)
    }
    return render(request, 'core/doctor_dashboard.html', context)

def doctor_accept_patient_view(request, specialty):
    if request.method == 'POST':
        removed_session = remove_from_queue(specialty)
        if removed_session:
            broadcast_queue_update(specialty)
    return redirect('doctor_dashboard', specialty=specialty)

def broadcast_queue_update(specialty):
    channel_layer = get_channel_layer()
    room_group_name = f'queue_{specialty.replace(" ", "_")}'
    
    queue = PATIENT_QUEUES.get(specialty, [])
    for idx, session_key in enumerate(queue):
        async_to_sync(channel_layer.group_send)(
            room_group_name,
            {
                'type': 'queue_update',
                'position': idx + 1,
                'total': len(queue),
                'queue_number': get_queue_number(session_key),
                'session_key': session_key
            }
        )

GRAPH_CACHE = None

def get_graph():
    global GRAPH_CACHE
    if GRAPH_CACHE is None:
        print("--- Caching road network graph for Bengaluru. This will happen only once. ---")
        start_time = time.time()
        GRAPH_CACHE = ox.graph_from_place('Bengaluru, India', network_type='drive')
        print(f"--- Graph cached in {time.time() - start_time:.2f} seconds. ---")
    return GRAPH_CACHE

def dijkstra_locator_view(request):
    return render(request, 'core/dijkstra_locator.html')

PHARMACY_CACHE = None

def find_pharmacies_dijkstra_api(request):
    global PHARMACY_CACHE
    lat_str = request.GET.get('lat')
    lon_str = request.GET.get('lon')

    if not lat_str or not lon_str:
        return JsonResponse({'error': 'Latitude and longitude are required'}, status=400)

    try:
        user_point = (float(lat_str), float(lon_str))
        G = get_graph()
        
        if PHARMACY_CACHE is None:
            print("--- Caching all pharmacies in Bengaluru. This happens once. ---")
            start_time = time.time()
            
            nodes_data = list(G.nodes(data=True))
            lats = [data['y'] for _, data in nodes_data]
            lons = [data['x'] for _, data in nodes_data]
            
            north, south = max(lats), min(lats)
            east, west = max(lons), min(lons)
            
            tags = {"amenity": "pharmacy"}
            gdf = ox.features_from_bbox((north, south, east, west), tags)
            gdf = gdf[gdf.geom_type == 'Point']
            
            PHARMACY_CACHE = gdf
            print(f"--- Cached {len(gdf)} pharmacies in {time.time() - start_time:.2f} seconds. ---")
        
        gdf = PHARMACY_CACHE
        
        if gdf.empty:
            return JsonResponse({'pharmacies': []})
        
        user_node = ox.nearest_nodes(G, user_point[1], user_point[0])
        
        results = []
        for idx, row in gdf.iterrows():
            try:
                pharmacy_node = ox.nearest_nodes(G, row.geometry.x, row.geometry.y)
                
                distance = nx.dijkstra_path_length(
                    G, 
                    source=user_node, 
                    target=pharmacy_node, 
                    weight='length'
                )
                
                name = row.get('name', 'Unnamed Pharmacy')
                if not isinstance(name, str):
                    name = 'Unnamed Pharmacy'
                    
                results.append({
                    'name': name,
                    'vicinity': f"{distance:.0f} meters away",
                    'distance_numeric': distance
                })
            except (nx.NetworkXNoPath, KeyError, Exception):
                continue
        
        sorted_results = sorted(results, key=lambda p: p['distance_numeric'])
        final_results = [{'name': r['name'], 'vicinity': r['vicinity']} for r in sorted_results[:5]]
        
        return JsonResponse({'pharmacies': final_results})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f"An internal error occurred: {str(e)}"}, status=500)

from collections import deque
import random

PATIENT_QUEUES = {
    'Cardiology': deque(),
    'Neurology': deque(),
    'General Physician': deque(),
}

QUEUE_NUMBERS = {}

def generate_queue_number():
    return f"P-{random.randint(1000, 9999)}"

def add_to_queue(specialty, session_key):
    if session_key not in QUEUE_NUMBERS:
        queue_number = generate_queue_number()
        while queue_number in QUEUE_NUMBERS.values():
            queue_number = generate_queue_number()
        QUEUE_NUMBERS[session_key] = queue_number
    
    queue = PATIENT_QUEUES.get(specialty)
    if queue is not None and session_key not in queue:
        queue.append(session_key)
        return QUEUE_NUMBERS[session_key]
    return QUEUE_NUMBERS.get(session_key)

def get_queue_position(specialty, session_key):
    queue = PATIENT_QUEUES.get(specialty)
    if queue and session_key in queue:
        return list(queue).index(session_key) + 1
    return -1

def get_queue_count(specialty):
    queue = PATIENT_QUEUES.get(specialty)
    return len(queue) if queue else 0

def remove_from_queue(specialty):
    queue = PATIENT_QUEUES.get(specialty)
    if queue:
        session_key = queue.popleft()
        return session_key
    return None

def get_queue_number(session_key):
    return QUEUE_NUMBERS.get(session_key)

def is_in_any_queue(session_key):
    return any(session_key in q for q in PATIENT_QUEUES.values())

def assign_specialty(symptoms):
    symptom_map = {
        'Chest Pain': 'Cardiology',
        'Shortness of Breath': 'Cardiology',
        'Headache': 'Neurology',
        'Dizziness': 'Neurology',
        'Fever': 'General Physician',
        'Cough': 'General Physician',
    }
    for symptom in symptoms:
        if symptom in symptom_map:
            return symptom_map[symptom]
    return 'General Physician'

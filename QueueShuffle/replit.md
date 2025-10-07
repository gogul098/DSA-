# HealthNav - Real-Time Telehealth Queue System

## Overview

HealthNav is a Django-based telehealth queue management system that connects patients with doctors based on their symptoms. The application uses WebSocket technology for real-time updates and assigns randomized queue numbers to patients for privacy and reliability.

The system provides automatic triage that routes patients to Cardiology, Neurology, or General Physician specialties based on their reported symptoms, with instant queue position updates delivered via WebSockets.

## Recent Changes (October 6, 2025)

- Implemented Django Channels for WebSocket-based real-time communication
- Added randomized patient queue numbers (P-1000 to P-9999) instead of sequential positions
- Created WebSocket consumer for bi-directional queue updates
- Built patient status page with automatic position updates
- Created doctor dashboard with live queue monitoring
- Configured Redis as the channel layer backend
- Set up ASGI server with daphne for WebSocket support
- Added Dijkstra-based pharmacy locator with unlimited distance coverage
- Implemented dual caching system (road network + pharmacy locations) for optimal performance

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Template-Based UI**: The application uses Django's template system with server-side rendering. All views are traditional HTML templates with embedded CSS and JavaScript for WebSocket connections.

**Real-Time Updates via WebSockets**: Both patient queue positions and doctor dashboards update in real-time using Django Channels WebSocket connections. Each specialty has its own WebSocket room group, allowing targeted updates to patients and doctors monitoring specific queues.

**Randomized Queue Numbers**: Each patient receives a unique randomized queue number (format: P-XXXX where XXXX is 1000-9999) instead of showing their sequential position. This provides privacy and a more professional queue experience.

**Rationale**: Server-side rendering was chosen for simplicity and faster initial development. WebSockets provide the real-time experience needed for queue management without requiring a full SPA architecture. Randomized numbers prevent patients from knowing exactly how many people are ahead of them while still providing queue status.

### Backend Architecture

**Django with Channels**: The application runs as a Django project with Django Channels extension for WebSocket support. The core app contains all business logic.

**In-Memory Queue Management**: Patient queues are stored in Python `deque` objects (double-ended queues) held in memory. Each specialty maintains its own queue, and session keys are used to track individual patients.

**Session-Based Patient Tracking**: Django sessions identify and track patients without requiring authentication or user accounts. The session key serves as the unique patient identifier and is mapped to a randomized queue number.

**Queue Number Generation**: A centralized dictionary (`QUEUE_NUMBERS`) maps session keys to randomized queue numbers (P-1000 to P-9999). The system ensures uniqueness by regenerating numbers if duplicates are detected.

**Symptom-to-Specialty Mapping**: A hardcoded dictionary maps symptoms to medical specialties (e.g., "Chest Pain" → Cardiology). This decision tree approach provides predictable routing.

**Real-Time Broadcasting**: When queue changes occur (patient joins or doctor accepts), the system broadcasts updates to all connected WebSocket clients in that specialty's room group.

**Rationale**: In-memory queues avoid database complexity for a prototype system. Session-based tracking eliminates user registration friction. Randomized queue numbers provide privacy while maintaining queue order integrity.

**Pros**: Fast development, instant real-time updates, no database schema for queues, simple deployment
**Cons**: Queue data lost on server restart, limited to single-server deployments (can be addressed with Redis-backed queues), no historical data

### Asynchronous Communication Layer

**Django Channels with ASGI**: The application uses Django Channels to handle WebSocket connections alongside traditional HTTP requests. The ASGI configuration routes HTTP traffic to Django and WebSocket traffic to Channels consumers.

**Redis Channel Layer**: Redis serves as the backing store for the channel layer, enabling message passing between different parts of the application and supporting potential multi-process deployments.

**WebSocket Consumer**: The `QueueConsumer` handles WebSocket connections, manages room group membership, and broadcasts queue updates to all connected clients in real-time.

**Rationale**: Channels extends Django's request-response model to handle long-lived WebSocket connections, enabling real-time features while maintaining Django's familiar patterns. Redis provides a production-ready channel layer backend.

### Data Flow Architecture

1. **Patient Journey**: Home → Symptom Form → Specialty Assignment → Queue Addition (with randomized number) → Real-time Status Updates via WebSocket
2. **Doctor Journey**: Home → Specialty Selection → Dashboard with Live Queue → Accept Next Patient (triggers broadcast)
3. **Real-time Sync**: When doctors accept patients or new patients join, queue updates are broadcast instantly to all connected clients via WebSockets

**Key Design Decision**: The queue position is calculated on-demand, but queue numbers are permanent per session. Each WebSocket message includes both the position and the queue number, allowing patients to see their randomized identifier while receiving position updates.

### URL Routing Structure

- `/` - Role selection (patient/doctor)
- `/patient/form/` - Symptom submission
- `/patient/submit/` - Form processing and queue addition
- `/patient/status/<specialty>/` - Queue status with WebSocket connection
- `/doctor/select/` - Specialty selection
- `/doctor/dashboard/<specialty>/` - Queue management interface
- `/doctor/accept/<specialty>/` - Accept next patient endpoint
- `/ws/queue/<specialty>/` - WebSocket endpoint for real-time updates

## External Dependencies

### Core Framework
- **Django 5.2.7**: Web framework providing ORM, templating, sessions, and URL routing
- **Django Channels 4.3.1**: Extends Django to handle WebSockets and asynchronous protocols via ASGI
- **Daphne 4.2.1**: ASGI server for running Django Channels applications
- **channels-redis 4.3.0**: Redis-backed channel layer for Django Channels

### Infrastructure
- **Redis 6.4.0**: In-memory data store used as the channel layer backend for WebSocket message routing
- **Python 3.11**: Runtime environment

### Python Libraries
- **osmnx 2.0.6**: OpenStreetMap network analysis library (for future pharmacy locator features)
- **networkx 3.5**: Graph/network analysis library (for future routing features)

### Database
- **SQLite**: Used only for Django sessions; no custom models persist queue data

### Key Features
- **Real-time Communication**: WebSocket-based instant updates for both patients and doctors
- **Randomized Queue Numbers**: Privacy-focused P-XXXX numbering system
- **No Authentication Required**: Anonymous session-based tracking
- **In-Memory Queue State**: Fast, simple queue management without database overhead
- **Pharmacy Locator**: Dijkstra's algorithm-based pharmacy finder with no distance limits
- **Dual Caching System**: Road network and pharmacy data cached for fast subsequent queries

**Future Considerations**: 
- Persist queues in Redis lists for restart resilience and multi-instance support
- Add queue number recycling when sessions expire
- Implement integration tests for queue operations
- Add estimated wait time calculations
- Create priority queue system for urgent cases

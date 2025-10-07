#!/bin/bash

redis-server --daemonize yes --port 6379

sleep 2

daphne -b 0.0.0.0 -p 5000 healthnav.asgi:application

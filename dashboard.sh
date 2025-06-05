#!/bin/zsh

# Kill any process using backend port 8000
lsof -ti :8000 | xargs -r kill -9

# Kill any process using frontend port 8081
lsof -ti :8081 | xargs -r kill -9

# Start the FastAPI backend (RPMEE simulation engine) on port 8000
uvicorn src.simulation:app --reload --host 127.0.0.1 --port 8000 &

# Wait briefly to ensure backend starts first
sleep 2

# Change directory to frontend folder and start HTTP server on port 8081
cd /Users/clevelandlewis/Library/Mobile\ Documents/com~apple~CloudDocs/Inbox/Zips/RPMEE_v1.1.0_Simulation/frontend || exit
python3 -m http.server 8081

# Automatically open the app page in the default browser
open "http://localhost:8081/dashboard.html"

# When done, you may need to manually kill the background backend with:
# kill %1
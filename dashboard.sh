#!/bin/zsh

# --- Step 1: (One time) install dependencies ---
pip install uvicorn transitions fastapi

# --- Step 2: Start backend server in the background ---
uvicorn src.simulation:app --reload &

# --- Step 3: Wait a moment to ensure the server starts ---
sleep 2

# --- Step 4: Open the frontend UI in the default browser ---
open frontend/dashboard.html

# (Optional) Show a message to kill the background server later
echo "When done, use 'kill %1' to stop the backend server if needed."
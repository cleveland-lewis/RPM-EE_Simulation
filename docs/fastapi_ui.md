# FastAPI and UI

This document outlines the plan for building a minimal FastAPI and UI surface for RPM-EE.

## FastAPI

A FastAPI application will be created to expose an API for running simulations.

### Endpoints

-   `POST /simulations`: Create and run a new simulation.
-   `GET /simulations/{simulation_id}`: Get the status and results of a simulation.

## UI

A simple web-based UI will be built to interact with the FastAPI.

### Features

-   A form for configuring and running a new simulation.
-   A page for viewing the results of a simulation.

## Technology Stack

-   **Backend**: FastAPI
-   **Frontend**: Streamlit or a similar framework.

# PathPilot Frontend

The frontend for PathPilot is a React application built with Vite. It features an interactive map for navigation and a 3D viewer for inspecting models.

## Installation

1.  Navigate to the `web` directory:
    ```bash
    cd web
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

## Running the Application

Start the development server:

```bash
npm run dev
```

The application will be accessible at `http://localhost:5173`.

## Features

### 2D Map Mode
*   Interactive OpenStreetMap view.
*   Click to set Start and End points.
*   Calculate and display shortest paths.

### 3D View Mode
*   Visualize 3D Gaussian Splat models.
*   Upload video footage to generate new 3D models via the backend pipeline.
*   Interactive controls (Rotate, Pan, Zoom).

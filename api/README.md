# PathPilot Backend

The backend for PathPilot is built with FastAPI. It provides endpoints for 2D pathfinding using OpenStreetMap data and a pipeline for converting videos into 3D Gaussian Splat models.

## Installation

1.  Navigate to the `api` directory:
    ```bash
    cd api
    ```

2.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    ```

3.  Activate the virtual environment:
    *   **macOS/Linux:** `source venv/bin/activate`
    *   **Windows:** `venv\Scripts\activate`

4.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

Start the server using `uvicorn`:

```bash
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### 2D Navigation

*   `GET /`: Health check.
*   `GET /graph/bounds`: Returns the latitude/longitude bounds of the loaded map.
*   `POST /route`: Calculates a route between two points.

### 3D Converter

*   `POST /upload`: Upload a video file (.mp4) for processing.
*   `POST /process`: Trigger the 3D conversion pipeline for an uploaded video.

## 3D Module

The 3D processing logic is located in the `converter` package. See `converter/README.md` for more details.

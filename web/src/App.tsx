import { useState, useCallback, Suspense, lazy } from 'react';
import CampusMap, { type RouteResponse } from './components/CampusMap';
import TrafficControl from './components/TrafficControl';
import type { LatLngTuple } from 'leaflet';
import './index.css';

// Lazy load 3D component
const Campus3D = lazy(() => import('./components/Campus3D'));

// Existing interfaces...
interface RouteRequest {
  start_lat: number;
  start_lon: number;
  end_lat: number;
  end_lon: number;
  weight: string;
}

interface Point {
  lat: number;
  lng: number;
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);
  const [points, setPoints] = useState<{ start: Point | null; end: Point | null }>({ start: null, end: null });
  const [darkMode, setDarkMode] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');

  // Traffic State
  const [trafficIntensity, setTrafficIntensity] = useState<'low' | 'medium' | 'high'>('low');
  const [isSimulatingTraffic, setIsSimulatingTraffic] = useState(false);

  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string>("");



  const handlePointsUpdate = useCallback((start: LatLngTuple | null, end: LatLngTuple | null) => {
    // Convert [lat, lon] tuple to Point object {lat, lng} for consistency if needed, 
    // or just change state to use tuples. Let's switch state to use Points to match existing access.

    const startPoint = start ? { lat: start[0], lng: start[1] } : null;
    const endPoint = end ? { lat: end[0], lng: end[1] } : null;

    setPoints({ start: startPoint, end: endPoint });
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    if (!darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  // Traffic Handler
  const handleTrafficChange = async (intensity: 'low' | 'medium' | 'high') => {
    setTrafficIntensity(intensity);
    setIsSimulatingTraffic(true);
    try {
      await fetch(`${API_URL}/traffic/simulate?intensity=${intensity}`, { method: 'POST' });
      // If we have a route, re-calculate it to show impact
      if (points.start && points.end) {
        handleCalculateRoute();
      }
    } catch (error) {
      console.error("Traffic simulation failed:", error);
    } finally {
      setIsSimulatingTraffic(false);
    }
  };

  const handleCalculateRoute = async () => {
    if (!points.start || !points.end) {
      alert("Please select both start and end points on the map");
      return;
    }

    try {
      // Use time-based weighting if traffic is significant (medium/high), 
      // or just to respect the traffic simulation in general.
      // Actually, we should always use 'weight_time' if we want to see traffic effects.
      // But maybe 'length' is default? Let's switch to 'weight_time' (our custom traffic weight)
      // when traffic controls are active or just always for "Smart Routing".
      const weightType = 'weight_time'; // Always use our smart weight for now

      const req: RouteRequest = {
        start_lat: points.start.lat,
        start_lon: points.start.lng,
        end_lat: points.end.lat,
        end_lon: points.end.lng,
        weight: weightType
      };

      const res = await fetch(`${API_URL}/route`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req)
      });

      if (!res.ok) throw new Error("Route calculation failed");
      const data = await res.json();
      setRouteData(data);
    } catch (err) {
      console.error(err);
      alert("Failed to calculate route");
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    setUploadStatus("Uploading video...");

    try {
      // 1. Upload
      const formData = new FormData();
      formData.append("file", file);

      const uploadRes = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData
      });

      if (!uploadRes.ok) throw new Error("Upload failed");
      const uploadData = await uploadRes.json();

      // 2. Process
      setUploadStatus("Processing Splat (this may take a moment)...");
      const processRes = await fetch(`${API_URL}/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_filename: uploadData.filename })
      });

      if (!processRes.ok) throw new Error("Processing failed");
      const processData = await processRes.json();

      setModelUrl(`${API_URL}/models/${processData.model_url.split('/').pop()}`);
      setUploadStatus("Ready!");

    } catch (err: any) {
      console.error(err);
      setUploadStatus(`Error: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className={`dashboard-container ${darkMode ? 'dark-mode' : ''}`}>
      {/* Header */}
      <header className="header">
        <div className="flex items-center gap-2 logo-container">
          {/* Logo Icon */}
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="logo-icon">
            <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon>
            <line x1="8" y1="2" x2="8" y2="18"></line>
            <line x1="16" y1="6" x2="16" y2="22"></line>
          </svg>
          <h1>PathPilot</h1>
          <span className="badge">
            Campus Pilot
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="location-text">
            Gandhinagar
          </div>
          {/* Settings Wheel */}
          <div className="relative setting-container">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="settings-btn"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={showSettings ? "animate-spin-slow" : ""}>
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </button>
            {/* Settings Dropdown */}
            {showSettings && (
              <div className="settings-dropdown">
                <div className="settings-title">Settings</div>
                <button
                  onClick={toggleDarkMode}
                  className="theme-toggle-btn"
                >
                  {darkMode ? (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                      Light Mode
                    </>
                  ) : (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
                      Dark Mode
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <main className="main-content">

        {/* Sidebar Controls */}
        <aside className="sidebar">
          <h2 className="sidebar-title">Navigation</h2>

          {/* View Mode Toggle */}
          <div className="view-mode-toggle">
            <button
              onClick={() => setViewMode('2d')}
              className={`toggle-btn ${viewMode === '2d' ? 'active' : ''}`}
            >
              2D Map
            </button>
            <button
              onClick={() => setViewMode('3d')}
              className={`toggle-btn ${viewMode === '3d' ? 'active' : ''}`}
            >
              3D View
            </button>
          </div>

          {viewMode === '3d' && (
            <div className="stat-card animate-fade-in card-border">
              <h3 className="card-title">
                3D Scanner
              </h3>
              <div className="upload-section">
                <input
                  type="file"
                  accept="video/mp4,video/quicktime"
                  onChange={handleFileUpload}
                  disabled={isProcessing}
                  className="file-input"
                />
              </div>
              {isProcessing && (
                <div className="processing-status">
                  <span className="animate-spin-slow spinner">⟳</span>
                  {uploadStatus}
                </div>
              )}
              {uploadStatus && !isProcessing && (
                <div className="success-status">
                  ✓ {uploadStatus}
                </div>
              )}
            </div>
          )}

          {viewMode === '2d' && (
            <div className="status-section">
              <div className="status-item">
                <span className={`status-dot ${points.start ? 'status-active-green' : 'status-inactive'}`}></span>
                <span>Start Point</span>
              </div>
              <div className="status-item">
                <span className={`status-dot ${points.end ? 'status-active-red' : 'status-inactive'}`}></span>
                <span>End Point</span>
              </div>

              <p className="instruction-text">
                {!points.start ? "Click map to set Start." : !points.end ? "Click map to set End." : "Calculating route..."}
              </p>
            </div>
          )}

          {viewMode === '2d' && routeData ? (
            <div className="stat-card animate-fade-in">
              <h3 className="card-title">
                Route Details
              </h3>
              <div className="route-distance">
                {(routeData.total_distance_meters / 1000).toFixed(2)} <span className="unit">km</span>
              </div>
              <div className="route-nodes">
                <span className="font-semibold">{routeData.nodes_visited}</span> graph nodes analyzed
              </div>
              <div className="route-alternatives" style={{ marginTop: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <span className="font-semibold">{routeData.alternatives?.length || 1}</span> routes found
              </div>
            </div>
          ) : null}

          {viewMode === '2d' && !routeData && (
            <div className="empty-state">
              Select points to view stats
            </div>
          )}

          <div className="mt-auto">
            {routeData && routeData.instructions && routeData.instructions.length > 0 ? (
              <div className="card" style={{ marginTop: '1rem', maxHeight: '30vh', overflowY: 'auto' }}>
                <h3 className="card-title">Turn-by-Turn</h3>
                <ul className="instructions-list">
                  {routeData.instructions.map((step, idx) => (
                    <li key={idx} style={{ padding: '4px 0', borderBottom: '1px solid var(--border-color)' }}>
                      {idx + 1}. {step}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <>
                <h3 className="instructions-title">Instructions</h3>
                <ul className="instructions-list">
                  {viewMode === '2d' ? (
                    <>
                      <li><b>Left Click</b>: Set Points</li>
                      <li><b>Double Click</b>: Clear Map</li>
                    </>
                  ) : (
                    <>
                      <li>Upload an .mp4 video</li>
                      <li>Wait for processing</li>
                    </>
                  )}
                </ul>
              </>
            )}
          </div>

        </aside>

        {/* Map Container */}
        <section className="map-wrapper relative-pos">
          {viewMode === '2d' ? (
            <>
              <CampusMap
                onRouteUpdate={setRouteData}
                onPointsUpdate={handlePointsUpdate}
                darkMode={darkMode}
              />
              <div style={{ position: 'absolute', top: '10px', left: '60px', zIndex: 1000, width: '300px' }}>
                <TrafficControl
                  intensity={trafficIntensity}
                  onIntensityChange={handleTrafficChange}
                  isSimulating={isSimulatingTraffic}
                />
              </div>
            </>
          ) : (
            <Suspense fallback={<div className="loading-3d">Loading 3D Engine...</div>}>
              <Campus3D modelUrl={modelUrl || undefined} />
            </Suspense>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;

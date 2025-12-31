import { useState, useCallback, Suspense, lazy } from 'react';
import CampusMap from './components/CampusMap';
import type { RouteResponse } from './components/CampusMap';
import './index.css';

// Lazy load 3D component
const Campus3D = lazy(() => import('./components/Campus3D'));

function App() {
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);
  const [points, setPoints] = useState({ start: false, end: false });
  const [darkMode, setDarkMode] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');


  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string>("");

  const handlePointsUpdate = useCallback((start: boolean, end: boolean) => {
    setPoints({ start, end });
  }, []);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
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

      const uploadRes = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData
      });

      if (!uploadRes.ok) throw new Error("Upload failed");
      const uploadData = await uploadRes.json();

      // 2. Process
      setUploadStatus("Processing Splat (this may take a moment)...");
      const processRes = await fetch("http://localhost:8000/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_filename: uploadData.filename })
      });

      if (!processRes.ok) throw new Error("Processing failed");
      const processData = await processRes.json();

      setModelUrl(processData.model_url);
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
        <div className="flex items-center gap-2">
          {/* Logo Icon */}
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--accent-color)' }}>
            <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon>
            <line x1="8" y1="2" x2="8" y2="18"></line>
            <line x1="16" y1="6" x2="16" y2="22"></line>
          </svg>
          <h1>PathPilot</h1>
          <span style={{ fontSize: '0.8rem', background: 'var(--accent-bg)', color: 'var(--accent-color)', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
            Campus Pilot
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Gandhinagar
          </div>
          {/* Settings Wheel */}
          <div className="relative" style={{ position: 'relative' }}>
            <button
              onClick={() => setShowSettings(!showSettings)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-primary)', padding: '4px' }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={showSettings ? "animate-spin-slow" : ""}>
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
              </svg>
            </button>
            {/* Settings Dropdown */}
            {showSettings && (
              <div style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: '0.5rem',
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                padding: '0.5rem',
                zIndex: 50,
                minWidth: '150px'
              }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', padding: '0.5rem' }}>Settings</div>
                <button
                  onClick={toggleDarkMode}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    width: '100%',
                    padding: '0.5rem',
                    fontSize: '0.9rem',
                    color: 'var(--text-primary)',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
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
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem', color: 'var(--text-primary)' }}>Navigation</h2>

          {/* View Mode Toggle */}
          <div style={{ display: 'flex', background: 'var(--bg-card)', padding: '4px', borderRadius: '8px', marginBottom: '1.5rem', border: '1px solid var(--border-color)' }}>
            <button
              onClick={() => setViewMode('2d')}
              style={{
                flex: 1,
                padding: '6px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: 500,
                background: viewMode === '2d' ? 'var(--accent-bg)' : 'transparent',
                color: viewMode === '2d' ? 'var(--accent-color)' : 'var(--text-secondary)',
                transition: 'all 0.2s'
              }}
            >
              2D Map
            </button>
            <button
              onClick={() => setViewMode('3d')}
              style={{
                flex: 1,
                padding: '6px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: 500,
                background: viewMode === '3d' ? 'var(--accent-bg)' : 'transparent',
                color: viewMode === '3d' ? 'var(--accent-color)' : 'var(--text-secondary)',
                transition: 'all 0.2s'
              }}
            >
              3D View
            </button>
          </div>

          {viewMode === '3d' && (
            <div className="stat-card animate-fade-in" style={{ marginBottom: '1.5rem', borderColor: 'var(--accent-color)' }}>
              <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                3D Scanner
              </h3>
              <div style={{ padding: '0.5rem 0' }}>
                <input
                  type="file"
                  accept="video/mp4,video/quicktime"
                  onChange={handleFileUpload}
                  disabled={isProcessing}
                  style={{ fontSize: '0.8rem', width: '100%', color: 'var(--text-primary)' }}
                />
              </div>
              {isProcessing && (
                <div style={{ fontSize: '0.8rem', color: 'var(--accent-color)', fontWeight: 500 }}>
                  <span className="animate-spin-slow" style={{ display: 'inline-block', marginRight: '5px' }}>⟳</span>
                  {uploadStatus}
                </div>
              )}
              {uploadStatus && !isProcessing && (
                <div style={{ fontSize: '0.8rem', color: '#10b981', marginTop: '5px' }}>
                  ✓ {uploadStatus}
                </div>
              )}
            </div>
          )}

          {viewMode === '2d' && (
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
                <span className={`status-dot ${points.start ? 'status-active-green' : 'status-inactive'}`}></span>
                <span>Start Point</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-primary)' }}>
                <span className={`status-dot ${points.end ? 'status-active-red' : 'status-inactive'}`}></span>
                <span>End Point</span>
              </div>

              <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                {!points.start ? "Click map to set Start." : !points.end ? "Click map to set End." : "Calculating route..."}
              </p>
            </div>
          )}

          {viewMode === '2d' && routeData ? (
            <div className="stat-card animate-fade-in">
              <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Route Details
              </h3>
              <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                {(routeData.total_distance_meters / 1000).toFixed(2)} <span style={{ fontSize: '1rem', fontWeight: 400 }}>km</span>
              </div>
              <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <span style={{ fontWeight: 600 }}>{routeData.nodes_visited}</span> graph nodes analyzed
              </div>
            </div>
          ) : null}

          {viewMode === '2d' && !routeData && (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)', border: '2px dashed var(--border-color)', borderRadius: '8px' }}>
              Select points to view stats
            </div>
          )}

          <div style={{ marginTop: 'auto' }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 0, marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Instructions</h3>
            <ul style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', paddingLeft: '1.2rem' }}>
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
          </div>
        </aside>

        {/* Map Container */}
        <section className="map-wrapper" style={{ position: 'relative' }}>
          {viewMode === '2d' ? (
            <CampusMap
              onRouteUpdate={setRouteData}
              onPointsUpdate={handlePointsUpdate}
              darkMode={darkMode}
            />
          ) : (
            <Suspense fallback={<div className="flex items-center justify-center h-full text-white bg-black">Loading 3D Engine...</div>}>
              <Campus3D modelUrl={modelUrl || undefined} />
            </Suspense>
          )}
        </section>

      </main>
    </div>
  );
}

export default App;

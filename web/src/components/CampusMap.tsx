import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, useMapEvents, CircleMarker, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { LatLngTuple } from 'leaflet';

// Map Styles
const MAP_URL_LIGHT = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
const MAP_URL_DARK = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

interface Bounds {
    min_lat: number;
    max_lat: number;
    min_lon: number;
    max_lon: number;
    center: { lat: number; lon: number };
}

export interface RouteResponse {
    path_coords: [number, number][];
    total_distance_meters: number;
    nodes_visited: number;
    instructions?: string[];
    alternatives?: {
        path_coords: [number, number][];
        distance_meters: number;
        type: string;
        instructions: string[];
    }[];
}

interface CampusMapProps {
    onRouteUpdate?: (data: RouteResponse | null) => void;
    onPointsUpdate?: (start: LatLngTuple | null, end: LatLngTuple | null) => void;
    darkMode?: boolean;
    path?: [number, number][]; // Prop to receive path from parent if needed, though currently it calls onRouteUpdate
}

// Sub-component to handle map clicks
function LocationSelector({
    onSelect,
    onReset
}: {
    onSelect: (lat: number, lon: number) => void;
    onReset: () => void;
}) {
    useMapEvents({
        click(e) {
            onSelect(e.latlng.lat, e.latlng.lng);
        },
        dblclick() {
            onReset();
        }
    });
    return null;
}

export default function CampusMap({ onRouteUpdate, onPointsUpdate, darkMode = false }: CampusMapProps) {
    const [bounds, setBounds] = useState<Bounds | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Routing State
    const [startPoint, setStartPoint] = useState<LatLngTuple | null>(null);
    const [endPoint, setEndPoint] = useState<LatLngTuple | null>(null);
    const [route, setRoute] = useState<RouteResponse | null>(null);
    const [selectedRouteIdx, setSelectedRouteIdx] = useState<number>(0);

    useEffect(() => {
        fetch('http://localhost:8000/graph/bounds')
            .then(res => {
                if (!res.ok) throw new Error("Failed to load map data");
                return res.json();
            })
            .then(data => {
                setBounds(data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setError("Backend connection failed.");
                setLoading(false);
            });
    }, []);

    // Notify parent of point/route changes
    useEffect(() => {
        if (onPointsUpdate) {
            onPointsUpdate(startPoint, endPoint);
        }
    }, [startPoint, endPoint, onPointsUpdate]);

    useEffect(() => {
        if (onRouteUpdate) {
            onRouteUpdate(route);
        }
    }, [route, onRouteUpdate]);

    const handleMapClick = async (lat: number, lon: number) => {
        if (!startPoint) {
            setStartPoint([lat, lon]);
            setRoute(null);
            setSelectedRouteIdx(0);
        } else if (!endPoint) {
            setEndPoint([lat, lon]);
            try {
                // Default to first calc
                await calculateRoute([lat, lon]);
            } catch (error) {
                console.error(error);
                alert("Failed to find path. Try points closer to roads.");
                setEndPoint(null);
            }
        } else {
            setStartPoint([lat, lon]);
            setEndPoint(null);
            setRoute(null);
            setSelectedRouteIdx(0);
        }
    };

    const calculateRoute = async (end: LatLngTuple) => {
        if (!startPoint) return;
        const res = await fetch('http://localhost:8000/route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_lat: startPoint[0],
                start_lon: startPoint[1],
                end_lat: end[0],
                end_lon: end[1]
            })
        });
        if (!res.ok) throw new Error("Pathfinding failed");
        const data = await res.json();
        setRoute(data);
    };

    const resetMap = () => {
        setStartPoint(null);
        setEndPoint(null);
        setRoute(null);
        setSelectedRouteIdx(0);
    };

    const ROUTE_COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b']; // Blue, Green, Violet, Amber

    // Helper to get color
    const getRouteColor = (index: number) => ROUTE_COLORS[index % ROUTE_COLORS.length];

    if (loading) return <div className="flex items-center justify-center h-full bg-gray-100">Loading Map...</div>;
    if (error) return <div className="flex items-center justify-center h-full text-red-500 bg-gray-100">{error}</div>;
    if (!bounds) return null;

    const center: LatLngTuple = [bounds.center.lat, bounds.center.lon];
    const alternatives = route?.alternatives || [];

    return (
        <div style={{ height: "100%", width: "100%", position: "relative", borderRadius: "12px", overflow: "hidden" }}>
            <MapContainer
                center={center}
                zoom={15}
                doubleClickZoom={false}
                style={{ height: "100%", width: "100%" }}
                maxBounds={[
                    [bounds.min_lat - 0.05, bounds.min_lon - 0.05],
                    [bounds.max_lat + 0.05, bounds.max_lon + 0.05]
                ]}
            >
                <TileLayer url={darkMode ? MAP_URL_DARK : MAP_URL_LIGHT} attribution={ATTRIBUTION} />
                <LocationSelector onSelect={handleMapClick} onReset={resetMap} />

                {startPoint && <CircleMarker center={startPoint} radius={8} pathOptions={{ color: 'green' }} />}
                {endPoint && <CircleMarker center={endPoint} radius={8} pathOptions={{ color: 'red' }} />}

                {/* Render All Routes */}
                {alternatives.map((alt, idx) => {
                    const isSelected = idx === selectedRouteIdx;
                    return (
                        <Polyline
                            key={`route-${idx}`}
                            positions={alt.path_coords}
                            pathOptions={{
                                color: getRouteColor(idx),
                                weight: isSelected ? 6 : 4,
                                opacity: isSelected ? 1.0 : 0.5,
                                dashArray: isSelected ? undefined : '5, 10'
                            }}
                            eventHandlers={{
                                click: () => {
                                    setSelectedRouteIdx(idx);
                                    if (route) {
                                        const newRoute = { ...route, ...alt, instructions: alt.instructions };
                                        setRoute(newRoute);
                                    }
                                    // Bring to front? Leaflet handles z-index by order usually, 
                                    // but we might need to re-sort specific one to bottom/top if overlapping hard.
                                    // For now, opacity helps.
                                }
                            }}
                        />
                    );
                })}
            </MapContainer>

            {alternatives.length > 1 && (
                <div style={{ position: 'absolute', bottom: '20px', left: '20px', zIndex: 1000, background: 'var(--bg-card)', padding: '10px', borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 'bold', marginBottom: '5px' }}>Alternative Routes</div>
                    <div style={{ display: 'flex', gap: '5px' }}>
                        {alternatives.map((alt, idx) => (
                            <button
                                key={idx}
                                onClick={() => {
                                    setSelectedRouteIdx(idx);
                                    if (route) {
                                        const newRoute = { ...route, ...alt, instructions: alt.instructions };
                                        setRoute(newRoute);
                                    }
                                }}
                                className={`btn ${selectedRouteIdx === idx ? 'btn-primary' : 'btn-secondary'}`}
                                style={{
                                    padding: '4px 8px',
                                    fontSize: '0.8rem',
                                    borderLeft: `4px solid ${getRouteColor(idx)}`
                                }}
                            >
                                {alt.type || `Route ${idx + 1}`}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

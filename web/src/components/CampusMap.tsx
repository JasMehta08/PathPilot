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
}

interface CampusMapProps {
    onRouteUpdate?: (data: RouteResponse | null) => void;
    onPointsUpdate?: (start: boolean, end: boolean) => void;
    darkMode?: boolean;
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
            onPointsUpdate(!!startPoint, !!endPoint);
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
        } else if (!endPoint) {
            setEndPoint([lat, lon]);
            try {
                const res = await fetch('http://localhost:8000/route', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        start_lat: startPoint[0],
                        start_lon: startPoint[1],
                        end_lat: lat,
                        end_lon: lon
                    })
                });
                if (!res.ok) throw new Error("Pathfinding failed");
                const data = await res.json();
                setRoute(data);
            } catch (error) {
                console.error(error);
                alert("Failed to find path. Try points closer to roads.");
                setEndPoint(null);
            }
        } else {
            setStartPoint([lat, lon]);
            setEndPoint(null);
            setRoute(null);
        }
    };

    const resetMap = () => {
        setStartPoint(null);
        setEndPoint(null);
        setRoute(null);
    };

    if (loading) return <div className="flex items-center justify-center h-full bg-gray-100">Loading Map...</div>;
    if (error) return <div className="flex items-center justify-center h-full text-red-500 bg-gray-100">{error}</div>;
    if (!bounds) return null;

    const center: LatLngTuple = [bounds.center.lat, bounds.center.lon];

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
                {route && <Polyline positions={route.path_coords} pathOptions={{ color: 'blue', weight: 6 }} />}
            </MapContainer>
        </div>
    );
}

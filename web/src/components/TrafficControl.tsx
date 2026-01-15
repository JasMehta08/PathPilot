import React from 'react';

interface TrafficControlProps {
    intensity: 'low' | 'medium' | 'high';
    onIntensityChange: (intensity: 'low' | 'medium' | 'high') => void;
    isSimulating: boolean;
}

const TrafficControl: React.FC<TrafficControlProps> = ({ intensity, onIntensityChange, isSimulating }) => {
    return (
        <div className="card" style={{ marginTop: '1rem' }}>
            <h3 style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                🚦 Traffic Conditions
                {isSimulating && <span className="status-dot status-processing" title="Updating..."></span>}
            </h3>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
                {(['low', 'medium', 'high'] as const).map((level) => (
                    <button
                        key={level}
                        className={`btn ${intensity === level ? 'btn-primary' : 'btn-secondary'}`}
                        onClick={() => onIntensityChange(level)}
                        style={{ flex: 1, textTransform: 'capitalize', fontSize: '0.9rem' }}
                        disabled={isSimulating}
                    >
                        {level}
                    </button>
                ))}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                *Simulates {intensity} congestion on main roads.
            </p>
        </div>
    );
};

export default TrafficControl;

import { Canvas } from '@react-three/fiber';
import { Splat, OrbitControls, Loader } from '@react-three/drei';
import { Suspense } from 'react';

export default function Campus3D({ modelUrl }: { modelUrl?: string }) {
    return (
        <div style={{ height: "100%", width: "100%", position: "relative", background: "#000" }}>
            <Canvas camera={{ position: [0, 1, 5], fov: 65 }}>
                <color attach="background" args={['#111827']} />

                <Suspense fallback={null}>
                    {/* Use custom model if provided, else default to garden demo */}
                    <Splat src={modelUrl || "/garden.splat"} />
                </Suspense>

                <OrbitControls makeDefault />
            </Canvas>

            {/* Overlay Loader */}
            <Loader />

            {/* Instruction Overlay */}
            <div style={{
                position: 'absolute',
                bottom: '20px',
                left: '50%',
                transform: 'translateX(-50%)',
                background: 'rgba(0,0,0,0.6)',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '0.8rem',
                pointerEvents: 'none'
            }}>
                Left Click to Rotate • Right Click to Pan • Scroll to Zoom
            </div>
        </div>
    );
}

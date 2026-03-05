import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera as CameraIcon, CheckCircle2, Circle, ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function CameraPage() {
    const webcamRef = useRef<Webcam>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [livenessStatus, setLivenessStatus] = useState<string>("Scanning WebGL Context...");
    const navigate = useNavigate();

    const handleCapture = useCallback(() => {
        if (webcamRef.current) {
            setIsProcessing(true);
            setLivenessStatus("Evaluating In-Browser Liveness...");

            const imageSrc = webcamRef.current.getScreenshot();

            if (imageSrc) {
                // Mock C2PA Browser Signing and API Upload
                setTimeout(() => {
                    setLivenessStatus("Assembling C2PA Manifest...");
                    setTimeout(() => {
                        navigate('/results', {
                            state: {
                                authenticity_score: 98.4,
                                c2pa_valid: true,
                                visual_artifacts_detected: false,
                                audio_artifacts_detected: false,
                                details: { info: "Signed via Browser WASM Module." }
                            }
                        });
                    }, 1500);
                }, 1500);
            }
        }
    }, [webcamRef, navigate]);

    return (
        <div className="flex flex-col items-center min-h-[80vh] justify-center px-4 max-w-4xl mx-auto space-y-8 animate-fade-in">
            <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-accent to-emerald-300">
                    Live Capture Context
                </h1>
                <p className="text-white/60">Passive liveness checks running natively in your browser.</p>
            </div>

            <div className="relative w-full max-w-2xl aspect-video rounded-2xl overflow-hidden glass-card shadow-2xl ring-1 ring-white/10 group">
                <Webcam
                    audio={false}
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    className="absolute inset-0 w-full h-full object-cover"
                    videoConstraints={{ facingMode: "user" }}
                />

                {/* Liveness Overlay */}
                <div className="absolute inset-0 z-10 pointer-events-none flex flex-col justify-between">
                    <div className="w-full flex justify-between p-6 bg-gradient-to-b from-black/50 to-transparent">
                        <div className="flex items-center gap-2 bg-black/40 backdrop-blur px-3 py-1.5 rounded-full border border-white/10">
                            <ShieldAlert size={14} className="text-accent" />
                            <span className="text-xs font-medium text-accent truncate max-w-[150px]">
                                Liveness: Active
                            </span>
                        </div>

                        {isProcessing && (
                            <div className="flex items-center gap-2 bg-primary/20 backdrop-blur px-4 py-1.5 rounded-full border border-primary text-primary animate-pulse">
                                <span className="text-sm font-semibold">{livenessStatus}</span>
                            </div>
                        )}
                    </div>

                    {/* Target Reticle */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-30 group-hover:opacity-60 transition-opacity">
                        <div className="w-48 h-48 sm:w-64 sm:h-64 border-2 border-white rounded-[50px] flex items-center justify-center">
                            <div className="w-40 h-40 sm:w-56 sm:h-56 border border-dashed border-white/50 rounded-[40px]"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="w-full max-w-md bg-surface/50 border border-white/5 rounded-2xl p-6 flex items-center justify-between glass-card">
                <div className="flex flex-col">
                    <span className="text-white font-medium text-lg">Align Face & Capture</span>
                    <span className="text-white/40 text-sm">Hardware signature ready</span>
                </div>

                <button
                    onClick={handleCapture}
                    disabled={isProcessing}
                    className={`relative rounded-full p-2 group transition-all duration-300 ${isProcessing ? 'pointer-events-none opacity-50' : 'hover:bg-white/10 active:scale-95 cursor-pointer'
                        }`}
                >
                    <div className="absolute inset-0 rounded-full border-[3px] border-white z-0 group-hover:scale-[1.1] group-hover:border-primary transition-all duration-300"></div>
                    {isProcessing ? (
                        <Circle className="text-white w-14 h-14 animate-spin opacity-50 relative z-10" strokeWidth={1.5} />
                    ) : (
                        <CameraIcon className="text-primary w-14 h-14 relative z-10 group-hover:scale-95 transition-transform bg-white rounded-full p-2.5" strokeWidth={2.5} />
                    )}
                </button>
            </div>
        </div>
    );
}

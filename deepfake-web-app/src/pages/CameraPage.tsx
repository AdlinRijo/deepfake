import React, { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { Camera as CameraIcon, Circle, ShieldAlert, AlertCircle, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export default function CameraPage() {
    const webcamRef = useRef<Webcam>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [livenessStatus, setLivenessStatus] = useState<string>("Ready to capture");
    const [elapsedTime, setElapsedTime] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const navigate = useNavigate();

    const startTimer = () => {
        setElapsedTime(0);
        timerRef.current = setInterval(() => {
            setElapsedTime(prev => prev + 100);
        }, 100);
    };

    const stopTimer = () => {
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
    };

    const formatTime = (ms: number) => {
        return `${(ms / 1000).toFixed(1)}s`;
    };

    const handleCapture = useCallback(async () => {
        if (webcamRef.current) {
            setIsProcessing(true);
            setError(null);
            setLivenessStatus("Capturing frame...");

            const imageSrc = webcamRef.current.getScreenshot();

            if (imageSrc) {
                try {
                    setLivenessStatus("Sending to AI models...");
                    startTimer();

                    // Convert base64 screenshot to a File blob
                    const response = await fetch(imageSrc);
                    const blob = await response.blob();
                    const file = new File([blob], 'live_capture.jpg', { type: 'image/jpeg' });

                    // Send to real backend API
                    const formData = new FormData();
                    formData.append('file', file);

                    setLivenessStatus("Running EfficientNet-B0 analysis...");

                    const result = await axios.post(`${API_URL}/upload`, formData, {
                        headers: { 'Content-Type': 'multipart/form-data' },
                    });

                    stopTimer();
                    setLivenessStatus("Analysis complete!");

                    // Navigate to results with REAL AI data
                    setTimeout(() => {
                        navigate('/results', {
                            state: {
                                ...result.data,
                                analysis_time_ms: elapsedTime,
                                source: 'live_capture',
                            }
                        });
                    }, 500);

                } catch (err: any) {
                    stopTimer();
                    setIsProcessing(false);
                    setLivenessStatus("Ready to capture");
                    const message = err.response?.data?.detail || err.message || 'Failed to analyze capture. Is the backend running?';
                    setError(message);
                    console.error('Capture analysis error:', err);
                }
            }
        }
    }, [webcamRef, navigate, elapsedTime]);

    return (
        <div className="flex flex-col items-center min-h-[80vh] justify-center px-4 max-w-4xl mx-auto space-y-8 animate-fade-in">
            <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-accent to-emerald-300">
                    Live Capture & AI Analysis
                </h1>
                <p className="text-white/60">Capture a photo and run real AI deepfake detection instantly.</p>
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
                                AI Detection: Active
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

            {/* Timer display when processing */}
            {isProcessing && (
                <div className="flex items-center gap-2 text-white/50 text-sm">
                    <Clock size={14} />
                    <span>Elapsed: <span className="text-white font-mono font-medium">{formatTime(elapsedTime)}</span></span>
                </div>
            )}

            {/* Error display */}
            {error && (
                <div className="w-full max-w-md glass-card rounded-xl p-4 border border-red-500/30 bg-red-500/10 flex items-start gap-3 text-left">
                    <AlertCircle className="text-red-400 flex-shrink-0 mt-0.5" size={20} />
                    <div>
                        <h4 className="font-semibold text-red-400">Analysis Failed</h4>
                        <p className="text-sm text-white/60 mt-1">{error}</p>
                    </div>
                </div>
            )}

            <div className="w-full max-w-md bg-surface/50 border border-white/5 rounded-2xl p-6 flex items-center justify-between glass-card">
                <div className="flex flex-col">
                    <span className="text-white font-medium text-lg">Align Face & Capture</span>
                    <span className="text-white/40 text-sm">Real AI analysis on capture</span>
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

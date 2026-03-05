import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileVideo, ShieldAlert, ArrowRight, AlertCircle, Clock, FileImage, Film } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export default function UploadPage() {
    const [isHovering, setIsHovering] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [statusText, setStatusText] = useState('');
    const [elapsedTime, setElapsedTime] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, []);

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
        const seconds = (ms / 1000).toFixed(1);
        return `${seconds}s`;
    };

    const handleUpload = async (file: File) => {
        setError(null);
        setIsUploading(true);
        setUploadProgress(0);
        setStatusText('Uploading file...');
        startTimer();

        try {
            const formData = new FormData();
            formData.append('file', file);

            // Phase 1: Upload with progress tracking
            setStatusText('Uploading file to server...');
            const response = await axios.post(`${API_URL}/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: (progressEvent) => {
                    const percent = progressEvent.total
                        ? Math.round((progressEvent.loaded / progressEvent.total) * 30)
                        : 0;
                    setUploadProgress(percent);
                },
            });

            // Upload complete — AI analysis happened on server
            setUploadProgress(100);
            setStatusText('Analysis complete!');
            stopTimer();

            // Navigate to results with REAL data from AI models
            setTimeout(() => {
                navigate('/results', {
                    state: {
                        ...response.data,
                        analysis_time_ms: elapsedTime,
                    }
                });
            }, 500);

        } catch (err: any) {
            stopTimer();
            setIsUploading(false);
            setUploadProgress(0);
            const message = err.response?.data?.detail || err.message || 'Failed to analyze media. Is the backend running?';
            setError(message);
            console.error('Upload error:', err);
        }
    };

    const handleFileDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsHovering(false);
        const file = e.dataTransfer.files?.[0];
        if (file) {
            setSelectedFile(file);
            handleUpload(file);
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            handleUpload(file);
        }
    };

    const getFileIcon = (file: File) => {
        if (file.type.startsWith('video')) return <Film size={20} className="text-purple-400" />;
        return <FileImage size={20} className="text-blue-400" />;
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] max-w-2xl mx-auto text-center space-y-10">
            <div className="space-y-4 animate-slide-up">
                <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-2">
                    Authenticate Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">Media</span>
                </h1>
                <p className="text-lg text-white/50 max-w-xl mx-auto">
                    Upload any image or video to run a real AI deepfake analysis using EfficientNet-B0 and Wav2Vec2 models.
                </p>
            </div>

            {/* Hidden file input */}
            <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,video/mp4,video/quicktime,audio/wav,audio/mp3,audio/mpeg"
                onChange={handleFileSelect}
                className="hidden"
            />

            <div
                className={`w-full glass-card rounded-2xl p-12 transition-all duration-300 border-2 border-dashed ${isHovering ? 'border-primary bg-primary/10 scale-[1.02]' : 'border-white/20 hover:border-white/40'}`}
                onDragOver={(e) => { e.preventDefault(); setIsHovering(true); }}
                onDragLeave={() => setIsHovering(false)}
                onDrop={handleFileDrop}
            >
                {isUploading ? (
                    <div className="flex flex-col items-center space-y-6 animate-fade-in">
                        {/* File info */}
                        {selectedFile && (
                            <div className="flex items-center gap-3 bg-white/5 px-4 py-2 rounded-lg border border-white/10">
                                {getFileIcon(selectedFile)}
                                <span className="text-sm text-white/70 truncate max-w-[200px]">{selectedFile.name}</span>
                                <span className="text-xs text-white/40">({(selectedFile.size / 1024 / 1024).toFixed(1)} MB)</span>
                            </div>
                        )}

                        {/* Status text with spinner */}
                        <div className="flex items-center gap-3">
                            <div className="relative w-10 h-10">
                                <div className="absolute inset-0 rounded-full border-4 border-white/10"></div>
                                <div className="absolute inset-0 rounded-full border-4 border-primary border-t-transparent animate-spin"></div>
                            </div>
                            <p className="text-lg font-medium text-white/80">{statusText}</p>
                        </div>

                        {/* Progress bar */}
                        <div className="w-full max-w-md space-y-2">
                            <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-300 ease-out"
                                    style={{ width: `${uploadProgress}%` }}
                                ></div>
                            </div>
                            <div className="flex justify-between text-xs text-white/40">
                                <span>{uploadProgress < 100 ? 'Running AI models...' : 'Done!'}</span>
                                <span>{uploadProgress}%</span>
                            </div>
                        </div>

                        {/* Elapsed time */}
                        <div className="flex items-center gap-2 text-white/50 text-sm">
                            <Clock size={14} />
                            <span>Elapsed: <span className="text-white font-mono font-medium">{formatTime(elapsedTime)}</span></span>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center space-y-6">
                        <div className="p-4 rounded-full bg-white/5 text-primary ring-1 ring-white/10">
                            <Upload size={48} strokeWidth={1.5} />
                        </div>

                        <div className="space-y-2">
                            <h3 className="text-xl font-semibold">Drag & Drop Media</h3>
                            <p className="text-white/40 text-sm">Supports MP4, MOV, JPEG, PNG, WAV, MP3</p>
                        </div>

                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="btn-primary flex items-center gap-2 mt-4"
                        >
                            Browse Files <ArrowRight size={18} />
                        </button>
                    </div>
                )}
            </div>

            {/* Error display */}
            {error && (
                <div className="w-full glass-card rounded-xl p-4 border border-red-500/30 bg-red-500/10 flex items-start gap-3 text-left">
                    <AlertCircle className="text-red-400 flex-shrink-0 mt-0.5" size={20} />
                    <div>
                        <h4 className="font-semibold text-red-400">Analysis Failed</h4>
                        <p className="text-sm text-white/60 mt-1">{error}</p>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                <div className="glass-card rounded-xl p-5 flex items-start text-left gap-4">
                    <ShieldAlert className="text-accent flex-shrink-0" size={24} />
                    <div>
                        <h4 className="font-semibold text-white">C2PA Standard</h4>
                        <p className="text-sm text-white/50 mt-1">Verifies digital signatures and hardware provenance trails.</p>
                    </div>
                </div>
                <div className="glass-card rounded-xl p-5 flex items-start text-left gap-4">
                    <FileVideo className="text-secondary flex-shrink-0" size={24} />
                    <div>
                        <h4 className="font-semibold text-white">Multimodal AI Pipeline</h4>
                        <p className="text-sm text-white/50 mt-1">EfficientNet-B0 (visual) + Wav2Vec2 (audio) real AI detection.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

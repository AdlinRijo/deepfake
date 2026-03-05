import React from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { ShieldCheck, ShieldAlert, Cpu, Fingerprint, RefreshCcw, Clock, Brain, AudioLines, Users, ScanFace } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: any[]) {
    return twMerge(clsx(inputs));
}

export default function ResultsPage() {
    const location = useLocation();
    const navigate = useNavigate();

    // Protect route if accessed directly without state
    if (!location.state) {
        return <Navigate to="/" replace />;
    }

    const { authenticity_score, c2pa_valid, visual_artifacts_detected, audio_artifacts_detected, face_detected, faces_count, verdict, details, analysis_time_ms } = location.state;

    const isAuthentic = authenticity_score > 80;
    const isSuspicious = authenticity_score > 50 && authenticity_score <= 80;

    const scoreColorClass = isAuthentic ? 'text-accent' : isSuspicious ? 'text-yellow-500' : 'text-danger';
    const scoreBgClass = isAuthentic ? 'bg-accent/10 border-accent/20' : isSuspicious ? 'bg-yellow-500/10 border-yellow-500/20' : 'bg-danger/10 border-danger/20';

    // Extract detailed scores from backend response
    const visualScore = details?.visual_analysis?.visual_artifacts_score;
    const audioScore = details?.audio_analysis?.audio_artifacts_score;
    const visualModel = details?.visual_analysis?.model || 'N/A';
    const audioModel = details?.audio_analysis?.model || 'N/A';
    const visualConfidence = details?.visual_analysis?.confidence;
    const audioConfidence = details?.audio_analysis?.confidence;
    const mediaType = details?.media_type || 'unknown';

    // Face analysis data
    const faceAnalysis = details?.face_analysis;
    const facesDetected = faceAnalysis?.faces_detected || 0;
    const uniqueIdentities = faceAnalysis?.unique_identities || 0;
    const faceClusters = faceAnalysis?.clusters || {};
    const faceThumbnails = faceAnalysis?.thumbnails || [];

    return (
        <div className="flex flex-col items-center justify-start min-h-[80vh] px-4 py-8 animate-fade-in max-w-5xl mx-auto space-y-10">
            <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold text-white">AI Analysis Results</h1>
                <p className="text-white/60">Real deepfake detection powered by EfficientNet-B0 & Wav2Vec2</p>
            </div>

            <div className={cn("w-full max-w-3xl glass-card rounded-3xl p-10 flex flex-col md:flex-row items-center justify-between gap-8 border-2 transition-colors", scoreBgClass)}>
                <div className="flex flex-col items-center md:items-start space-y-2">
                    <span className="text-sm font-bold uppercase tracking-widest text-white/50">Overall Authenticity</span>
                    <div className="flex items-baseline gap-2">
                        <span className={cn("text-7xl font-black tabular-nums tracking-tighter", scoreColorClass)}>
                            {authenticity_score.toFixed(1)}
                        </span>
                        <span className={cn("text-2xl font-bold", scoreColorClass)}>%</span>
                    </div>

                    {/* Verdict from backend AI */}
                    <div className="flex items-center gap-2 mt-4 px-4 py-2 bg-black/40 rounded-full border border-white/10">
                        {isAuthentic ? <ShieldCheck className="text-accent" size={18} /> : <ShieldAlert className="text-danger" size={18} />}
                        <span className="text-sm font-medium text-white/80">
                            {verdict || (isAuthentic ? 'Verified Authentic Media' : isSuspicious ? 'Potential Anomalies Detected' : 'Synthetically Generated Media')}
                        </span>
                    </div>

                    {/* Analysis time */}
                    {analysis_time_ms > 0 && (
                        <div className="flex items-center gap-2 mt-2 text-white/40 text-xs">
                            <Clock size={12} />
                            <span>Analyzed in <span className="text-white/60 font-mono">{(analysis_time_ms / 1000).toFixed(1)}s</span></span>
                        </div>
                    )}
                </div>

                {/* Visual Graphic */}
                <div className="relative w-48 h-48 flex items-center justify-center">
                    <svg className="absolute inset-0 w-full h-full -rotate-90">
                        <circle cx="96" cy="96" r="80" className="stroke-white/10" strokeWidth="12" fill="none" />
                        <circle cx="96" cy="96" r="80"
                            className={cn("transition-all duration-1000 ease-out", scoreColorClass)}
                            stroke="currentColor"
                            strokeWidth="12"
                            fill="none"
                            strokeDasharray="502"
                            strokeDashoffset={502 - (502 * authenticity_score) / 100}
                            strokeLinecap="round" />
                    </svg>
                    <Cpu className={cn("w-16 h-16 opacity-80", scoreColorClass)} />
                </div>
            </div>

            <div className="w-full max-w-3xl grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Trust Provenance */}
                <div className="glass-card p-6 rounded-2xl flex flex-col gap-4 border border-white/5">
                    <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                        <Fingerprint className="text-primary" />
                        <h3 className="text-lg font-semibold text-white">Trust Provenance</h3>
                    </div>
                    <div className="space-y-4 pt-2">
                        <div className="flex justify-between items-center">
                            <span className="text-white/60">C2PA Signature</span>
                            <span className={cn("font-medium px-3 py-1 rounded-md text-sm", c2pa_valid ? 'bg-accent/20 text-accent' : 'bg-danger/20 text-danger')}>
                                {c2pa_valid ? 'Cryptographically Valid' : 'Missing / Invalid'}
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-white/60">Media Type</span>
                            <span className="font-medium px-3 py-1 rounded-md text-sm bg-white/10 text-white/70 capitalize">
                                {mediaType}
                            </span>
                        </div>
                    </div>
                </div>

                {/* AI Model Results */}
                <div className="glass-card p-6 rounded-2xl flex flex-col gap-4 border border-white/5">
                    <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                        <Brain className="text-secondary" />
                        <h3 className="text-lg font-semibold text-white">AI Model Inference</h3>
                    </div>
                    <div className="space-y-4 pt-2">
                        <div className="space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-white/60 flex items-center gap-1.5"><Cpu size={14} /> Visual Analysis</span>
                                <span className={cn("font-medium px-3 py-1 rounded-md text-sm", visual_artifacts_detected ? 'bg-danger/20 text-danger' : 'bg-accent/20 text-accent')}>
                                    {visual_artifacts_detected ? 'AI Generated / Fake' : 'Natural / Real'}
                                </span>
                            </div>
                            {visualScore !== undefined && (
                                <div className="ml-4 space-y-1">
                                    <div className="flex justify-between text-xs text-white/40">
                                        <span>{visualModel}</span>
                                        <span>Fake: {(visualScore * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                                        <div
                                            className={cn("h-full rounded-full", visual_artifacts_detected ? 'bg-red-500' : 'bg-accent')}
                                            style={{ width: `${visualScore * 100}%` }}
                                        ></div>
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-white/60 flex items-center gap-1.5"><AudioLines size={14} /> Audio Analysis</span>
                                <span className={cn("font-medium px-3 py-1 rounded-md text-sm", audio_artifacts_detected ? 'bg-danger/20 text-danger' : 'bg-accent/20 text-accent')}>
                                    {audio_artifacts_detected ? 'Synthesized Audio' : 'Natural Audio'}
                                </span>
                            </div>
                            {audioScore !== undefined && audioScore > 0 && (
                                <div className="ml-4 space-y-1">
                                    <div className="flex justify-between text-xs text-white/40">
                                        <span>{audioModel}</span>
                                        <span>Fake: {(audioScore * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                                        <div
                                            className={cn("h-full rounded-full", audio_artifacts_detected ? 'bg-red-500' : 'bg-accent')}
                                            style={{ width: `${audioScore * 100}%` }}
                                        ></div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Face Analysis Section */}
            {(facesDetected > 0 || face_detected) && (
                <div className="w-full max-w-3xl glass-card p-6 rounded-2xl flex flex-col gap-4 border border-white/5">
                    <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                        <ScanFace className="text-purple-400" />
                        <h3 className="text-lg font-semibold text-white">Face Analysis</h3>
                        <span className="ml-auto text-xs text-white/40">{faceAnalysis?.model || 'dFace (MTCNN + FaceNet)'}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-2">
                        <div className="flex flex-col items-center gap-1 bg-white/5 rounded-xl p-4">
                            <ScanFace className="text-blue-400" size={28} />
                            <span className="text-2xl font-bold text-white">{facesDetected}</span>
                            <span className="text-xs text-white/50">Faces Detected</span>
                        </div>
                        <div className="flex flex-col items-center gap-1 bg-white/5 rounded-xl p-4">
                            <Users className="text-purple-400" size={28} />
                            <span className="text-2xl font-bold text-white">{uniqueIdentities}</span>
                            <span className="text-xs text-white/50">Unique Identities</span>
                        </div>
                    </div>

                    {/* Identity Cluster Thumbnails */}
                    {Object.keys(faceClusters).length > 0 && (
                        <div className="pt-4 space-y-3">
                            <h4 className="text-sm font-medium text-white/60">Identity Clusters</h4>
                            <div className="flex flex-wrap gap-3">
                                {Object.entries(faceClusters).map(([key, cluster]: [string, any]) => (
                                    <div key={key} className="flex flex-col items-center gap-1.5 bg-white/5 rounded-xl p-3 border border-white/10">
                                        {cluster.sample_thumbnail && (
                                            <img
                                                src={`data:image/jpeg;base64,${cluster.sample_thumbnail}`}
                                                alt={key}
                                                className="w-16 h-16 rounded-lg object-cover ring-2 ring-purple-500/30"
                                            />
                                        )}
                                        <span className="text-xs text-white/70 font-medium">{key.replace('_', ' ')}</span>
                                        <span className="text-[10px] text-white/40">{cluster.count} appearances</span>
                                        <span className="text-[10px] text-white/40">Conf: {(cluster.avg_confidence * 100).toFixed(1)}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Image face thumbnails (no clusters) */}
                    {faceThumbnails.length > 0 && Object.keys(faceClusters).length === 0 && (
                        <div className="pt-4 space-y-3">
                            <h4 className="text-sm font-medium text-white/60">Detected Faces</h4>
                            <div className="flex flex-wrap gap-3">
                                {faceThumbnails.map((thumb: string, idx: number) => (
                                    <img
                                        key={idx}
                                        src={`data:image/jpeg;base64,${thumb}`}
                                        alt={`face-${idx}`}
                                        className="w-16 h-16 rounded-lg object-cover ring-2 ring-blue-500/30"
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            <button
                onClick={() => navigate('/')}
                className="btn-secondary flex items-center gap-2 mt-8"
            >
                <RefreshCcw size={16} /> Analyze Another File
            </button>
        </div>
    );
}

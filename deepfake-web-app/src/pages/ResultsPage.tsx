import React from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { ShieldCheck, ShieldAlert, Cpu, Fingerprint, RefreshCcw } from 'lucide-react';
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

    const { authenticity_score, c2pa_valid, visual_artifacts_detected, audio_artifacts_detected, details } = location.state;

    const isAuthentic = authenticity_score > 80;
    const isSuspicious = authenticity_score > 50 && authenticity_score <= 80;

    const scoreColorClass = isAuthentic ? 'text-accent' : isSuspicious ? 'text-yellow-500' : 'text-danger';
    const scoreBgClass = isAuthentic ? 'bg-accent/10 border-accent/20' : isSuspicious ? 'bg-yellow-500/10 border-yellow-500/20' : 'bg-danger/10 border-danger/20';

    return (
        <div className="flex flex-col items-center justify-start min-h-[80vh] px-4 py-8 animate-fade-in max-w-5xl mx-auto space-y-10">
            <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold text-white">Analysis Results</h1>
                <p className="text-white/60">Comprehensive deepfake intelligence report.</p>
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

                    <div className="flex items-center gap-2 mt-4 px-4 py-2 bg-black/40 rounded-full border border-white/10">
                        {isAuthentic ? <ShieldCheck className="text-accent" size={18} /> : <ShieldAlert className="text-danger" size={18} />}
                        <span className="text-sm font-medium text-white/80">
                            {isAuthentic ? 'Verified Authentic Media' : isSuspicious ? 'Potential Anomalies Detected' : 'Synthetically Generated Media'}
                        </span>
                    </div>
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
                <div className="glass-card p-6 rounded-2xl flex flex-col gap-4 border border-white/5">
                    <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                        <Fingerprint className="text-primary" />
                        <h3 className="text-lg font-semibold text-white">Trust Provenance</h3>
                    </div>
                    <div className="space-y-4 pt-2">
                        <div className="flex justify-between items-center">
                            <span className="text-white/60">C2PA Standard Signature</span>
                            <span className={cn("font-medium px-3 py-1 rounded-md text-sm", c2pa_valid ? 'bg-accent/20 text-accent' : 'bg-danger/20 text-danger')}>
                                {c2pa_valid ? 'Cryptographically Valid' : 'Missing / Invalid'}
                            </span>
                        </div>
                        {details.info && (
                            <p className="text-sm text-white/40 italic">"{details.info}"</p>
                        )}
                    </div>
                </div>

                <div className="glass-card p-6 rounded-2xl flex flex-col gap-4 border border-white/5">
                    <div className="flex items-center gap-3 border-b border-white/10 pb-4">
                        <Cpu className="text-secondary" />
                        <h3 className="text-lg font-semibold text-white">Inference Vectors</h3>
                    </div>
                    <div className="space-y-4 pt-2">
                        <div className="flex justify-between items-center">
                            <span className="text-white/60">Visual Artifacts</span>
                            <span className={cn("font-medium px-3 py-1 rounded-md text-sm", visual_artifacts_detected ? 'bg-danger/20 text-danger' : 'bg-accent/20 text-accent')}>
                                {visual_artifacts_detected ? 'Detected High Risk' : 'None Detected'}
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-white/60">Audio Synthesis</span>
                            <span className={cn("font-medium px-3 py-1 rounded-md text-sm", audio_artifacts_detected ? 'bg-danger/20 text-danger' : 'bg-accent/20 text-accent')}>
                                {audio_artifacts_detected ? 'Detected Synthesized' : 'Natural Audio Profile'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <button
                onClick={() => navigate('/')}
                className="btn-secondary flex items-center gap-2 mt-8"
            >
                <RefreshCcw size={16} /> Analyze Another File
            </button>
        </div>
    );
}

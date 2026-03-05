import React, { useState } from 'react';
import { Upload, FileVideo, ShieldAlert, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function UploadPage() {
    const [isHovering, setIsHovering] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const navigate = useNavigate();

    const handleFileDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsHovering(false);
        simulateUpload();
    };

    const simulateUpload = () => {
        setIsUploading(true);
        // Mocking an upload delay and navigating to results
        setTimeout(() => {
            setIsUploading(false);
            navigate('/results', {
                state: {
                    authenticity_score: 45.2,
                    c2pa_valid: false,
                    visual_artifacts_detected: true,
                    audio_artifacts_detected: false,
                    details: { info: "Analyzed media successfully." }
                }
            });
        }, 2500);
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] max-w-2xl mx-auto text-center space-y-10">
            <div className="space-y-4 animate-slide-up">
                <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-2">
                    Authenticate Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">Media</span>
                </h1>
                <p className="text-lg text-white/50 max-w-xl mx-auto">
                    Upload any image or video to run a multimodal deepfake analysis and detect cryptographic provenance tampering.
                </p>
            </div>

            <div
                className={`w-full glass-card rounded-2xl p-12 transition-all duration-300 border-2 border-dashed ${isHovering ? 'border-primary bg-primary/10 scale-[1.02]' : 'border-white/20 hover:border-white/40'}`}
                onDragOver={(e) => { e.preventDefault(); setIsHovering(true); }}
                onDragLeave={() => setIsHovering(false)}
                onDrop={handleFileDrop}
            >
                {isUploading ? (
                    <div className="flex flex-col items-center space-y-4 animate-fade-in">
                        <div className="relative w-16 h-16">
                            <div className="absolute inset-0 rounded-full border-4 border-white/10"></div>
                            <div className="absolute inset-0 rounded-full border-4 border-primary border-t-transparent animate-spin"></div>
                        </div>
                        <p className="text-xl font-medium text-white/80 animate-pulse-slow">Analyzing Media...</p>
                    </div>
                ) : (
                    <div className="flex flex-col items-center space-y-6">
                        <div className="p-4 rounded-full bg-white/5 text-primary ring-1 ring-white/10">
                            <Upload size={48} strokeWidth={1.5} />
                        </div>

                        <div className="space-y-2">
                            <h3 className="text-xl font-semibold">Drag & Drop Media</h3>
                            <p className="text-white/40 text-sm">Supports MP4, MOV, JPEG, PNG (Max 50MB)</p>
                        </div>

                        <button
                            onClick={simulateUpload}
                            className="btn-primary flex items-center gap-2 mt-4"
                        >
                            Browse Files <ArrowRight size={18} />
                        </button>
                    </div>
                )}
            </div>

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
                        <h4 className="font-semibold text-white">Multimodal Pipeline</h4>
                        <p className="text-sm text-white/50 mt-1">Cross-references visual inconsistencies and audio synthesis.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

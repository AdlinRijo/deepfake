import React, { useState } from 'react';
import { Key, X, Copy, Check, ShieldAlert, AlertCircle } from 'lucide-react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

interface ApiAccessModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function ApiAccessModal({ isOpen, onClose }: ApiAccessModalProps) {
    const [companyName, setCompanyName] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [apiKey, setApiKey] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    if (!isOpen) return null;

    const handleGenerate = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setApiKey(null);
        setIsLoading(true);

        if (companyName.trim().length < 2) {
            setError('Please enter a valid company name.');
            setIsLoading(false);
            return;
        }

        try {
            const response = await axios.post(`${API_URL}/admin/generate-key`, {
                company_name: companyName.trim()
            });
            setApiKey(response.data.api_key);
            setCompanyName('');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to generate API Key.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleCopy = () => {
        if (apiKey) {
            navigator.clipboard.writeText(apiKey);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleClose = () => {
        setApiKey(null);
        setCompanyName('');
        setError(null);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
            <div className="relative w-full max-w-md bg-[#1A1A24] border border-white/10 rounded-2xl shadow-2xl p-6 overflow-hidden">
                {/* Close Button */}
                <button
                    onClick={handleClose}
                    className="absolute top-4 right-4 text-white/50 hover:text-white transition-colors"
                >
                    <X size={20} />
                </button>

                {/* Header */}
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-3 rounded-full bg-accent/20 text-accent">
                        <Key size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white">API Access</h2>
                        <p className="text-sm text-white/50">Generate keys for B2B integration</p>
                    </div>
                </div>

                {/* Error Banner */}
                {error && (
                    <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-start gap-2">
                        <AlertCircle size={16} className="text-red-400 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-red-300">{error}</p>
                    </div>
                )}

                {/* Content */}
                {!apiKey ? (
                    <form onSubmit={handleGenerate} className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-white/80">Company Name</label>
                            <input
                                type="text"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                                placeholder="e.g. X Corp"
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-accent/50"
                                required
                            />
                        </div>

                        <div className="p-3 rounded-lg bg-white/5 text-sm text-white/60 flex items-start gap-2">
                            <ShieldAlert size={16} className="flex-shrink-0 mt-0.5" />
                            <p>This key grants full access to the B2B verification endpoints. Keep it secure.</p>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading || !companyName.trim()}
                            className="w-full py-2.5 rounded-lg bg-gradient-to-r from-primary to-accent text-white font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                            ) : (
                                <>Generate API Key</>
                            )}
                        </button>
                    </form>
                ) : (
                    <div className="space-y-6 animate-slide-up">
                        <div className="text-center">
                            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-500/20 text-green-400 mb-3">
                                <Check size={24} />
                            </div>
                            <h3 className="text-lg font-semibold text-white">Key Generated Successfully</h3>
                            <p className="text-sm text-white/60 mt-1">Please copy this key now. It will not be shown again.</p>
                        </div>

                        <div className="relative">
                            <input
                                type="text"
                                readOnly
                                value={apiKey}
                                className="w-full bg-black/50 border border-accent/30 rounded-lg pl-4 pr-12 py-3 text-white font-mono text-sm"
                            />
                            <button
                                onClick={handleCopy}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md hover:bg-white/10 text-white/70 transition-colors"
                                title="Copy to clipboard"
                            >
                                {copied ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
                            </button>
                        </div>

                        <button
                            onClick={handleClose}
                            className="w-full py-2.5 rounded-lg border border-white/20 text-white font-medium hover:bg-white/5 transition-colors"
                        >
                            Done
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

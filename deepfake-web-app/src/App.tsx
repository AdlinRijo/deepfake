import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Camera, Upload, LayoutDashboard } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

import UploadPage from './pages/UploadPage';
import CameraPage from './pages/CameraPage';
import ResultsPage from './pages/ResultsPage';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

function Navigation() {
    const location = useLocation();

    const navItems = [
        { path: '/', label: 'Upload', icon: Upload },
        { path: '/camera', label: 'Live Capture', icon: Camera },
    ];

    return (
        <nav className="fixed top-0 w-full z-50 glass-card border-b border-white/5 py-4">
            <div className="container mx-auto px-4 flex justify-between items-center">
                <Link to="/" className="flex items-center gap-2 group">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center group-hover:shadow-[0_0_15px_rgba(59,130,246,0.5)] transition-all">
                        <LayoutDashboard size={18} className="text-white" />
                    </div>
                    <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
                        Deepfake Detector
                    </span>
                </Link>

                <div className="flex gap-2">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={cn(
                                    "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300",
                                    isActive
                                        ? "bg-white/10 text-white shadow-[inset_0_1px_rgba(255,255,255,0.1)]"
                                        : "text-white/60 hover:text-white hover:bg-white/5"
                                )}
                            >
                                <Icon size={16} />
                                <span className="hidden sm:inline">{item.label}</span>
                            </Link>
                        );
                    })}
                </div>
            </div>
        </nav>
    );
}

function App() {
    return (
        <BrowserRouter>
            <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-surface via-background to-background pt-24 pb-12">
                <Navigation />
                <main className="container mx-auto px-4 animate-fade-in">
                    <Routes>
                        <Route path="/" element={<UploadPage />} />
                        <Route path="/camera" element={<CameraPage />} />
                        <Route path="/results" element={<ResultsPage />} />
                    </Routes>
                </main>
            </div>
        </BrowserRouter>
    );
}

export default App;

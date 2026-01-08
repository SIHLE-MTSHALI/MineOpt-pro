/**
 * NotFoundPage.jsx - 404 Error Page
 * 
 * Displays when user navigates to a non-existent route.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, ArrowLeft, AlertTriangle } from 'lucide-react';

const NotFoundPage = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6">
            <div className="text-center max-w-md">
                {/* Icon */}
                <div className="w-24 h-24 mx-auto mb-8 rounded-2xl bg-gradient-to-br from-amber-500/20 to-red-500/20 flex items-center justify-center border border-amber-500/30">
                    <AlertTriangle size={48} className="text-amber-400" />
                </div>

                {/* Error Code */}
                <h1 className="text-8xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-red-400 mb-4">
                    404
                </h1>

                {/* Title */}
                <h2 className="text-2xl font-semibold text-white mb-4">
                    Page Not Found
                </h2>

                {/* Description */}
                <p className="text-slate-400 mb-8">
                    The page you're looking for doesn't exist or has been moved.
                    Check the URL or navigate back to the dashboard.
                </p>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <button
                        onClick={() => navigate(-1)}
                        className="flex items-center justify-center gap-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 rounded-xl transition-colors"
                    >
                        <ArrowLeft size={18} />
                        Go Back
                    </button>

                    <button
                        onClick={() => navigate('/app/dashboard')}
                        className="flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white rounded-xl transition-all shadow-lg shadow-blue-500/20"
                    >
                        <Home size={18} />
                        Go to Dashboard
                    </button>
                </div>

                {/* Brand */}
                <div className="mt-12 text-slate-600">
                    <span className="font-bold">MineOpt</span>
                    <span className="text-blue-500 font-bold">Pro</span>
                </div>
            </div>
        </div>
    );
};

export default NotFoundPage;

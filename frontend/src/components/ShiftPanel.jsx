import React from 'react';
import { Clock, Target } from 'lucide-react';

export default function ShiftPanel({ shiftName, progress, production, target }) {
    return (
        <div className="bg-slate-900 border-t border-slate-800 p-4 flex items-center justify-between">
            <div className="flex items-center gap-8">
                {/* Shift Info */}
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                        <Clock className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                        <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Current Shift</p>
                        <h3 className="text-lg font-bold text-white">{shiftName}</h3>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="w-64">
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-400">Shift Progress</span>
                        <span className="text-white font-medium">{progress.toFixed(0)}%</span>
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-blue-500 transition-all duration-500"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* Targets */}
            <div className="flex items-center gap-6">
                <div className="text-right">
                    <p className="text-xs text-slate-500">Shift Target</p>
                    <p className="text-lg font-bold text-white">{target.toLocaleString()} t</p>
                </div>
                <div className="text-right">
                    <p className="text-xs text-slate-500">Actual</p>
                    <p className={`text-lg font-bold ${production >= target ? 'text-green-400' : 'text-orange-400'}`}>
                        {production.toLocaleString()} t
                    </p>
                </div>
                <div className="p-3 bg-slate-800 rounded-full">
                    <Target className="w-6 h-6 text-slate-400" />
                </div>
            </div>
        </div>
    );
}

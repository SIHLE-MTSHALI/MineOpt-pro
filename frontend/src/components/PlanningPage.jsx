import React from 'react';
import { Layers, Database, ArrowRight } from 'lucide-react';
import { clsx } from 'clsx';

export default function PlanningPage({ simulationState }) {
    if (!simulationState) return <div className="p-8 text-slate-400">Waiting for simulation data...</div>;

    const { blocks, stockpiles } = simulationState;

    return (
        <div className="flex-1 bg-slate-900 p-8 overflow-y-auto">
            <h1 className="text-3xl font-bold text-white mb-8 flex items-center gap-3">
                <Layers className="text-blue-500" />
                Short-Term Scheduling & Planning
            </h1>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                {/* BLOCK MODEL VISUALIZATION */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-6">
                    <h2 className="text-xl font-bold text-slate-200 mb-4 flex items-center justify-between">
                        <span>Dig Sequence / Block Model</span>
                        <span className="text-xs font-normal text-slate-500 bg-slate-900 px-2 py-1 rounded border border-slate-800">
                            {blocks ? blocks.length : 0} Blocks
                        </span>
                    </h2>

                    <div className="space-y-3">
                        {blocks && blocks.map((block) => (
                            <div key={block.block_id} className={clsx(
                                "p-4 rounded-lg border flex items-center justify-between transition-all",
                                block.status === 'mined' ? "bg-slate-900/50 border-slate-800 opacity-50" :
                                    block.status === 'mining' ? "bg-blue-900/20 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.1)]" :
                                        block.status === 'available' ? "bg-slate-800 border-slate-700" :
                                            "bg-slate-900 border-slate-800 text-slate-600"
                            )}>
                                <div>
                                    <div className="flex items-center gap-3">
                                        <span className="font-mono text-white font-bold">{block.block_id}</span>
                                        {block.status === 'mining' && (
                                            <span className="text-xs bg-blue-500 text-blue-950 font-bold px-2 py-0.5 rounded-full animate-pulse">Running</span>
                                        )}
                                    </div>
                                    <div className="text-sm text-slate-400 mt-1">
                                        {block.tonnes.toLocaleString()}t remaining &bull; Ash: {block.quality.ash}%
                                    </div>
                                </div>

                                {block.dependencies.length > 0 && (
                                    <div className="text-xs text-slate-500 flex flex-col items-end">
                                        <span>Depends on:</span>
                                        <span className="font-mono text-slate-400">{block.dependencies.join(', ')}</span>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* STOCKPILE MONITOR */}
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-6">
                    <h2 className="text-xl font-bold text-slate-200 mb-4 flex items-center gap-2">
                        <Database className="text-purple-500" />
                        Stockpile Management
                    </h2>

                    {stockpiles && stockpiles.map(stock => (
                        <div key={stock.stockpile_id} className="mb-6 last:mb-0">
                            <div className="flex justify-between items-end mb-2">
                                <h3 className="text-lg font-bold text-white">{stock.stockpile_id}</h3>
                                <div className="text-right">
                                    <div className="text-2xl font-bold text-white">{stock.current_tonnes.toLocaleString()} <span className="text-sm text-slate-500">tonnes</span></div>
                                </div>
                            </div>

                            {/* Quality Meters */}
                            <div className="grid grid-cols-3 gap-4 mt-4">
                                <QualityMeter
                                    label="Ash"
                                    value={stock.current_quality.ash}
                                    target={stock.target_quality.ash}
                                    unit="%"
                                />
                                <QualityMeter
                                    label="Sulfur"
                                    value={stock.current_quality.sulfur}
                                    target={stock.target_quality.sulfur}
                                    unit="%"
                                />
                                <QualityMeter
                                    label="CV"
                                    value={stock.current_quality.cv}
                                    target={stock.target_quality.cv}
                                    unit="MJ/kg"
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function QualityMeter({ label, value, target, unit }) {
    const diff = value - target;
    const isGood = Math.abs(diff) < (target * 0.1); // 10% tolerance

    return (
        <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
            <div className="text-xs text-slate-500 mb-1">{label}</div>
            <div className="flex items-end gap-2">
                <span className={clsx("text-xl font-bold", isGood ? "text-green-400" : "text-orange-400")}>
                    {value.toFixed(2)}
                </span>
                <span className="text-xs text-slate-600 mb-1">{unit}</span>
            </div>
            <div className="text-xs text-slate-500 mt-1">Target: {target}</div>
        </div>
    )
}

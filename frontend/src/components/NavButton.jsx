import React from 'react';
import { clsx } from 'clsx';

export default function NavButton({ icon: Icon, active, onClick }) {
    return (
        <button
            onClick={onClick}
            className={clsx(
                "p-3 rounded-xl transition-all duration-300 w-full flex justify-center",
                active ? "bg-slate-800 text-blue-400 shadow-inner" : "text-slate-500 hover:text-slate-300 hover:bg-slate-900"
            )}
        >
            <Icon className="w-6 h-6" />
        </button>
    )
}

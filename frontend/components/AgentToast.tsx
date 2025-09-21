'use client';

import React from 'react';

export type AgentToastProps = {
  title?: string;
  subtitle?: string;
  onOpen: () => void;
  onDismiss?: () => void;
};

export default function AgentToast({ title = 'Illegal Vessel Detected', subtitle, onOpen, onDismiss }: AgentToastProps) {
  return (
    <div
      className="relative top-0 left-0 z-[1000] text-white rounded-b-2xl shadow-2xl border border-white/10 bg-black/70"
      style={{ backdropFilter: 'blur(10px)', width: 'min(400px, 92vw)', marginLeft:"12px"}}
    >
      <div className="px-6 py-4">
        <div className="flex items-start gap-4">
          <div className="mt-0.5 flex items-center justify-center w-10 h-10 rounded-full bg-red-600/20 text-red-400 ring-1 ring-red-500/30">
            <span className="text-sm">!</span>
          </div>
          <div className="flex-1">
            <div className="text-[15px] font-semibold leading-6">{title}</div>
            {subtitle && <div className="text-xs text-gray-400 mt-1.5">{subtitle}</div>}
            <div className="flex gap-2 mt-3">
              <button
                onClick={onOpen}
                className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-white text-black hover:bg-gray-200 transition-colors"
              >
                Open Agent
              </button>
              <button
                onClick={onDismiss}
                className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-black/60 border border-white/10 text-gray-300 hover:bg-black/80 transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// keyframes (scoped via tailwind arbitrary) fallback if needed
// Defined inline via animate-[] utility name; Tailwind JIT will not inject keyframes.
// If missing, animation will be skipped gracefully.



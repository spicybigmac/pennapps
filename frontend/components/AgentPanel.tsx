'use client';

import React, { useEffect, useMemo, useState } from 'react';

export type AgentPoint = {
  id?: string;
  lat: number;
  lng: number;
  timestamp: string;
  confidence: number; // 0..1
};

export type AgentPanelProps = {
  open: boolean;
  point: AgentPoint | null;
  onClose: () => void;
};

type StepState = 'pending' | 'active' | 'done';

export default function AgentPanel({ open, point, onClose }: AgentPanelProps) {
  const [showSummary, setShowSummary] = useState(false);
  const [showLaws, setShowLaws] = useState(false);
  const [steps, setSteps] = useState<StepState[]>(['pending', 'pending', 'pending', 'pending', 'pending']);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    if (!open || !point) return;

    setShowSummary(false);
    setShowLaws(false);
    setSteps(['pending', 'pending', 'pending', 'pending', 'pending']);
    setCompleted(false);

    const timers: number[] = [];
    // Stagger summary and legal basis
    timers.push(window.setTimeout(() => setShowSummary(true), 300));
    timers.push(window.setTimeout(() => setShowLaws(true), 1200));

    // Sequentially progress through steps
    const advance = (index: number) => {
      setSteps((prev) => {
        const next = [...prev];
        for (let i = 0; i < next.length; i++) {
          if (i < index) next[i] = 'done';
          else if (i === index) next[i] = 'active';
          else next[i] = 'pending';
        }
        return next;
      });
    };

    // Each step a few seconds apart
    const schedule = [0, 2200, 4200, 6200, 8200];
    schedule.forEach((t, i) => {
      timers.push(window.setTimeout(() => advance(i), 900 + t));
    });
    timers.push(
      window.setTimeout(() => {
        setSteps(['done', 'done', 'done', 'done', 'done']);
        setCompleted(true);
      }, 900 + schedule[schedule.length - 1] + 1400)
    );

    return () => {
      timers.forEach((id) => window.clearTimeout(id));
    };
  }, [open, point]);

  const laws = useMemo(
    () => [
      {
        title: 'UN Fish Stocks Agreement Art. 18',
        href: 'https://www.un.org/Depts/los/convention_agreements/fish_stocks_agreement.htm'
      },
      {
        title: 'FAO Port State Measures Agreement Art. 9',
        href: 'https://www.fao.org/port-state-measures/en/'
      },
      {
        title: 'Magnuson–Stevens Act 16 U.S.C. §1857',
        href: 'https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title16-section1857&num=0&edition=prelim'
      }
    ],
    []
  );

  const StepIcon = ({ state }: { state: StepState }) => {
    if (state === 'active') {
      return (
        <div className="w-3.5 h-3.5 rounded-full border-2 border-yellow-400 border-t-transparent animate-spin" />
      );
    }
    if (state === 'done') {
      return (
        <div className="w-3.5 h-3.5 rounded-full bg-green-500" />
      );
    }
    return <div className="w-3.5 h-3.5 rounded-full bg-gray-700" />;
  };

  return (
    <div
      className="absolute inset-y-0 left-0 z-[1050]"
      aria-hidden={!open}
      style={{
        width: 560,
        transform: open ? 'translateX(0)' : 'translateX(-105%)',
        transition: 'transform 260ms ease',
      }}
    >
      <div className="h-full bg-black border-r border-gray-900 text-white shadow-2xl flex flex-col">
        <div className="px-4 py-3 border-b border-gray-900 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <h2 className="text-sm font-semibold">Coast Guard Dispatch Agent</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors text-sm"
            aria-label="Close agent panel"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
          {/* Detection Summary */}
          {point && (
            <div
              className="border border-gray-900 rounded-lg p-4 bg-black/60 anim-slide-up"
              style={{
                opacity: showSummary ? 1 : 0,
                transition: 'opacity 240ms ease',
              }}
            >
              <div className="text-sm font-semibold mb-2">Detection Summary</div>
              <ul className="text-xs text-gray-300 space-y-1.5">
                <li>
                  <span className="text-gray-500">Coordinates:</span>{' '}
                  {point.lat.toFixed(4)}°, {point.lng.toFixed(4)}°
                </li>
                <li>
                  <span className="text-gray-500">Timestamp:</span>{' '}
                  {new Date(point.timestamp).toLocaleString()}
                </li>
                <li>
                  <span className="text-gray-500">Confidence:</span>{' '}
                  {(point.confidence * 100).toFixed(0)}%
                </li>
                <li>
                  <span className="text-gray-500">Classification:</span>{' '}
                  Likely illegal fishing
                </li>
              </ul>
              <div className="mt-2 text-[10px] text-gray-500">source: MongoDB (simulated)</div>
            </div>
          )}

          {/* Legal Basis */}
          <div
            className="border border-gray-900 rounded-lg p-4 bg-black/60 anim-slide-up"
            style={{
              opacity: showLaws ? 1 : 0,
              transition: 'opacity 240ms ease',
            }}
          >
            <div className="text-sm font-semibold mb-2">Legal Basis (via Exa AI)</div>
            <div className="flex flex-wrap gap-1">
              {laws.map((law) => (
                <a
                  key={law.href}
                  href={law.href}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[10px] px-2.5 py-1 rounded-full border border-gray-800 text-gray-300 hover:text-white hover:border-gray-700 transition-colors"
                >
                  {law.title}
                </a>
              ))}
            </div>
          </div>

          {/* Dispatch Workflow */}
          <div className="border border-gray-900 rounded-lg p-4 bg-black/60">
            <div className="text-sm font-semibold mb-2">Dispatch Workflow</div>
            <ol className="space-y-2">
              <li className="flex items-center gap-2 text-xs text-gray-300">
                <StepIcon state={steps[0]} />
                <span>Data being sent to Coast Guard</span>
              </li>
              <li className="flex items-center gap-2 text-xs text-gray-300" style={{ opacity: steps[1] === 'pending' ? 0.4 : 1, transition: 'opacity 220ms ease' }}>
                <StepIcon state={steps[1]} />
                <span>Coast Guard received data and satellite GPS synced</span>
              </li>
              <li className="flex items-center gap-2 text-xs text-gray-300" style={{ opacity: steps[2] === 'pending' ? 0.4 : 1, transition: 'opacity 220ms ease' }}>
                <StepIcon state={steps[2]} />
                <span>Confidential users alerted about this request</span>
              </li>
              <li className="flex items-center gap-2 text-xs text-gray-300" style={{ opacity: steps[3] === 'pending' ? 0.4 : 1, transition: 'opacity 220ms ease' }}>
                <StepIcon state={steps[3]} />
                <span>Agent log saved to MongoDB database</span>
              </li>
              <li className="flex items-center gap-2 text-xs text-gray-300" style={{ opacity: steps[4] === 'pending' ? 0.4 : 1, transition: 'opacity 220ms ease' }}>
                <StepIcon state={steps[4]} />
                <span>Data sent to MongoDB pattern recognition model</span>
              </li>
            </ol>
          </div>

          {/* Summary */}
          <div
            className="border border-gray-900 rounded-lg p-4 bg-black/60 anim-slide-up"
            style={{
              opacity: completed ? 1 : 0,
              transition: 'opacity 260ms ease',
            }}
          >
            <div className="text-sm font-semibold mb-2">Summary</div>
            <p className="text-xs text-gray-300">
              Process completed. Coast Guard is on their way to investigate. ETA ~30 minutes.
            </p>
          </div>
        </div>
      </div>
      {/* Bottom action bar */}
      <div className="border-t border-gray-900 bg-black px-4 py-3">
        <button
          onClick={onClose}
          disabled={!completed}
          className="w-full text-sm font-medium rounded-lg px-4 py-2 transition-colors disabled:bg-black disabled:text-gray-600 disabled:border-gray-800 bg-white text-black hover:bg-gray-200"
        >
          {completed ? 'Complete' : 'Processing...'}
        </button>
      </div>
    </div>
  );
}



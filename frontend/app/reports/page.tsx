'use client';
import Link from 'next/link';
import React, { useState } from 'react';
import Modal from '../../components/Modal';
import { useAuth } from '../../hooks/useAuth';

interface Report {
  id: string;
  title: string;
  date: string;
  clearance: string;
}

const reports: Report[] = [
  {
    id: 'weekly-iuu-summary-2025-09-20',
    title: 'Weekly IUU Summary',
    date: '2025-09-20',
    clearance: 'Public Trust',
  },
  {
    id: 'voice-agent-performance-q3-2025',
    title: 'Voice Agent Performance Q3',
    date: '2025-09-18',
    clearance: 'Confidential',
  },
  {
    id: 'bodega-bay-mpa-analysis-2025-09-15',
    title: 'Bodega Bay MPA Analysis',
    date: '2025-09-15',
    clearance: 'Top Secret',
  },
];

const timeOptions: string[] = [];
for (let i = 0; i < 24; i++) {
  const hours = i;
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const formattedHours = hours % 12 === 0 ? 12 : hours % 12;
  timeOptions.push(`${formattedHours}:00 ${ampm}`);
}

const ReportsPage = () => {
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [reportToShare, setReportToShare] = useState<Report | null>(null);
  const { user } = useAuth();

  // Form state
  const [dateStart, setDateStart] = useState<string>('');
  const [dateEnd, setDateEnd] = useState<string>('');
  const [timeStart, setTimeStart] = useState<string>('');
  const [timeEnd, setTimeEnd] = useState<string>('');
  const [clearance, setClearance] = useState<string>('Public Trust');
  const [sections, setSections] = useState({
    iuu_activity: false,
    ai_voice_agent: false,
    vessel_tracks: false,
    economic_impact: false,
  });

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedReport, setGeneratedReport] = useState<any>(null);
  const [includedSections, setIncludedSections] = useState<string[]>([]);
  const [lastGeneratedId, setLastGeneratedId] = useState<string | null>(null);

  const handleShareClick = (report: Report) => {
    setReportToShare(report);
    setIsShareModalOpen(true);
  };

  const handleSectionToggle = (key: keyof typeof sections) => {
    setSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setGeneratedReport(null);
    setIncludedSections([]);
    try {
      const payload = {
        date_start: dateStart || null,
        date_end: dateEnd || null,
        time_start: timeStart || null,
        time_end: timeEnd || null,
        clearance,
        user_id: user?.sub || 'anonymous',
        sections: {
          iuu_activity: sections.iuu_activity,
          ai_voice_agent: sections.ai_voice_agent,
          vessel_tracks: sections.vessel_tracks,
          economic_impact: sections.economic_impact,
        },
      };

      // Diagnostics for troubleshooting
      console.log('[Reports] Generate clicked with payload:', payload);

      const res = await fetch('http://127.0.0.1:8000/api/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        console.error('[Reports] Backend error response:', text);
        throw new Error(text || 'Failed to generate report');
      }

      const data = await res.json();
      const reportJson = data.report ?? null;
      console.log('[Reports] Generation success. Included sections:', data.included_sections);
      setGeneratedReport(reportJson);
      setIncludedSections(data.included_sections ?? []);

      // Create a lightweight report entry and persist the JSON by id in localStorage
      const id = `generated-${Date.now()}`;
      const title = 'Generated Report';
      const date = new Date().toISOString().slice(0, 10);
      const clearanceSaved = clearance;
      const storageKey = `report_json_${id}`;
      try {
        localStorage.setItem(storageKey, JSON.stringify(reportJson));
      } catch (e) {
        console.warn('Failed saving report HTML to localStorage', e);
      }
      setLastGeneratedId(id);

      // Optimistically show it at top of the list by mutating local array for this session
      reports.unshift({ id, title, date, clearance: clearanceSaved });
    } catch (e: any) {
      console.error('[Reports] Generation failed:', e);
      setError(e.message || 'Something went wrong');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex-1 p-8 text-white flex">
      {/* Left side: Reports List */}
      <div className="w-1/2 pr-8 border-r border-gray-800">
        <h1 className="text-3xl font-bold mb-4">Reports</h1>
        <p className="text-gray-400 mb-8">
          Review and share weekly summaries, performance analyses, and incident reports.
        </p>

        <div className="space-y-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="flex items-center justify-between p-4 bg-black border border-gray-800 rounded-lg"
            >
              <Link href={`/reports/${report.id}`} className="flex-1 hover:underline">
                <div className="font-sans">
                  <h3 className="font-medium">{report.title}</h3>
                  <p className="text-sm text-gray-500">{report.date}</p>
                </div>
              </Link>
              <div className="flex items-center space-x-4">
                <span
                  className="px-3 py-1 text-xs font-semibold rounded-full border border-gray-700 bg-black text-gray-300 font-sans"
                >
                  {report.clearance}
                </span>
                <button
                  onClick={() => handleShareClick(report)}
                  className="w-10 h-10 flex items-center justify-center border border-gray-700 rounded-md hover:bg-gray-900 transition-colors"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
                    <polyline points="16 6 12 2 8 6" />
                    <line x1="12" x2="12" y1="2" y2="15" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right side: Generate Report */}
      <div className="w-1/2 pl-8 flex flex-col font-sans">
          <h2 className="text-xl font-bold mb-4">Generate New Report</h2>
          <p className="text-gray-400 mb-6">Customize and create a new report based on the latest data.</p>
          
          <div className="space-y-6 flex-1">
            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Date Range</label>
              <div className="flex space-x-4">
                <input value={dateStart} onChange={(e) => setDateStart(e.target.value)} type="date" className="w-full bg-black border border-gray-700 rounded-md p-2 text-white font-sans" />
                <input value={dateEnd} onChange={(e) => setDateEnd(e.target.value)} type="date" className="w-full bg-black border border-gray-700 rounded-md p-2 text-white font-sans" />
              </div>
            </div>

            {/* Time Range */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Time Range (EST)</label>
              <div className="flex space-x-4">
                <div className="relative w-full">
                  <select value={timeStart} onChange={(e) => setTimeStart(e.target.value)} className="w-full bg-black border border-gray-700 rounded-md p-2 text-white font-sans appearance-none pr-8">
                    <option value="">Select start</option>
                    {timeOptions.map(time => <option key={time} value={time}>{time}</option>)}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400">
                    <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                  </div>
                </div>
                <div className="relative w-full">
                  <select value={timeEnd} onChange={(e) => setTimeEnd(e.target.value)} className="w-full bg-black border border-gray-700 rounded-md p-2 text-white font-sans appearance-none pr-8">
                    <option value="">Select end</option>
                    {timeOptions.map(time => <option key={time} value={time}>{time}</option>)}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400">
                    <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Sections to Include */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Sections to Include</label>
              <div className="flex flex-col space-y-4">
                <label className="flex items-center space-x-3 font-sans cursor-pointer">
                  <input checked={sections.iuu_activity} onChange={() => handleSectionToggle('iuu_activity')} type="checkbox" className="peer hidden" />
                  <span className="w-5 h-5 border-2 border-gray-700 rounded-sm flex items-center justify-center transition-colors peer-checked:bg-white peer-checked:border-gray-400 peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-white ring-offset-black">
                    <svg className="w-3 h-3 text-black hidden peer-checked:block" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                  </span>
                  <span>IUU Activity Summary</span>
                </label>
                <label className="flex items-center space-x-3 font-sans cursor-pointer">
                  <input checked={sections.ai_voice_agent} onChange={() => handleSectionToggle('ai_voice_agent')} type="checkbox" className="peer hidden" />
                  <span className="w-5 h-5 border-2 border-gray-700 rounded-sm flex items-center justify-center transition-colors peer-checked:bg-white peer-checked:border-gray-400 peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-white ring-offset-black">
                    <svg className="w-3 h-3 text-black hidden peer-checked:block" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                  </span>
                  <span>AI Voice Agent Performance</span>
                </label>
                <label className="flex items-center space-x-3 font-sans cursor-pointer">
                  <input checked={sections.vessel_tracks} onChange={() => handleSectionToggle('vessel_tracks')} type="checkbox" className="peer hidden" />
                  <span className="w-5 h-5 border-2 border-gray-700 rounded-sm flex items-center justify-center transition-colors peer-checked:bg-white peer-checked:border-gray-400 peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-white ring-offset-black">
                    <svg className="w-3 h-3 text-black hidden peer-checked:block" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                  </span>
                  <span>Vessel Track Details</span>
                </label>
                <label className="flex items-center space-x-3 font-sans cursor-pointer">
                  <input checked={sections.economic_impact} onChange={() => handleSectionToggle('economic_impact')} type="checkbox" className="peer hidden" />
                  <span className="w-5 h-5 border-2 border-gray-700 rounded-sm flex items-center justify-center transition-colors peer-checked:bg-white peer-checked:border-gray-400 peer-focus-visible:ring-2 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-white ring-offset-black">
                    <svg className="w-3 h-3 text-black hidden peer-checked:block" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                  </span>
                  <span>Economic Impact Analysis</span>
                </label>
              </div>
            </div>

            {/* Clearance Level */}
            <div>
              <label htmlFor="clearance" className="block text-sm font-medium text-gray-400 mb-2">Clearance Level</label>
              <div className="relative w-full">
                <select id="clearance" value={clearance} onChange={(e) => setClearance(e.target.value)} className="w-full bg-black border border-gray-700 rounded-md p-2 text-white font-sans appearance-none pr-8">
                  <option>Public Trust</option>
                  <option>Confidential</option>
                  <option>Top Secret</option>
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400">
                  <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
              </div>
            </div>
          </div>

          {/* Generate Button */}
          <div className="mt-auto pt-6 border-t border-gray-800">
            <button
              disabled={isGenerating}
              onClick={handleGenerate}
              className="w-full bg-white text-black font-bold py-3 px-4 rounded-lg transition-colors hover:bg-gray-300 disabled:opacity-60"
            >
              {isGenerating ? 'Generating…' : 'Generate Report'}
            </button>
            <div className="sr-only" aria-live="polite">{isGenerating ? 'Generating report' : 'Idle'}</div>
            {error && (
              <p className="mt-3 text-sm text-red-400">{error}</p>
            )}
            {/* No inline preview; user clicks the new report entry to read */}
          </div>
      </div>

      <Modal isOpen={isShareModalOpen} onClose={() => setIsShareModalOpen(false)}>
        {reportToShare && (
          <>
            <h2 className="text-2xl font-bold mb-2">Share Report</h2>
            <p className="text-gray-400 mb-6 font-sans">
              You are sharing: <span className="font-semibold text-white">{reportToShare.title}</span>
            </p>
            
            <div className="font-sans">
              <label htmlFor="email" className="block text-sm font-medium text-gray-400 mb-2">Recipient's Email</label>
              <input
                type="email"
                id="email"
                placeholder="example@domain.com"
                className="w-full bg-black border border-gray-700 rounded-md p-2 text-white"
              />
            </div>

            <div className="mt-8 pt-6 border-t border-gray-800">
              <button
                onClick={() => setIsShareModalOpen(false)}
                className="w-full bg-white text-black font-bold py-3 px-4 rounded-lg transition-colors"
              >
                Send Report
              </button>
            </div>
          </>
        )}
      </Modal>
    </div>
  );
};

export default ReportsPage;

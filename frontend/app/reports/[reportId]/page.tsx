'use client';

import Link from 'next/link';
import React, { use, useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar, PieChart, Pie, Cell, Legend, AreaChart, Area } from 'recharts';

interface WeeklyData {
  week: string;
  vessels_detected: number;
}

interface CallOutcome {
  name: string;
  value: number;
}

interface AgentStats {
  success_rate: number;
  avg_call_duration_min: number;
  escalation_rate: number;
  total_calls_q3: number;
  call_outcomes: CallOutcome[];
}

interface ReportData {
  weeklyIUU: WeeklyData[];
  agentPerformance: AgentStats;
}

const COLORS = ['#FFFFFF', '#A0AEC0', '#4A5568'];

const ReportDisplayPage = ({ params }: { params: Promise<{ reportId:string }> }) => {
  const resolvedParams = use(params);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [generatedJson, setGeneratedJson] = useState<any | null>(null);

  const exportElementToPDF = (elementId: string, title: string) => {
    if (typeof window === 'undefined') return;
    const node = document.getElementById(elementId);
    if (!node) return;
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;
    const styles = `
      <style>
        @page { size: A4; margin: 16mm; }
        html, body { background: #ffffff; color: #111827; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; }
        h1,h2,h3 { color: #111827; margin: 0 0 8px 0; }
        p { margin: 8px 0; line-height: 1.5; }
        section { margin-bottom: 20px; }
        .border { border-color: #e5e7eb; }
        svg { max-width: 100% !important; height: auto !important; }
      </style>
    `;
    printWindow.document.write(`<html><head><title>${title}</title>${styles}</head><body>`);
    printWindow.document.write(node.innerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 300);
  };

  useEffect(() => {
    // If this is a generated report, load JSON and render react-based sections
    const jsonKey = `report_json_${resolvedParams.reportId}`;
    const jsonStr = typeof window !== 'undefined' ? localStorage.getItem(jsonKey) : null;
    if (jsonStr) {
      try {
        const parsed = JSON.parse(jsonStr);
        setGeneratedJson(parsed);
        setReportData(null);
        return;
      } catch (e) {
        // fall through to mock charts
      }
    }

    // Fallback to demo mock data for hardcoded reports
    fetch('/mock-data.json')
      .then((res) => res.json())
      .then((data) => setReportData(data));
  }, [resolvedParams.reportId]);

  // Render generated JSON reports with charts
  if (generatedJson) {
    return (
      <div className="flex-1 p-8 text-white">
        <div className="max-w-4xl">
          <Link href="/reports" className="flex items-center space-x-2 text-gray-400 hover:text-white mb-6">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>
            <span>All Reports</span>
          </Link>
          <h1 className="text-3xl font-bold mb-2">
            Report: <span className="text-gray-400 capitalize">{resolvedParams.reportId.replaceAll('-', ' ')}</span>
          </h1>
          <p className="text-gray-500 mb-8">Generated on: {new Date().toLocaleDateString()}</p>
          <div className="mb-4 flex justify-end">
            <button
              onClick={() => exportElementToPDF('report-content', `Report ${resolvedParams.reportId}`)}
              className="px-4 py-2 bg-white text-black rounded-md font-semibold hover:bg-gray-300"
            >
              Export PDF
            </button>
          </div>
          <div id="report-content" className="bg-black border border-gray-800 rounded-lg p-8 space-y-10 max-h-[70vh] overflow-y-auto overflow-x-hidden">
            {/* Executive Summary */}
            {Array.isArray(generatedJson.executiveSummary) && (
              <section>
                <h2 className="text-xl font-semibold mb-4 border-b border-gray-800 pb-3">Executive Summary</h2>
                <div className="space-y-4 text-gray-300">
                  {generatedJson.executiveSummary.map((p: string, idx: number) => (
                    <p key={idx}>{p}</p>
                  ))}
                </div>
              </section>
            )}

            {/* Sections */}
            {Array.isArray(generatedJson.sections) && generatedJson.sections.map((s: any, idx: number) => (
              <section key={idx}>
                <h2 className="text-xl font-semibold mb-4 border-b border-gray-800 pb-3">{s?.heading || 'Section'}</h2>
                <div className="space-y-4 text-gray-300">
                  {(Array.isArray(s?.content) ? s.content : []).map((p: string, i: number) => (
                    <p key={i}>{p}</p>
                  ))}
                </div>
                {s?.chart?.callout && (
                  <p className="text-gray-400 text-sm mt-3"><em>Chart callout:</em> {s.chart.callout}</p>
                )}

                {/* Chart selection */}
                <div className="mt-6 h-64">
                  <ResponsiveContainer>
                    {(() => {
                      const type = s?.chart?.type || 'none';
                      const heading = (s?.heading || '').toLowerCase();
                      // Sample data tailored to sustainability theme
                      if (type === 'bar' || heading.includes('iuu')) {
                        const data = [
                          { label: 'Hotspot A', incidents: 7 },
                          { label: 'Hotspot B', incidents: 5 },
                          { label: 'Hotspot C', incidents: 3 },
                          { label: 'Hotspot D', incidents: 2 },
                        ];
                        return (
                          <BarChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
                            <XAxis dataKey="label" stroke="#A0AEC0" fontSize={12} />
                            <YAxis stroke="#A0AEC0" fontSize={12} />
                            <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.85)', borderColor: '#4A5568', color: '#E2E8F0' }} />
                            <Bar dataKey="incidents" fill="#E2E8F0" radius={[4,4,0,0]} />
                          </BarChart>
                        );
                      }
                      if (type === 'radial' || heading.includes('voice agent')) {
                        const success = 82;
                        const radialData = [{ name: 'Success Rate', value: success }];
                        return (
                          <RadialBarChart innerRadius="80%" outerRadius="100%" data={radialData} startAngle={90} endAngle={-270}>
                            <RadialBar background dataKey="value" fill="#FFFFFF" cornerRadius={10} />
                            <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="text-2xl font-semibold fill-white">{`${success}%`}</text>
                            <text x="50%" y="65%" textAnchor="middle" dominantBaseline="middle" className="text-sm fill-gray-400">Success Rate</text>
                          </RadialBarChart>
                        );
                      }
                      if (type === 'pie' || heading.includes('economic')) {
                        const pieData = [
                          { name: 'Compliance Savings', value: 45 },
                          { name: 'Patrol Efficiency', value: 30 },
                          { name: 'Market Stability', value: 25 },
                        ];
                        const COLORS = ['#FFFFFF', '#A0AEC0', '#4A5568'];
                        return (
                          <PieChart>
                            <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                              {pieData.map((entry, i) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.85)', borderColor: '#4A5568', color: '#E2E8F0' }} />
                            <Legend iconSize={10} wrapperStyle={{ fontSize: '12px', color: '#A0AEC0' }} />
                          </PieChart>
                        );
                      }
                      // Default sustainability line/area chart
                      const areaData = [
                        { t: 'Wk 1', co2: 2.1 },
                        { t: 'Wk 2', co2: 2.4 },
                        { t: 'Wk 3', co2: 1.9 },
                        { t: 'Wk 4', co2: 1.6 },
                      ];
                      return (
                        <AreaChart data={areaData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                          <defs>
                            <linearGradient id="co2" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#FFFFFF" stopOpacity={0.8}/>
                              <stop offset="95%" stopColor="#FFFFFF" stopOpacity={0.1}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
                          <XAxis dataKey="t" stroke="#A0AEC0" fontSize={12} />
                          <YAxis stroke="#A0AEC0" fontSize={12} />
                          <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.85)', borderColor: '#4A5568', color: '#E2E8F0' }} />
                          <Area type="monotone" dataKey="co2" stroke="#FFFFFF" fill="url(#co2)" />
                        </AreaChart>
                      );
                    })()}
                  </ResponsiveContainer>
                </div>
              </section>
            ))}

            {/* Estimated Sustainability Impact */}
            <section>
              <h2 className="text-xl font-semibold mb-4 border-b border-gray-800 pb-3">Estimated Sustainability Impact</h2>
              <p className="text-gray-300 mb-4">Based on observed compliance improvements and deterrence effects in the selected period, we estimate the following positive environmental outcomes. These estimates are illustrative and directionally conservative.</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Endangered fish saved (bar) */}
                <div className="h-64">
                  <ResponsiveContainer>
                    <BarChart data={[{species:'Bluefin Tuna', saved: 140},{species:'Hammerhead Shark', saved: 90},{species:'Sea Turtles', saved: 60}] } margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
                      <XAxis dataKey="species" stroke="#A0AEC0" fontSize={12} />
                      <YAxis stroke="#A0AEC0" fontSize={12} />
                      <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.85)', borderColor: '#4A5568', color: '#E2E8F0' }} />
                      <Bar dataKey="saved" fill="#E2E8F0" radius={[4,4,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                {/* Pollution avoided (area) */}
                <div className="h-64">
                  <ResponsiveContainer>
                    <AreaChart data={[{t:'Wk 1', tons: 3.2},{t:'Wk 2', tons: 3.8},{t:'Wk 3', tons: 4.1},{t:'Wk 4', tons: 4.6}]} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                      <defs>
                        <linearGradient id="tons" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#FFFFFF" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#FFFFFF" stopOpacity={0.1}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
                      <XAxis dataKey="t" stroke="#A0AEC0" fontSize={12} />
                      <YAxis stroke="#A0AEC0" fontSize={12} />
                      <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.85)', borderColor: '#4A5568', color: '#E2E8F0' }} />
                      <Area type="monotone" dataKey="tons" stroke="#FFFFFF" fill="url(#tons)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                {/* Prevention mix (pie) */}
                <div className="h-64">
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie data={[{name:'Oil discharge prevented', value: 40},{name:'Illegal dumping deterred', value: 35},{name:'Bycatch reduction', value: 25}]} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                        {['#FFFFFF','#A0AEC0','#4A5568'].map((c, i) => (<Cell key={i} fill={c} />))}
                      </Pie>
                      <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.85)', borderColor: '#4A5568', color: '#E2E8F0' }} />
                      <Legend iconSize={10} wrapperStyle={{ fontSize: '12px', color: '#A0AEC0' }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    );
  }
  
  // If neither generatedJson nor reportData is ready yet, show a lightweight loading state
  if (!reportData) {
    return <div className="flex-1 p-8 text-white text-center">Loading report data...</div>;
  }
  
  const successRateData = [{ name: 'Success Rate', value: reportData.agentPerformance.success_rate }];

  return (
    <div className="flex-1 p-8 text-white">
      <div className="max-w-4xl">
        <Link href="/reports" className="flex items-center space-x-2 text-gray-400 hover:text-white mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>
          <span>All Reports</span>
        </Link>
        <h1 className="text-3xl font-bold mb-2">
          Report: <span className="text-gray-400 capitalize">{resolvedParams.reportId.replaceAll('-', ' ')}</span>
        </h1>
        <p className="text-gray-500 mb-8">Generated on: {new Date().toLocaleDateString()}</p>
        <div className="mb-4 flex justify-end">
          <button
            onClick={() => exportElementToPDF('report-content', `Report ${resolvedParams.reportId}`)}
            className="px-4 py-2 bg-white text-black rounded-md font-semibold hover:bg-gray-300"
          >
            Export PDF
          </button>
        </div>
        <div id="report-content" className="bg-black border border-gray-800 rounded-lg p-8 space-y-12 max-h-[70vh] overflow-y-auto overflow-x-hidden">
          <section>
            <h2 className="text-xl font-semibold mb-4 border-b border-gray-800 pb-3">
              Weekly IUU Activity Analysis
            </h2>
            <p className="text-gray-400 text-sm mb-6">
              This section provides a week-over-week summary of detected vessels engaged in suspected Illegal, Unreported, and Unregulated (IUU) fishing activities. The data is aggregated from AIS, satellite imagery, and environmental sensor fusion.
            </p>
            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
                <BarChart data={reportData.weeklyIUU} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
                  <XAxis dataKey="week" stroke="#A0AEC0" fontSize={12} />
                  <YAxis stroke="#A0AEC0" fontSize={12} />
                  <Tooltip
                    cursor={{ fill: 'rgba(255, 255, 255, 0.1)' }}
                    contentStyle={{
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      borderColor: '#4A5568',
                      color: '#E2E8F0',
                    }}
                  />
                  <Bar dataKey="vessels_detected" fill="#E2E8F0" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-gray-400 text-xs mt-4 text-center">
              Figure 1: Count of vessels flagged for IUU-like behavior over the past four weeks.
            </p>
            <p className="text-gray-300 text-sm mt-6">
              <strong>Analysis:</strong> A notable increase in flagged activity was observed in Week 37, coinciding with seasonal migration patterns of target species. Further investigation into the satellite reconnaissance data from this period is recommended.
            </p>
          </section>
          
          <section>
            <h2 className="text-xl font-semibold mb-4 border-b border-gray-800 pb-3">
              AI Voice Agent Performance
            </h2>
            <p className="text-gray-400 text-sm mb-6">
              The following metrics evaluate the performance of the automated AI Voice Agent. The success rate is defined as the percentage of calls resulting in a confirmed receipt of information without requiring human operator intervention.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
                {/* Chart 1: Success Rate */}
                <div className="h-64 flex flex-col items-center justify-center">
                    <ResponsiveContainer>
                      <RadialBarChart 
                        innerRadius="80%" 
                        outerRadius="100%" 
                        data={successRateData} 
                        startAngle={90} 
                        endAngle={-270}
                      >
                        <RadialBar
                          background
                          dataKey='value'
                          fill="#FFFFFF"
                          cornerRadius={10}
                        />
                        <text 
                          x="50%" 
                          y="50%" 
                          textAnchor="middle" 
                          dominantBaseline="middle" 
                          className="text-2xl font-semibold fill-white"
                        >
                          {`${reportData.agentPerformance.success_rate}%`}
                        </text>
                         <text 
                          x="50%" 
                          y="65%" 
                          textAnchor="middle" 
                          dominantBaseline="middle" 
                          className="text-sm fill-gray-400"
                        >
                          Success Rate
                        </text>
                      </RadialBarChart>
                    </ResponsiveContainer>
                </div>
                {/* Chart 2: Call Outcomes */}
                <div className="h-64">
                    <ResponsiveContainer>
                        <PieChart>
                            <Pie
                                data={reportData.agentPerformance.call_outcomes}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                fill="#8884d8"
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {reportData.agentPerformance.call_outcomes.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                cursor={{ fill: 'rgba(255, 255, 255, 0.1)' }}
                                contentStyle={{
                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                    borderColor: '#4A5568',
                                    color: '#E2E8F0',
                                }}
                            />
                            <Legend iconSize={10} wrapperStyle={{ fontSize: "12px", color: '#A0AEC0' }} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
                 {/* Stats */}
                <div className="space-y-4">
                  <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-800">
                      <p className="text-sm text-gray-400">Avg. Call Duration</p>
                      <p className="text-2xl font-semibold">{reportData.agentPerformance.avg_call_duration_min} min</p>
                  </div>
                  <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-800">
                      <p className="text-sm text-gray-400">Total Calls (Q3)</p>
                      <p className="text-2xl font-semibold">{reportData.agentPerformance.total_calls_q3}</p>
                  </div>
                </div>
            </div>
            <p className="text-gray-300 text-sm mt-6">
              <strong>Summary:</strong> The voice agent continues to perform with high efficacy, successfully managing the majority of outbound alerts. The low escalation rate of {reportData.agentPerformance.escalation_rate}% indicates a high level of autonomy and reliability. Call duration remains efficient, contributing to operational cost savings.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

export default ReportDisplayPage;

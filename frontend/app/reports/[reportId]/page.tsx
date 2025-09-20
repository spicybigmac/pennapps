'use client';

import Link from 'next/link';
import React, { use, useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadialBarChart, RadialBar, PieChart, Pie, Cell, Legend } from 'recharts';

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

  useEffect(() => {
    fetch('/mock-data.json')
      .then((res) => res.json())
      .then((data) => setReportData(data));
  }, []);

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

        <div className="bg-black border border-gray-800 rounded-lg p-8 space-y-12">
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

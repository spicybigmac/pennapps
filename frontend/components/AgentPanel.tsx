'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export type AgentPoint = {
  id?: string;
  lat: number;
  lng: number;
  timestamp: string;
  confidence: number; // 0..1
  isfishing?: boolean; // Added for the vessel data
};

export type AgentPanelProps = {
  open: boolean;
  point: AgentPoint | null;
  onClose: () => void;
};

type StepState = 'pending' | 'active' | 'done';

type ExaResult = {
  url: string;
  text: string;
};

type GeminiResponseData = {
  summaries: string[];
  agent_message: string;
  legal_basis: { title: string; summary: string; citation: string; url: string }[];
};

export default function AgentPanel({ open, point, onClose }: AgentPanelProps) {
  const [showSummary, setShowSummary] = useState(false);
  const [showLaws, setShowLaws] = useState(false);
  const [steps, setSteps] = useState<StepState[]>(['pending', 'pending', 'pending', 'pending', 'pending']);
  const [completed, setCompleted] = useState(false);

  // New states for API fetching
  const [agentResponse, setAgentResponse] = useState<string | null>(null);
  const [isLoadingAgentResponse, setIsLoadingAgentResponse] = useState(false);
  const [relevantLaws, setRelevantLaws] = useState<{ title: string; summary: string; citation:string; url: string }[]>([]);

  // Auth state
  const { user, hasAnyRole, isLoading } = useAuth();

  useEffect(() => {
    if (!open || !point) {
      // Reset states when panel is closed or point is null
      setShowSummary(false);
      setShowLaws(false);
      setSteps(['pending', 'pending', 'pending', 'pending', 'pending']);
      setCompleted(false);
      setAgentResponse(null);
      setIsLoadingAgentResponse(false);
      setRelevantLaws([]);
      return;
    }

    const fetchData = async () => {
      setAgentResponse('Loading agent response...');
      setIsLoadingAgentResponse(true);
      setShowSummary(true); // Show summary immediately
      setSteps(['active', 'pending', 'pending', 'pending', 'pending']); // Step 1 active

      setShowLaws(false);
      setRelevantLaws([]);

      try {
        // Step 1: Exa Search Request for laws and regulations
        const exaSearchQuery = `maritime laws and regulations at latitude ${point.lat.toFixed(2)}, longitude ${point.lng.toFixed(2)}`;
        const exaResponse = await fetch("http://127.0.0.1:8000/api/ai/exa/search", {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: exaSearchQuery, num_results: 3 }), // Limit results for brevity
        });
        const exaData: { results: ExaResult[] } = await exaResponse.json();

        let fetchedExaResults: ExaResult[] = [];
        if (exaData && exaData.results && exaData.results.length > 0) {
          fetchedExaResults = exaData.results;
        }
        
        setSteps(['done', 'active', 'pending', 'pending', 'pending']); // Step 1 done, Step 2 active

        // Introduce a slight delay for visual progression (mimicking old timers)
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Step 2: Gemini Chat Request for agent's response
        const chatPrompt = `An unregistered vessel (ID: ${point.id}) is located at latitude ${point.lat.toFixed(4)}, longitude ${point.lng.toFixed(4)}. It is currently ${point.isfishing ? 'fishing' : 'not fishing'}.
        Based on the following maritime laws and regulations from Exa AI search results:
        ${fetchedExaResults.length > 0 ? fetchedExaResults.map(result => `${result.url}`).join('\n') : 'No specific laws and regulations found.'}

        Please simulate an agent's response to this unregistered vessel. The response should be informative, authoritative, and suggest appropriate actions or warnings.
        Additionally, provide a summary for each of the three Exa search results.
        Your entire response must be in JSON format only, with no other formatting. Do not use Markdown within the JSON.
        The JSON should contain:
        - "agent_message": a single string for the agent's full message.
        - "legal_basis": a list of objects, where each object has:
          - "title" (string, a short encompassing title for the source)
          - "summary" (string, a summary of the Exa results' laws which are relevant to the unregistered vessel in at most three sentences), 
          - "citation" (string, an APA in-text citation for the source), and 
          - "url" (string, the original URL from Exa).

        Example JSON format:
        {
          "agent_message": "This is the agent's authoritative message.",
          "legal_basis": [
            { "title": "Example 1", "summary": "Summary of Law 1.", "citation": "(Example1, 2025)", "url": "http://example.com/law1" },
            { "title": "Example 2", "summary": "Summary of Law 2.", "citation": "(Example2, 2025)", "url": "http://example.com/law2" },
            { "title": "Example 3", "summary": "Summary of Law 3.", "citation": "(Example3, 2025)", "url": "http://example.com/law3" }
          ]
        }`;

        const geminiResponse = await fetch("http://127.0.0.1:8000/api/ai/gemini/chat", {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: chatPrompt, user_id: point.id}),
        });

        if(!geminiResponse.ok){
          const errorData = await geminiResponse.json();
          throw new Error(errorData.detail || 'The link could not be processed.');
        }

        const geminiData: GeminiResponseData = await geminiResponse.json();

        if (geminiData) {
          setAgentResponse(geminiData["agent_message"]);
          setRelevantLaws(geminiData["legal_basis"]);
          setShowLaws(true); // Show legal basis after fetching
        } else {
          setAgentResponse("Failed to get a response from the agent.");
        }
        setSteps(['done', 'done', 'active', 'pending', 'pending']); // Step 2 done, Step 3 active

        // Simulate the remaining steps of the workflow
        await new Promise(resolve => setTimeout(resolve, 1500));
        setSteps(['done', 'done', 'done', 'active', 'pending']); // Step 3 done, Step 4 active
        await new Promise(resolve => setTimeout(resolve, 1500));
        setSteps(['done', 'done', 'done', 'done', 'active']); // Step 4 done, Step 5 active
        await new Promise(resolve => setTimeout(resolve, 1500));
        setSteps(['done', 'done', 'done', 'done', 'done']); // Step 5 done
        setCompleted(true);

      } catch (error) {
        console.error('Error in agent chat process:', error);
        setAgentResponse("An error occurred while getting the agent's response.");
        // Set all steps to 'pending' or 'error' state if you want to show an error visually
        setSteps(['pending', 'pending', 'pending', 'pending', 'pending']);
        setCompleted(false); // Indicate failure
      } finally {
        setIsLoadingAgentResponse(false);
      }
    };

    fetchData();

    // No need for a return cleanup with `timers` as the fetch is handled by `fetchData`'s lifecycle
  }, [open, point]);

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

  // Check if user has required clearance level
  const hasAccess = hasAnyRole(['confidential', 'secret', 'top-secret']);

  // Don't render anything if user doesn't have required roles
  if (!isLoading && !hasAccess) {
    return null;
  }

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
                  Likely illegal fishing {point.isfishing ? '(Vessel is fishing)' : '(Vessel is not fishing)'}
                </li>
              </ul>
              <div className="mt-2 text-[10px] text-gray-500">source: MongoDB (simulated)</div>
            </div>
          )}

          {/* Dispatch Workflow */}
          <div className="border border-gray-900 rounded-lg p-4 bg-black/60">
            <div className="text-sm font-semibold mb-2">Dispatch Workflow</div>
            <ol className="space-y-2">
              <li className="flex items-center gap-2 text-xs text-gray-300">
                <StepIcon state={steps[0]} />
                <span>Exa AI searching for relevant maritime laws</span>
              </li>
              <li className="flex items-center gap-2 text-xs text-gray-300" style={{ opacity: steps[1] === 'pending' ? 0.4 : 1, transition: 'opacity 220ms ease' }}>
                <StepIcon state={steps[1]} />
                <span>Gemini AI generating agent response</span>
              </li>
              <li className="flex items-center gap-2 text-xs text-gray-300" style={{ opacity: steps[2] === 'pending' ? 0.4 : 1, transition: 'opacity 220ms ease' }}>
                <StepIcon state={steps[2]} />
                <span>Coast Guard received data and satellite GPS synced</span>
              </li>
              <li className="flex items-center gap-2 text-xs text-gray-300" style={{ opacity: steps[3] === 'pending' ? 0.4 : 1, transition: 'opacity 220ms ease' }}>
                <StepIcon state={steps[3]} />
                <span>Confidential users alerted about this request</span>
              </li>
              <li className="flex items-center gap-2 text-xs text-gray-300" style={{ opacity: steps[4] === 'pending' ? 0.4 : 1, transition: 'opacity 220ms ease' }}>
                <StepIcon state={steps[4]} />
                <span>Agent log saved to MongoDB database and sent to pattern recognition model</span>
              </li>
            </ol>
          </div>

          {/* Legal Basis */}
          <div
            className="border border-gray-900 rounded-lg p-4 bg-black/60 anim-slide-up"
            style={{
              opacity: showLaws ? 1 : 0,
              transition: 'opacity 240ms ease',
            }}
          >
            <div className="text-sm font-semibold mb-2">Legal Basis</div>
            <div className="flex flex-wrap gap-1">
              {relevantLaws ? (
                relevantLaws.map((law, index) => (
                  <div key={index} className="text-[10px] px-2.5 py-1 rounded-lg border border-gray-800 text-gray-300 hover:text-white hover:border-blue-500 transition-colors"> 
                    <p>
                      <span className="text-[12px] font-semibold">{law.title}</span>
                      {law.summary} {law.citation} <br></br>
                      <a href={law.url} className="text-blue-300">source</a>
                    </p>
                  </div>
                ))
              ) : (
                <span className="text-xs text-gray-500">No specific laws and regulations found.</span>
              )}
            </div>
          </div>

          {/* Agent Response */}
          <div
            className="border border-gray-900 rounded-lg p-4 bg-black/60 anim-slide-up"
            style={{
              opacity: agentResponse ? 1 : 0,
              transition: 'opacity 260ms ease',
            }}
          >
            <div className="text-sm font-semibold mb-2">Agent's Message</div>
            {isLoadingAgentResponse ? (
              <p className="text-xs text-gray-400 animate-pulse">{agentResponse}</p>
            ) : (
              <p className="text-xs text-gray-300 whitespace-pre-wrap">{agentResponse}</p>
            )}
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
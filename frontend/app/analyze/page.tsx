'use client';

import React, { useState } from 'react';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function AnalyzePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleTestAnalysis = () => {
    setIsLoading(true);
    
    // Simulate analysis generation
    setTimeout(() => {
      const analysisContent = `High Priority Alert\nRisk Score: 87/100\n\nVessel: MMSI: 123456789\nActivity: Suspected IUU Fishing\nLocation: Bodega Bay, California\n\nKey Indicators:\n• Vessel showing fishing-like behavior patterns\n• Speed profile indicates trawling activity\n• Located within Marine Protected Area\n• AIS transmission gaps detected\n• Satellite imagery shows vessel activity during dark period\n\nAnalysis complete! I've detected suspicious vessel activity in Bodega Bay. Would you like me to explain any specific aspect of this analysis?`;

      const analysisMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: analysisContent,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, analysisMessage]);
      setIsLoading(false);
    }, 2000);
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const responses = [
        "Based on the vessel's speed profile and heading changes, this appears to be typical trawling behavior. The vessel is moving at 2-4 knots with frequent course corrections, which matches fishing patterns.",
        "The satellite imagery shows the vessel was active during a period when its AIS was offline, indicating potential 'dark activity' - a common sign of illegal fishing operations.",
        "The vessel is currently positioned within the Bodega Bay Marine Protected Area where commercial fishing is prohibited. This constitutes a clear violation of maritime law.",
        "The risk score of 87/100 is based on multiple factors: location violation (40 points), dark activity (25 points), fishing behavior patterns (15 points), and historical data (7 points).",
        "I recommend immediate dispatch of patrol units to intercept this vessel. The evidence suggests ongoing illegal fishing activity that poses a threat to marine conservation efforts."
      ];

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-black text-white font-sans">
      {/* Left Panel - Analysis Chat */}
      <div className="flex-1 flex flex-col border-r border-gray-800">
        {/* Header */}
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-2xl font-semibold">Expansi Analysis Center</h1>
          <p className="text-sm text-gray-400">AI-powered maritime surveillance analysis</p>
        </div>

        {/* Test Button */}
        <div className="p-4 border-b border-gray-800">
          <button
            onClick={handleTestAnalysis}
            disabled={isLoading}
            className="w-full bg-black hover:bg-white disabled:bg-black border border-gray-700 hover:text-black text-white font-medium py-3 px-4 rounded-lg transition-colors"
          >
            {isLoading ? 'Running Analysis...' : 'Run Test Analysis'}
          </button>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] p-3 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-white text-black'
                    : 'bg-black border border-gray-800 text-white'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs text-gray-500 text-right mt-1.5">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-black p-3 rounded-lg border border-gray-800">
                <div className="flex space-x-1.5">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-800">
          <div className="flex space-x-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about the analysis..."
              className="flex-1 bg-black border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-600 focus:border-transparent"
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={isLoading || !inputValue.trim()}
              className="bg-white hover:bg-gray-300 disabled:bg-gray-800 disabled:text-gray-500 text-black px-5 py-2 rounded-lg transition-colors"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      {/* Right Panel - Mapbox Placeholder */}
      <div className="flex-1 bg-black/50 relative">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center p-8 bg-black/50 rounded-lg border border-gray-800">
            <div className="w-16 h-16 bg-gray-900 rounded-lg mx-auto mb-4 flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Mapbox Integration</h3>
            <p className="text-sm text-gray-500 mb-4">Interactive maritime surveillance map</p>
            <div className="bg-black rounded-lg p-4 max-w-sm mx-auto border border-gray-800">
              <p className="text-xs text-gray-400 mb-2">Features to be implemented:</p>
              <ul className="text-xs text-gray-400 space-y-1 text-left">
                <li>• Real-time vessel tracking</li>
                <li>• AIS data visualization</li>
                <li>• Satellite detection overlay</li>
                <li>• Marine Protected Areas</li>
                <li>• Alert markers and zones</li>
              </ul>
            </div>
          </div>
        </div>
        
        {/* Mapbox attribution placeholder */}
        <div className="absolute bottom-4 right-4 text-xs text-gray-500">
          <div className="bg-black/50 px-2 py-1 rounded">
            <span className="font-bold">mapbox</span>
          </div>
        </div>
      </div>
    </div>
  );
}

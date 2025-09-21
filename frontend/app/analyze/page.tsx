'use client';

import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import { useAuth } from '@/hooks/useAuth';

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
  const [selectedTarget, setSelectedTarget] = useState<string | null>(null);
  const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lng: number } | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    if (!mapContainerRef.current) return;

    const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN as string | undefined;
    if (!token) {
      console.warn('Missing NEXT_PUBLIC_MAPBOX_TOKEN');
      return;
    }
    mapboxgl.accessToken = token;

    mapRef.current = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/tcytseven/cmfscq4hy003901qpcl7m8jlb',
      center: [-79.5, 31.5],
      zoom: 5.25,
      bearing: 0,
      pitch: 0
    });

    mapRef.current.on('load', () => {
      // Fit to Southeast US coastal area similar to screenshot (FL to NC)
      try {
        mapRef.current!.fitBounds([
          [-84.5, 24.5], // SW (Gulf side south FL)
          [-74.0, 36.8]  // NE (offshore NC)
        ], { padding: 40, animate: false });
      } catch {}
      // Attach popups to symbol/circle layers from the style (cover both 'yummy' and 'dummy')
      const style = mapRef.current!.getStyle();
      const targetLayerIds = (style.layers || [])
        .filter((l: any) => (l.type === 'circle' || l.type === 'symbol') && ['yummy','dummy'].includes(l['source-layer']))
        .map((l) => l.id);

      targetLayerIds.forEach((layerId) => {
        // Hide features with disallowed names so icons don't render
        try {
          const existing = mapRef.current!.getFilter(layerId) as any;
          const nameExpr: any = ['downcase', ['coalesce',
            ['to-string', ['get', 'name']],
            ['to-string', ['get', 'title']],
            ['to-string', ['get', 'vesselName']],
            ['to-string', ['get', 'vessel_name']],
            ['to-string', ['get', 'shipname']],
            ''
          ]];
          const notBanned: any = ['all',
            ['!=', nameExpr, 'unknown'],
            ['!=', nameExpr, 'speed boat'],
            ['!=', nameExpr, 'speedboat'],
            ['!=', nameExpr, 'speed-boat'],
            ['!=', nameExpr, 'speed_boat'],
            ['!=', nameExpr, 'tourist cruise'],
            ['!=', nameExpr, 'touristcruise'],
            ['!=', nameExpr, 'tourist-cruise'],
            ['!=', nameExpr, 'tourist_cruise'],
            ['!=', nameExpr, '']
          ];
          const combined = existing ? ['all', existing as any, notBanned] : notBanned;
          mapRef.current!.setFilter(layerId, combined as any);
        } catch {}

        mapRef.current!.on('click', layerId, (e: any) => {
          const f = e.features?.[0];
          if (!f) return;
          const props: any = f.properties || {};
          const rawNameValue = props.name ?? props.title ?? props.vesselName ?? props.vessel_name ?? props.shipname ?? '';
          const rawName = String(rawNameValue);
          const normalized = rawName
            .normalize('NFKC')
            .replace(/[\u200B-\u200D\uFEFF]/g, '')
            .replace(/[_-]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim()
            .toLowerCase();
          if (normalized === 'unknown' || normalized === 'speed boat' || normalized === 'speedboat' || normalized === 'tourist cruise') {
            return; // Do not display these
          }
          const title = (rawName && rawName.trim()) || 'Vessel';
          const classification = props.classification || props.category || 'not fishing';
          const rawConfidence = typeof props.confidence === 'number' ? props.confidence : (props.confidence ? Number(props.confidence) : 0.85);
          const confidencePct = isFinite(rawConfidence) ? (rawConfidence <= 1 ? rawConfidence * 100 : rawConfidence) : 85;
          const vesselLengthMeters = props.vesselLengthMeters ?? props.length ?? 50;
          const timestamp = props.timestamp || new Date().toISOString();

          // Use actual clicked coordinates for accurate alignment
          const lngLat = [e.lngLat.lng, e.lngLat.lat] as [number, number];

              // Format fields for better readability
              const dt = new Date(timestamp);
              const formatted = isNaN(dt.getTime())
                ? timestamp
                : dt.toLocaleString(undefined, {
                    year: 'numeric', month: 'short', day: '2-digit',
                    hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'UTC'
                  });
              const roundedLng = lngLat[0].toFixed(2);
              const roundedLat = lngLat[1].toFixed(2);

              const html = `
                <div class="popup-card">
                  <div class="popup-title">${title}</div>
                  <div class="popup-dl">
                    <div class="row"><dt>Location</dt><dd>${roundedLng}, ${roundedLat}</dd></div>
                  </div>
                </div>`;
          new mapboxgl.Popup({ className: 'expansi-popup', maxWidth: '220px' })
            .setLngLat(lngLat)
            .setHTML(html)
            .addTo(mapRef.current!);

          setSelectedTarget(title);
          setSelectedLocation({ lng: lngLat[0], lat: lngLat[1] });
          setMessages((prev) => [
            ...prev,
            { id: Date.now().toString(), type: 'assistant', content: `Vessel selected: ${title}`, timestamp: new Date() }
          ]);
        });

        // Cursor feedback
        mapRef.current!.on('mouseenter', layerId, () => {
          mapRef.current!.getCanvas().style.cursor = 'pointer';
        });
        mapRef.current!.on('mouseleave', layerId, () => {
          mapRef.current!.getCanvas().style.cursor = '';
        });
      });
    });

    return () => {
      try { mapRef.current?.remove(); } catch {}
    };
  }, []);

  const handleApiCall = async (prompt: string, location?: { lat: number, lng: number } | null) => {
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/ai/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          user_id: user?.sub || 'anonymous',
          location: location || undefined
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const assistantMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: data.content,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      
      if (data.type === 'location' && data.data) {
        const { lat, lng } = data.data;
        if (mapRef.current && typeof lat === 'number' && typeof lng === 'number') {
            mapRef.current.flyTo({
                center: [lng, lat],
                zoom: 12,
                essential: true
            });
        }
      }

    } catch (error) {
      console.error("Failed to fetch analysis:", error);
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'assistant',
        content: "Sorry, I couldn't get a response from the server. Please try again later.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestAnalysis = () => {
    const prompt = selectedTarget 
      ? `Run analysis on ${selectedTarget}` 
      : 'Generate the weekly IUU report';
    
    const userMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'user',
        content: prompt,
        timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    handleApiCall(prompt, selectedLocation);
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
    handleApiCall(userMessage.content);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-black text-white font-sans relative" style={{marginLeft:"104px"}}>
      {/* Left Panel - Analysis Chat */}
      <div className={`w-1/2 flex flex-col h-screen`}> 
        {/* Header */}
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-2xl font-semibold">OverSea Analysis Center</h1>
          <p className="text-sm text-gray-400">AI-powered maritime surveillance analysis</p>
        </div>

        {/* Test Button */}
        <div className="p-4 border-b border-gray-800">
          <button
            onClick={handleTestAnalysis}
            disabled={isLoading}
            className="w-full bg-black hover:bg-white disabled:bg-black border border-gray-700 hover:text-black text-white font-medium py-3 px-4 rounded-lg transition-colors"
          >
            {isLoading ? 'Running Analysis...' : selectedTarget ? `Run Analysis On ${selectedTarget}` : 'Run Analysis'}
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

      {/* Vertical Separator */}
      <div className="w-px bg-gradient-to-b from-white/10 via-white/20 to-white/10" />

      {/* Right Panel - Mapbox */}
      <div className={`w-1/2 bg-black relative h-screen`}>
        <div ref={mapContainerRef} className="absolute inset-0" style={{ height: '100%' }} />
      </div>

      {/* Center fade between chat and map (very subtle, non-interactive) */}
      <div className="pointer-events-none absolute inset-y-0 left-1/2 -translate-x-1/2 w-12 bg-gradient-to-r from-transparent via-black/40 to-transparent" />
    </div>
  );
}

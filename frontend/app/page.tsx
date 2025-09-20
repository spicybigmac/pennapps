'use client';

import dynamic from 'next/dynamic';
import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import * as topojson from 'topojson-client';

const Globe = dynamic(() => import('react-globe.gl'), { ssr: false });

interface VesselData {
  lat: number;
  lng: number;
  isfishing: boolean;
  legal: boolean;
  id: string; 
}

interface ClusterData {
  lat: number;
  lng: number;
  count: number;
  markers: VesselData[];
  isfishing: boolean;
  legal: boolean;
  closest: number;
}

const HomePage: React.FC = () => {
  const globeEl = useRef<any>(null);
  const [landData, setLandData] = useState<{ features: any[] }>({ features: [] });
  const [vesselData, setVesselData] = useState<VesselData[]>([]);
  const [clusteredData, setClusteredData] = useState<ClusterData[]>([]);
  const [clusterThreshold, setClusterThreshold] = useState(0);
  const [hoveredVessel, setHoveredVessel] = useState<VesselData | null>(null);
  const [popupPosition, setPopupPosition] = useState<{ x: number; y: number } | null>(null);
  const [showAgentChat, setShowAgentChat] = useState(false);
  const [agentChatVessel, setAgentChatVessel] = useState<VesselData | null>(null); // New state for vessel in chat

  const [chatWindowPosition, setChatWindowPosition] = useState({ x: 20, y: 20 });
  const [isDragging, setIsDragging] = useState(false);
  const dragOffset = useRef({ x: 0, y: 0 });
  const chatWindowRef = useRef<HTMLDivElement>(null);

  const markerSvg = `<svg viewBox="-4 0 36 36">
    <path fill="currentColor" d="M14,0 C21.732,0 28,5.641 28,12.6 C28,23.963 14,36 14,36 C14,36 0,24.064 0,12.6 C0,5.641 6.268,0 14,0 Z"></path>
    <circle fill="black" cx="14" cy="14" r="7"></circle>
  </svg>`;

  const clusterSvg = (count: number) => `<svg viewBox="-4 0 36 36">
    <path fill="currentColor" d="M14,0 C21.732,0 28,5.641 28,12.6 C28,23.963 14,36 14,36 C14,36 0,24.064 0,12.6 C0,5.641 6.268,0 14,0 Z"></path>
    <circle fill="black" cx="14" cy="14" r="7"></circle>
    <text x="14" y="18" text-anchor="middle" fill="white" font-size="10" font-weight="bold">${count}</text>
  </svg>`;

  const clusterMarkers = (markers: VesselData[], clusterThreshold: number = 1200) => {
    if (markers.length === 0) return [];
    
    const clusters: ClusterData[] = [];
    const processed = new Set<number>();
    
    for (let index = 0; index < markers.length; index++) {
      if (processed.has(index)) continue;
      
      const marker = markers[index];
      const cluster: ClusterData = {
        lat: marker.lat,
        lng: marker.lng,
        count: 1,
        markers: [marker],
        isfishing: marker.isfishing,
        legal: marker.legal,
        closest: Infinity
      };
      
      for (let otherIndex = 0; otherIndex < markers.length; otherIndex++) {
        if (otherIndex === index || processed.has(otherIndex)) continue;
        
        const otherMarker = markers[otherIndex];
        
        const R = 6371;
        const dLat = (otherMarker.lat - marker.lat) * Math.PI / 180;
        const dLng = (otherMarker.lng - marker.lng) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(marker.lat * Math.PI / 180) * Math.cos(otherMarker.lat * Math.PI / 180) *
                  Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        const distance = R * c;
        
        if (distance < clusterThreshold) {
          cluster.count++;
          cluster.markers.push(otherMarker);
          processed.add(otherIndex);
          cluster.legal = cluster.legal && otherMarker.legal
          cluster.closest = Math.min(cluster.closest, distance);
        }
      }

      if (cluster.markers.length > 1) {
        let x = 0, y = 0, z = 0;
        for (const m of cluster.markers) {
          const latRad = m.lat * Math.PI / 180;
          const lngRad = m.lng * Math.PI / 180;
          x += Math.cos(latRad) * Math.cos(lngRad);
          y += Math.cos(latRad) * Math.sin(lngRad);
          z += Math.sin(latRad);
        }
        const total = cluster.markers.length;
        x /= total;
        y /= total;
        z /= total;

        const norm = Math.sqrt(x * x + y * y + z * z);
        x /= norm;
        y /= norm;
        z /= norm;

        const lat = Math.asin(z) * 180 / Math.PI;
        const lng = Math.atan2(y, x) * 180 / Math.PI;
        cluster.lat = lat;
        cluster.lng = lng;
      }
      
      clusters.push(cluster);
      processed.add(index);
    }
    
    setClusteredData(clusters);
  };

  const handleZoom = (pov : any) => {
    const newThreshold = Math.min(5000, Math.round(500 * pov.altitude / 200) * 200);
    if(newThreshold != clusterThreshold){
      setClusterThreshold(newThreshold);
      clusterMarkers(vesselData, newThreshold);
    }
    setHoveredVessel(null);
    setPopupPosition(null);
    // Don't close chat on zoom, it's persistent now
  }

  const fetchData = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/getPositions', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await response.json();
      if (response.ok) {
        setVesselData(data);
        clusterMarkers(data);
      }
    } catch (error) {
      console.error('Error fetching vessel data:', error);
    }
  }

  useEffect(() => {
    fetch('https://cdn.jsdelivr.net/npm/world-atlas/land-110m.json')
      .then((res) => res.json())
      .then((landTopo) => {
        const featureCollection = topojson.feature(landTopo, landTopo.objects.land);
        setLandData(featureCollection as unknown as { features: any[] });
      });

    fetchData();
  }, []);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchData();
      }
    };

    const handleFocus = () => {
      fetchData();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  const handleOpenAgentChat = (vessel: VesselData) => {
    console.log(`Opening agent chat for vessel ID: ${vessel.id}`);
    setAgentChatVessel(vessel); // Set the vessel for the chat
    setShowAgentChat(true);
    setChatWindowPosition({ x: 20, y: 20 }); // Reset position when opening for a new vessel
  };

  const closeAgentChat = () => {
    setShowAgentChat(false);
    setAgentChatVessel(null); // Clear the vessel when chat is closed
  };

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    if (chatWindowRef.current) {
      setIsDragging(true);
      const rect = chatWindowRef.current.getBoundingClientRect();
      dragOffset.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
      e.preventDefault();
    }
  }, []);

  const onMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging && chatWindowRef.current) {
      const x = e.clientX - dragOffset.current.x;
      const y = e.clientY - dragOffset.current.y;
      
      const chatRect = chatWindowRef.current.getBoundingClientRect();
      const maxX = window.innerWidth - chatRect.width;
      const maxY = window.innerHeight - chatRect.height;

      setChatWindowPosition({
        x: Math.max(0, Math.min(x, maxX)),
        y: Math.max(0, Math.min(y, maxY)),
      });
    }
  }, [isDragging]);

  const onMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    } else {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
  }, [isDragging, onMouseMove, onMouseUp]);

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', overflow: 'hidden' }}>
      <Globe
        ref={globeEl}
        globeImageUrl={null}
        bumpImageUrl={null}
        backgroundImageUrl={null}
        showGlobe={false}
        showAtmosphere={false}
        backgroundColor={'rgba(0,0,0,0)'}

        polygonsData={landData.features}
        polygonCapColor={() => 'rgba(130, 130, 130, 0.5)'}
        polygonSideColor={() => 'rgba(0,0,0,0)'}
        polygonAltitude={0}
        polygonStrokeColor={() => 'rgba(255, 255, 255, 1)'}

        showGraticules={true}

        htmlElementsData={clusteredData}
        htmlElement={(d: any) => {
          const el = document.createElement('div');
          if (d.count > 1) {
            el.innerHTML = clusterSvg(d.count);
          } else {
            el.innerHTML = markerSvg;
          }
          
          el.style.color = d.legal ? "#41fc03" : "#fc0303";
          el.style.width = d.count > 1 ? `40px` : `30px`;
          el.style.height = 'auto';
          el.style.transition = 'opacity 250ms';
          el.style.cursor = 'pointer';
          el.style.pointerEvents = 'auto';
          
          el.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            // Do not close chat automatically on marker click
            
            if (d.count == 1) {
              setHoveredVessel(d.markers[0]);
              
              const popupHeight = 300;
              const popupWidth = 320;
              const screenHeight = window.innerHeight;
              const screenWidth = window.innerWidth;
              
              let x = e.clientX + 15;
              let y = e.clientY - 10;
              
              if (x + popupWidth > screenWidth) {
                x = e.clientX - popupWidth - 15;
              }
              
              if (e.clientY > screenHeight / 2) {
                y = e.clientY - popupHeight - 10;
              } else {
                y = e.clientY - 10;
              }
              
              y = Math.max(10, Math.min(y, screenHeight - popupHeight - 10));
              x = Math.max(10, Math.min(x, screenWidth - popupWidth - 10));
              
              setPopupPosition({ x, y });
            } else {
              if (globeEl.current) {
                const currentPov = globeEl.current.pointOfView();
                const targetPov = {
                  lat: d.lat,
                  lng: d.lng,
                  altitude: Math.min(5000, d.closest) / 500 * 0.5
                };

                const duration = 1200;
                const start = performance.now();

                function animateZoom(now: number) {
                  const t = Math.min((now - start) / duration, 1);
                  const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
                  const pov = {
                    lat: currentPov.lat + (targetPov.lat - currentPov.lat) * ease,
                    lng: currentPov.lng + (targetPov.lng - currentPov.lng) * ease,
                    altitude: currentPov.altitude + (targetPov.altitude - currentPov.altitude) * ease
                  };
                  globeEl.current.pointOfView(pov);
                  if (t < 1) {
                    requestAnimationFrame(animateZoom);
                  }
                }
                requestAnimationFrame(animateZoom);
              }
            }
          });
          
          return el;
        }}
        htmlElementVisibilityModifier={(el : any, isVisible : Boolean) => {
          if(isVisible){
            el.style.opacity = '1';
            el.style['pointer-events'] = 'auto';
          } else {
            el.style.opacity = '0';
            el.style['pointer-events'] = 'none';
          }
        }}
      
        onGlobeReady={()=>{clusterMarkers(vesselData)}}
        onZoom={(pov) => {handleZoom(pov)}}
      />
      
      {/* Vessel information popup */}
      {hoveredVessel && popupPosition && (
        <div
          data-popup="vessel-info"
          style={{
            position: 'fixed',
            left: popupPosition.x + 15,
            top: popupPosition.y - 10,
            backgroundColor: 'rgba(0, 0, 0, 0.95)',
            color: 'white',
            padding: '20px',
            borderRadius: '12px',
            fontSize: '14px',
            fontFamily: 'Arial, sans-serif',
            zIndex: 1000,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            maxWidth: '320px',
            minWidth: '280px',
            backdropFilter: 'blur(10px)'
          }}
        >

          <div style={{ fontWeight: 'bold', marginBottom: '12px', color: hoveredVessel.legal ? '#0ff736ff' : '#ff3030ff', fontSize: '16px' }}>
            {hoveredVessel.legal ? 'Registered' : 'Unregistered'}
          </div>

          <div
            style={{
              width: '100%',
              height: '120px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              borderRadius: '8px',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px dashed rgba(255, 255, 255, 0.3)',
              color: 'rgba(255, 255, 255, 0.6)',
              fontSize: '12px'
            }}
          >
            📷 Vessel Image Placeholder
          </div>
          
          <div style={{ marginBottom: '10px' }}>
            <strong>Location:</strong> {hoveredVessel.lat.toFixed(4)}°, {hoveredVessel.lng.toFixed(4)}°
          </div>
          
          <div style={{ marginBottom: '10px' }}>
            <strong>Status:</strong> 
            <span style={{ 
              color: hoveredVessel.isfishing ? '#ff3030ff' : '#0ff736ff',
              marginLeft: '8px',
              fontWeight: 'bold'
            }}>
              {hoveredVessel.isfishing ? 'Fishing' : 'Not Fishing'}
            </span>
          </div>
          
          {!hoveredVessel.legal && (
            <button
              onClick={() => handleOpenAgentChat(hoveredVessel)} // Pass the whole vessel object
              style={{
                width: '100%',
                padding: '10px 16px',
                backgroundColor: '#ff3030ff',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                marginBottom: '10px'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#be2424ff';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#ff3030ff';
              }}
            >
              Open Agent Chat
            </button>
          )}

          <button
            onClick={() => {
              setHoveredVessel(null);
              setPopupPosition(null);
              // Do not close chat here, it's independent
            }}
            style={{
              width: '100%',
              padding: '10px 16px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '500',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
            }}
          >
            Close
          </button>
        </div>
      )}

      {/* Agent Chat Interface */}
      {showAgentChat && agentChatVessel && (
        <div
          ref={chatWindowRef}
          style={{
            position: 'fixed',
            top: chatWindowPosition.y,
            left: chatWindowPosition.x,
            width: '350px',
            height: '500px',
            backgroundColor: 'rgba(30, 30, 30, 0.98)',
            color: 'white',
            borderRadius: '12px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            zIndex: 1001,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
        >
          <div
            style={{
              padding: '15px',
              backgroundColor: '#ff3030ff',
              borderTopLeftRadius: '12px',
              borderTopRightRadius: '12px',
              fontWeight: 'bold',
              fontSize: '16px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'grab',
            }}
            onMouseDown={onMouseDown}
          >
            Agent Chat - Vessel {agentChatVessel.id || 'Unknown'}
            <button
              onClick={closeAgentChat} // Use the new close chat function
              style={{
                background: 'none',
                border: 'none',
                color: 'white',
                fontSize: '18px',
                cursor: 'pointer',
              }}
            >
              &times;
            </button>
          </div>
          <div style={{ flexGrow: 1, padding: '15px', overflowY: 'auto', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <p style={{ margin: '0 0 10px 0', color: '#ccc' }}>Agent: Hello! How can I assist you with vessel {agentChatVessel.id}?</p>
            <p style={{ margin: '0 0 10px 0', textAlign: 'right', color: '#add8e6' }}>You: I need more information on its recent activities.</p>
          </div>
          <div style={{ padding: '15px', display: 'flex', borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
            <input
              type="text"
              placeholder="Type your message..."
              style={{
                flexGrow: 1,
                padding: '10px',
                borderRadius: '6px',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                color: 'white',
                marginRight: '10px',
                fontSize: '14px',
              }}
            />
            <button
              style={{
                padding: '10px 15px',
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#218838';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#28a745';
              }}
            >
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
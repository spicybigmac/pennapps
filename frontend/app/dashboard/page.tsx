'use client';

import dynamic from 'next/dynamic';
import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react'; // Added useCallback, useMemo
import * as topojson from 'topojson-client';
import AgentPanel, { type AgentPoint } from '../../components/AgentPanel';
import { useAuth } from '../../hooks/useAuth';
import ReactCountryFlag from 'react-country-flag';

const Globe = dynamic(() => import('react-globe.gl'), { ssr: false });

interface VesselData {
  lat: number;
  lng: number;
  registered: boolean;
  timestamp: string;
  geartype: string;
  mmsi: string;
  imo: string;
  shipName: string;
  flag: string;
}

interface ClusterData {
  lat: number;
  lng: number;
  count: number;
  markers: VesselData[];
  registered: boolean;
  closest: number;
}

interface HotspotData {
  lat: number;
  lng: number;
  size: number;
}

const HomePage: React.FC = () => {
  const GREEN = "#2eb700";
  const RED = "#fc0303";
  const DARK_RED = "#bf0202";

  const globeEl = useRef<any>(null);
  const [landData, setLandData] = useState<{ features: any[] }>({ features: [] });
  const [vesselData, setVesselData] = useState<VesselData[]>([]);

  const [clusteredData, setClusteredData] = useState<ClusterData[]>([]);
  const [hoveredVessel, setHoveredVessel] = useState<VesselData | null>(null);
  const [popupPosition, setPopupPosition] = useState<{ x: number; y: number } | null>(null);

  const [hotspotData, setHotspotData] = useState<HotspotData[]>([]);
  const [isDataLoaded, setIsDataLoaded] = useState(false);
  const [isFirstLoad, setIsFirstLoad] = useState(true);

  // Agent panel state
  const [agentPoint, setAgentPoint] = useState<AgentPoint | null>(null);
  const [isAgentPanelOpen, setIsAgentPanelOpen] = useState(false);

  // Auth state
  const { user, hasAnyRole } = useAuth();

  // Timestamp slider state
  const [minTimestamp, setMinTimestamp] = useState<number>(0); // Unix timestamp
  const [maxTimestamp, setMaxTimestamp] = useState<number>(1e15); // Unix timestamp
  const [timeL, setTimeL] = useState<number>(0);
  const [timeR, setTimeR] = useState<number>(1e15);

  const [showRegistered, setShowRegistered] = useState<Boolean>(true);

  const markerSvg = `<svg viewBox="-4 0 36 36">
    <path fill="currentColor" d="M14,0 C21.732,0 28,5.641 28,12.6 C28,23.963 14,36 14,36 C14,36 0,24.064 0,12.6 C0,5.641 6.268,0 14,0 Z"></path>
    <circle fill="black" cx="14" cy="14" r="7"></circle>
  </svg>`;

  const clusterSvg = (count: number) => `<svg viewBox="-4 0 36 36">
    <path fill="currentColor" d="M14,0 C21.732,0 28,5.641 28,12.6 C28,23.963 14,36 14,36 C14,36 0,24.064 0,12.6 C0,5.641 6.268,0 14,0 Z"></path>
    <circle fill="black" cx="14" cy="14" r="7"></circle>
    <text x="14" y="18" text-anchor="middle" fill="white" font-size="12" font-weight="bold">${count}</text>
  </svg>`;

  const clusterBase = 1500;
  const cullingBase = 7000;

  const clusterMarkers = useCallback((markers: VesselData[], cull=true) => {
    if (markers.length === 0) return;

    const pov = globeEl.current ? globeEl.current.pointOfView() : { lat: 0, lng: 0, altitude: 2.5 };
    const clusterThreshold = Math.min(10000, clusterBase * pov.altitude);
    const cullingThreshold = Math.max(1, Math.min(70000, cullingBase * pov.altitude));

    const clusters: ClusterData[] = [];
    const processed = new Set<number>();

    for (let index = 0; index < markers.length; index++) {
      if (processed.has(index)) continue;

      const marker = markers[index];

      if(marker.registered && !showRegistered) continue;
      if (!marker.registered && !hasAnyRole(['confidential', 'secret', 'top-secret'])) continue;

      const v = new Date(marker.timestamp).getTime();
      if(timeL > v || timeR < v) continue;

      if(cull){
        const R = 6371;
        const dLat = (pov.lat - marker.lat) * Math.PI / 180;
        const dLng = (pov.lng - marker.lng) * Math.PI / 180;
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(marker.lat * Math.PI / 180) * Math.cos(pov.lat * Math.PI / 180) *
                  Math.sin(dLng / 2) * Math.sin(dLng / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const distance = R * c;
        if (distance > cullingThreshold) continue;
      }

      const cluster: ClusterData = {
        lat: marker.lat,
        lng: marker.lng,
        count: 1,
        markers: [marker],
        registered: marker.registered,
        closest: Infinity
      };

      for (let otherIndex = 0; otherIndex < markers.length; otherIndex++) {
        if (otherIndex === index || processed.has(otherIndex)) continue;

        const otherMarker = markers[otherIndex];

        if (cluster.registered !== otherMarker.registered) continue;

        const R_other = 6371;
        const dLat_other = (otherMarker.lat - marker.lat) * Math.PI / 180;
        const dLng_other = (otherMarker.lng - marker.lng) * Math.PI / 180;
        const a_other = Math.sin(dLat_other / 2) * Math.sin(dLat_other / 2) +
                        Math.cos(marker.lat * Math.PI / 180) * Math.cos(otherMarker.lat * Math.PI / 180) *
                        Math.sin(dLng_other / 2) * Math.sin(dLng_other / 2);
        const c_other = 2 * Math.atan2(Math.sqrt(a_other), Math.sqrt(1 - a_other));
        const distance_other = R_other * c_other;

        if (distance_other < clusterThreshold) {
          cluster.count++;
          cluster.markers.push(otherMarker);
          processed.add(otherIndex);
          cluster.registered = cluster.registered && otherMarker.registered;
          cluster.closest = Math.min(cluster.closest, distance_other);
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

        var mndis = Infinity;

        for (const m of cluster.markers) {
          const R_centroid = 6371;
          const dLat_centroid = (lat - m.lat) * Math.PI / 180;
          const dLng_centroid = (lng - m.lng) * Math.PI / 180;
          const a_centroid = Math.sin(dLat_centroid / 2) * Math.sin(dLat_centroid / 2) +
                             Math.cos(m.lat * Math.PI / 180) * Math.cos(lat * Math.PI / 180) *
                             Math.sin(dLng_centroid / 2) * Math.sin(dLng_centroid / 2);
          const c_centroid = 2 * Math.atan2(Math.sqrt(a_centroid), Math.sqrt(1 - a_centroid));
          const distance_centroid = R_centroid * c_centroid;
          if (distance_centroid < mndis) {
            mndis = distance_centroid;
            cluster.lat = m.lat;
            cluster.lng = m.lng;
          }
        }
      }

      clusters.push(cluster);
      processed.add(index);
    }

    setClusteredData(clusters);
  }, [globeEl, timeL, timeR, showRegistered]);

  const handleZoom = useCallback(() => { // Removed `pov` as it's not used directly from the param
    clusterMarkers(vesselData); // Cluster filtered data
    setHoveredVessel(null);
    setPopupPosition(null);
  }, [clusterMarkers, vesselData]);

  const fetchData = useCallback(async () => {
    setIsDataLoaded(false);
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/getPositions', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      const data: VesselData[] = await response.json();
      if (response.ok) {
        setVesselData(data);

        // Extract all timestamps and set min/max for the slider
        const timestamps = data.map(v => new Date(v.timestamp).getTime()).sort();
        if (timestamps.length > 0) {
          setMinTimestamp(timestamps[0]);
          setMaxTimestamp(timestamps[timestamps.length - 1]);
          
          setTimeL(timestamps[0]);
          setTimeR(timestamps[timestamps.length - 1]);
          const mn : any = document.getElementById("min-timestamp");
          const mx : any = document.getElementById("max-timestamp");
          mn.value = timestamps[0];
          mx.value = timestamps[timestamps.length - 1];

          setShowRegistered(true);
          const toggler : any = document.getElementById("toggle-registered");
          toggler.checked = true;
        }

        clusterMarkers(vesselData);
        setIsDataLoaded(true);
        setIsFirstLoad(false);
      }
    } catch (error) {
      console.log('Error fetching vessel data:', error);
      setIsDataLoaded(true); // Set to true even on error to show the interface
      setIsFirstLoad(false);
    }

    try {
      const response = await fetch('http://127.0.0.1:8000/api/hotspots/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      const data: any = await response.json();
      if(response.ok){
        setHotspotData(data["hotspots"]);
        console.log(data,data["hotspots"]);
      }
    } catch (error) {
      console.log('Error fetching hotspot data:', error);
    }
  }, []);

  useEffect(() => {
    fetch('https://cdn.jsdelivr.net/npm/world-atlas/land-110m.json')
      .then((res) => res.json())
      .then((landTopo) => {
        const featureCollection = topojson.feature(landTopo, landTopo.objects.land);
        setLandData(featureCollection as unknown as { features: any[] });
      });

    fetchData();
  }, [fetchData]);

  // Re-cluster whenever vesselData changes
  useEffect(() => {
    clusterMarkers(vesselData);
  }, [vesselData, clusterMarkers]);

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
  }, [fetchData]);

  // Helper to format timestamp for display
  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toISOString().split('T')[0];
  };

  const handleSliderChange = (event: React.ChangeEvent<HTMLInputElement>, type: 'min' | 'max') => {
    const value = parseInt(event.target.value);

    if (type === 'min') {
      setTimeL(value);
    } else {
      setTimeR(value);
    }
  };

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', overflow: 'hidden' }}>
      {!isDataLoaded && isFirstLoad ? (
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#000',
          color: 'white',
          fontSize: '18px',
          fontFamily: 'Arial, sans-serif'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              width: '40px', 
              height: '40px', 
              border: '3px solid #333', 
              borderTop: '3px solid #fff', 
              borderRadius: '50%', 
              animation: 'spin 1s linear infinite',
              margin: '0 auto 20px'
            }}></div>
            Loading vessel data...
          </div>
        </div>
      ) : (
        <>
          <div style={{
            position: 'absolute',
            inset: 0
          }}>
            <Globe
          ref={globeEl}
          globeImageUrl={null}
          bumpImageUrl={null}
          backgroundImageUrl={"night-sky.png"}
          showGlobe={false}
          showAtmosphere={false}
          backgroundColor={'rgba(0,0,0,0)'}

          polygonsData={landData.features}
          polygonCapColor={() => 'rgba(130, 130, 130, 0.5)'}
          polygonSideColor={() => 'rgba(0,0,0,0)'}
          polygonAltitude={0}
          polygonStrokeColor={() => 'rgba(255, 255, 255, 1)'}

          ringsData={hotspotData}
          ringLat="lat"
          ringLng="lon"
          ringAltitude={0}
          ringColor={() => "rgba(255,0,0,1)"}
          ringMaxRadius={(e:any)=>300*e.size}
          ringPropagationSpeed={(e:any)=>300*e.size/5}
          ringRepeatPeriod={1000}

          showGraticules={true}

          htmlElementsData={clusteredData}
          htmlElement={(d: any) => {
            const el = document.createElement('div');
            if (d.count > 1) {
              el.innerHTML = clusterSvg(d.count);
            } else {
              el.innerHTML = markerSvg;
            }

            el.style.color = d.registered ? GREEN : RED;
            el.style.width = `${40 + d.count / 200}px`;
            el.style.height = 'auto';
            el.style.cursor = 'pointer';
            el.style.pointerEvents = 'auto';

            el.addEventListener('click', (e) => {
              e.preventDefault();
              e.stopPropagation();

              if (d.count === 1) {
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
                    altitude: Math.max(Math.min(10000, d.closest) / clusterBase * 0.5, currentPov.altitude * 0.2)
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
          htmlElementVisibilityModifier={(el: any, isVisible: Boolean) => {
            if (isVisible) {
              el.style.opacity = '1';
              el.style['pointer-events'] = 'auto';
            } else {
              el.style.opacity = '0';
              el.style['pointer-events'] = 'none';
            }
          }}

          onGlobeReady={() => { 
            clusterMarkers(vesselData); // Use filtered data on ready
            // Disable autorotation for dashboard
            if (globeEl.current) {
              globeEl.current.controls().autoRotate = false;
            }
          }}
          onZoom={() => { handleZoom(); }}
        />
          </div>

          {/* Vessel information popup */}
      {hoveredVessel && popupPosition && (
        <div
          data-popup="vessel-info"
          style={{
            position: 'fixed',
            left: popupPosition.x,
            top: popupPosition.y,
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

          <div style={{ fontWeight: 'bold', marginBottom: '12px', color: hoveredVessel.registered ? GREEN : RED, fontSize: '16px' }}>
            {hoveredVessel.registered ? hoveredVessel.shipName : '[UNREGISTERED VESSEL]'}
            <ReactCountryFlag countryCode={hoveredVessel.flag} style={{ float: 'right' }} />
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
            <strong>Timestamp:</strong> {hoveredVessel.timestamp}
          </div>

          {
            hoveredVessel.geartype !== "" ?
              <div style={{ marginBottom: '10px' }}>
                <strong>Geartype:</strong> {hoveredVessel.geartype}
              </div> : null
          }

          {!hoveredVessel.registered && hasAnyRole(['confidential', 'secret', 'top-secret']) && (
            <button
              onClick={() => {
                const ap: AgentPoint = {
                  lat: hoveredVessel.lat,
                  lng: hoveredVessel.lng,
                  timestamp: hoveredVessel.timestamp,
                  mmsi: hoveredVessel.mmsi,
                  imo: hoveredVessel.imo,
                  flag: hoveredVessel.flag,
                  shipName: hoveredVessel.shipName,
                  geartype: hoveredVessel.geartype
                };
                setAgentPoint(ap);
                setIsAgentPanelOpen(true);
                setHoveredVessel(null);
                setPopupPosition(null);
              }}
              style={{
                width: '100%',
                padding: '10px 16px',
                backgroundColor: RED,
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '600',
                marginBottom: '10px',
                transition: 'all 0.2s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = DARK_RED;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = RED;
              }}
            >
              Open Agent
            </button>
          )}

          <button
            onClick={() => {
              setHoveredVessel(null);
              setPopupPosition(null);
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

      {/* Rounded window for timestamp slider */}
    
      <div
        style={{
          position: 'fixed',
          right: '20px', // Move to top right corner
          top: '20px',   // Move to top right corner
          transform: 'none', // Remove translateY
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          color: 'white',
          padding: '20px',
          borderRadius: '15px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
          zIndex: 1000,
          maxWidth: '300px', // Make the window wider
          display: 'flex',
          flexDirection: 'column',
          gap: '15px',
          backdropFilter: 'blur(5px)',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <h3 style={{ margin: '0 0 10px 0', fontSize: '1.1em', textAlign: 'center' }}>Filters</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          <label htmlFor="min-timestamp" style={{ fontSize: '0.9em' }}>Start: {formatTimestamp(timeL)}</label>
          <input
            type="range"
            id="min-timestamp"
            min={minTimestamp}
            max={maxTimestamp}
            onChange={(e) => handleSliderChange(e, 'min')}
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
          <label htmlFor="max-timestamp" style={{ fontSize: '0.9em' }}>End: {formatTimestamp(timeR)}</label>
          <input
            type="range"
            id="max-timestamp"
            min={minTimestamp}
            max={maxTimestamp}
            onChange={(e) => handleSliderChange(e, 'max')}
            style={{ width: '100%' }}
          />
        </div>

        {/* New toggle button for registered markers */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '5px' }}>
          <label htmlFor="toggle-registered" style={{ fontSize: '0.9em' }}>Show Registered</label>
          <label className="switch">
            <input
              type="checkbox"
              id="toggle-registered"
              onChange={() => setShowRegistered(!showRegistered)}
            />
            <span className="slider round"></span>
          </label>
        </div>
        {/* End new toggle button */}

        {/* Stats below filter options */}
        <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.2)', paddingTop: '15px', marginTop: '10px' }}>
          <div style={{ marginBottom: '8px', fontSize: '0.9em' }}>
            <strong>Total Vessels:</strong> {vesselData.length}
          </div>
          <div style={{ marginBottom: '8px', fontSize: '0.9em' }}>
            <strong>Total Unregistered Vessels:</strong> {vesselData.filter(v => !v.registered).length}
          </div>
          <div style={{ fontSize: '0.9em' }}>
            <strong>% Unregistered:</strong> {vesselData.length > 0 ? ((vesselData.filter(v => !v.registered).length / vesselData.length) * 100).toFixed(2) : '0.00'}%
          </div>
        </div>
        {/* End Stats */}

        <button
          onClick={() => {
            // Reset to full range if needed, or trigger re-cluster explicitly
            setTimeL(minTimestamp);
            setTimeR(maxTimestamp);
            const mn : any = document.getElementById("min-timestamp");
            const mx : any = document.getElementById("max-timestamp");
            mn.value = minTimestamp;
            mx.value = maxTimestamp;

            setShowRegistered(true);
            const toggler : any = document.getElementById("toggle-registered");
            toggler.checked = true;
          }}
          style={{
            padding: '8px 12px',
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
            color: 'white',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '5px',
            cursor: 'pointer',
            fontSize: '0.9em',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'; }}
        >
          Reset Filters
        </button>
      </div>

          {/* Agent Panel */}
          <AgentPanel open={isAgentPanelOpen} point={agentPoint} onClose={() => setIsAgentPanelOpen(false)} />
        </>
      )}

      {(isDataLoaded || !isFirstLoad) && !hasAnyRole(['confidential', 'secret', 'top-secret']) && <div id="headsup"><p>Login to view unregistered vessels</p></div>}
    </div>
  );
};

export default HomePage;
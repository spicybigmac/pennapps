'use client';

import dynamic from 'next/dynamic';
import React, { useRef, useEffect, useState, useMemo } from 'react';
import * as topojson from 'topojson-client';

const Globe = dynamic(() => import('react-globe.gl'), { ssr: false });

interface VesselData {
  lat: number;
  lng: number;
  isfishing: boolean;
  legal: boolean;
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

  const markerSvg = `<svg viewBox="-4 0 36 36">
    <path fill="currentColor" d="M14,0 C21.732,0 28,5.641 28,12.6 C28,23.963 14,36 14,36 C14,36 0,24.064 0,12.6 C0,5.641 6.268,0 14,0 Z"></path>
    <circle fill="black" cx="14" cy="14" r="7"></circle>
  </svg>`;

  const clusterSvg = (count: number) => `<svg viewBox="-4 0 36 36">
    <path fill="currentColor" d="M14,0 C21.732,0 28,5.641 28,12.6 C28,23.963 14,36 14,36 C14,36 0,24.064 0,12.6 C0,5.641 6.268,0 14,0 Z"></path>
    <circle fill="black" cx="14" cy="14" r="7"></circle>
    <text x="14" y="18" text-anchor="middle" fill="white" font-size="10" font-weight="bold">${count}</text>
  </svg>`;

  // Clustering algorithm based on visual distance
  const clusterMarkers = (markers: VesselData[], clusterThreshold: number = 1200) => {
    if (markers.length === 0) return [];
    
    // Cluster threshold based on zoom level - higher zoom = smaller threshold
    // This creates a more aggressive clustering when zoomed out
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
      
      // Find nearby markers to cluster
      for (let otherIndex = 0; otherIndex < markers.length; otherIndex++) {
        if (otherIndex === index || processed.has(otherIndex)) continue;
        
        const otherMarker = markers[otherIndex];
        
        // Calculate distance using Haversine formula for more accurate geographic distance
        const R = 6371; // Earth's radius in kilometers
        const dLat = (otherMarker.lat - marker.lat) * Math.PI / 180;
        const dLng = (otherMarker.lng - marker.lng) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(marker.lat * Math.PI / 180) * Math.cos(otherMarker.lat * Math.PI / 180) *
                  Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        const distance = R * c; // Distance in kilometers
        
        if (distance < clusterThreshold) {
          cluster.count++;
          cluster.markers.push(otherMarker);
          processed.add(otherIndex);
          cluster.legal = cluster.legal && otherMarker.legal
          cluster.closest = Math.min(cluster.closest, distance);
        }
      }

      // Calculate average position of cluster markers on the sphere
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

        // Normalize to unit vector
        const norm = Math.sqrt(x * x + y * y + z * z);
        x /= norm;
        y /= norm;
        z /= norm;

        // Convert back to lat/lng
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
    // Close popup on zoom
    setHoveredVessel(null);
    setPopupPosition(null);
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
      }
    } catch (error) {
      alert('An unexpected error occurred.');
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

  // Handle clicking outside the popup to close it
  // useEffect(() => {
  //   const handleClickOutside = (event: MouseEvent) => {
  //     if (hoveredVessel && popupPosition) {
  //       // Check if the click is outside the popup
  //       const target = event.target as HTMLElement;
  //       const popupElement = document.querySelector('[data-popup="vessel-info"]');
        
  //       if (popupElement && !popupElement.contains(target)) {
  //         setHoveredVessel(null);
  //         setPopupPosition(null);
  //       }
  //     }
  //   };

  //   if (hoveredVessel) {
  //     document.addEventListener('mousedown', handleClickOutside);
  //   }

  //   return () => {
  //     document.removeEventListener('mousedown', handleClickOutside);
  //   };
  // }, [hoveredVessel, popupPosition]);

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

        // Land polygons
        polygonsData={landData.features}
        polygonCapColor={() => 'rgba(130, 130, 130, 0.5)'}
        polygonSideColor={() => 'rgba(0,0,0,0)'}
        polygonAltitude={0}
        polygonStrokeColor={() => 'rgba(255, 255, 255, 1)'}

        // Graticules
        showGraticules={true}

        htmlElementsData={clusteredData}
        htmlElement={(d: any) => {
          const el = document.createElement('div');
          // Use cluster SVG if count > 1, otherwise use regular marker
          if (d.count > 1) {
            el.innerHTML = clusterSvg(d.count);
          } else {
            el.innerHTML = markerSvg;
          }
          
          el.style.color = d.legal ? "#41fc03" : "#fc0303";
          el.style.width = d.count > 1 ? `40px` : `30px`; // Make clusters slightly larger
          el.style.height = 'auto';
          el.style.transition = 'opacity 250ms';
          el.style.cursor = 'pointer';
          el.style.pointerEvents = 'auto'; // Ensure pointer events work
          
          // Add click event handler for all markers
          el.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            if (d.count == 1) {
              // Handle single vessel click
              setHoveredVessel(d.markers[0]);
              
              // Calculate smart positioning based on screen position
              const popupHeight = 300; // Approximate popup height
              const popupWidth = 320; // Approximate popup width
              const screenHeight = window.innerHeight;
              const screenWidth = window.innerWidth;
              
              let x = e.clientX + 15;
              let y = e.clientY - 10;
              
              // Adjust horizontal position if popup would go off screen
              if (x + popupWidth > screenWidth) {
                x = e.clientX - popupWidth - 15; // Position to the left instead
              }
              
              // Adjust vertical position based on screen half
              if (e.clientY > screenHeight / 2) {
                // Bottom half - position popup above the click
                y = e.clientY - popupHeight - 10;
              } else {
                // Top half - position popup below the click
                y = e.clientY - 10;
              }
              
              // Ensure popup stays within screen bounds
              y = Math.max(10, Math.min(y, screenHeight - popupHeight - 10));
              x = Math.max(10, Math.min(x, screenWidth - popupWidth - 10));
              
              setPopupPosition({ x, y });
            } else {
              // INSERT_YOUR_CODE
              // Gradually zoom onto the cluster when a cluster is clicked
              if (globeEl.current) {
                // Get current POV
                const currentPov = globeEl.current.pointOfView();
                // Target POV: center on cluster, zoom in (decrease altitude)

                const targetPov = {
                  lat: d.lat,
                  lng: d.lng,
                  altitude: Math.min(5000, d.closest) / 500 * 0.5 // zoom in, but not too close
                };

                // Animate the transition
                const duration = 1200; // ms
                const start = performance.now();

                function animateZoom(now: number) {
                  const t = Math.min((now - start) / duration, 1);
                  // Ease in-out
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
        htmlElementVisibilityModifier={(el, isVisible) => {
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
          {/* Image placeholder */}
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
          
          <div style={{ fontWeight: 'bold', marginBottom: '12px', color: hoveredVessel.legal ? '#51cf66' : '#ff6b6b', fontSize: '16px' }}>
            Vessel Information
          </div>
          
          <div style={{ marginBottom: '10px' }}>
            <strong>Location:</strong> {hoveredVessel.lat.toFixed(4)}°, {hoveredVessel.lng.toFixed(4)}°
          </div>
          
          <div style={{ marginBottom: '10px' }}>
            <strong>Status:</strong> 
            <span style={{ 
              color: hoveredVessel.isfishing ? '#ff6b6b' : '#51cf66',
              marginLeft: '8px',
              fontWeight: 'bold'
            }}>
              {hoveredVessel.isfishing ? 'Fishing' : 'Not Fishing'}
            </span>
          </div>
          
          <div style={{ marginBottom: '16px' }}>
            <strong>Registered:</strong> 
            <span style={{ 
              color: hoveredVessel.legal ? '#51cf66' : '#ff6b6b',
              marginLeft: '8px',
              fontWeight: 'bold'
            }}>
              {hoveredVessel.legal ? 'Yes' : 'No'}
            </span>
          </div>
          
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
    </div>
  );
};

export default HomePage;
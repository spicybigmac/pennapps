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
}

const HomePage: React.FC = () => {
  const globeEl = useRef<any>(null);
  const [landData, setLandData] = useState<{ features: any[] }>({ features: [] });
  const [vesselData, setVesselData] = useState<VesselData[]>([]);
  const [clusteredData, setClusteredData] = useState<ClusterData[]>([]);
  const [clusterThreshold, setClusterThreshold] = useState(0);
  const [hoveredVessel, setHoveredVessel] = useState<VesselData | null>(null);

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
        legal: marker.legal
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
          
          el.style.color = d.legal ? "green" : "red";
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
            }
          });
          
          // Add hover event handlers
          el.addEventListener('mouseenter', (e) => {
            el.style.transform = 'scale(1.2)';
            el.style.zIndex = '100';
          });
          
          el.addEventListener('mouseleave', () => {
            el.style.transform = 'scale(1)';
            el.style.zIndex = '1';
          });
          
          return el;
        }}
        htmlElementVisibilityModifier={(el, isVisible) => el.style.opacity = isVisible ? "1" : "0"}
      
        onGlobeReady={()=>{clusterMarkers(vesselData)}}
        onZoom={(pov) => {handleZoom(pov)}}
      />
      
      {/* Vessel information popup */}
      {hoveredVessel && (
        <div
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            color: 'white',
            padding: '16px 20px',
            borderRadius: '8px',
            fontSize: '14px',
            fontFamily: 'Arial, sans-serif',
            zIndex: 1000,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            maxWidth: '300px',
            minWidth: '250px'
          }}
        >
          <div style={{ fontWeight: 'bold', marginBottom: '12px', color: hoveredVessel.isfishing ? '#ff6b6b' : '#51cf66' }}>
            Vessel Information
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>Location:</strong> {hoveredVessel.lat.toFixed(4)}°, {hoveredVessel.lng.toFixed(4)}°
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>Status:</strong> {hoveredVessel.isfishing ? 'Fishing' : 'Not Fishing'}
          </div>
          <div style={{ marginBottom: '8px' }}>
            <strong>Registered:</strong> {hoveredVessel.legal ? 'Yes' : 'No'}
          </div>
          <button
            onClick={() => setHoveredVessel(null)}
            style={{
              marginTop: '12px',
              padding: '8px 16px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
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
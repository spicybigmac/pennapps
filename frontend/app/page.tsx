'use client';

import dynamic from 'next/dynamic';
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation'; // Import useRouter for navigation
import * as topojson from 'topojson-client';

const Globe = dynamic(() => import('react-globe.gl'), { ssr: false });

// Interfaces (assuming these are shared, or only needed for visual globe)
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

const LandingPage: React.FC = () => {
  const router = useRouter(); // Initialize useRouter
  const globeEl = useRef<any>(null);
  const [landData, setLandData] = useState<{ features: any[] }>({ features: [] });
  const [isDataLoaded, setIsDataLoaded] = useState(false);
  const [isFirstLoad, setIsFirstLoad] = useState(true);

  // Minimal data for landing page globe background
  const [clusteredData, setClusteredData] = useState<ClusterData[]>([]);
  const [vesselData, setVesselData] = useState<VesselData[]>([]); // To simulate data for the background globe
  const GREEN = "#2eb700";
  const RED = "#fc0303";

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

  // Simplified cluster function for landing page to just show some markers
  const clusterMarkers = useCallback((markers: VesselData[], cull = true) => {
    if (markers.length === 0) return;

    // For landing page, we just want some visible clusters/markers
    // No culling based on POV, just a simple representation
    const clusters: ClusterData[] = [];
    markers.slice(0, 50).forEach(marker => { // Display a subset for performance
        clusters.push({
            lat: marker.lat,
            lng: marker.lng,
            count: 1,
            markers: [marker],
            registered: marker.registered,
            closest: Infinity
        });
    });
    setClusteredData(clusters);
  }, []);

  const fetchData = useCallback(async () => {
    setIsDataLoaded(false);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/getPositions', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      const data: VesselData[] = await response.json();
      if (response.ok) {
        setVesselData(data); // Store for background globe
        clusterMarkers(data); // Cluster them
        setIsDataLoaded(true);
        setIsFirstLoad(false);
      }
    } catch (error) {
      console.log('Error fetching vessel data:', error);
      setIsDataLoaded(true);
      setIsFirstLoad(false);
    }
  }, [clusterMarkers]);

  useEffect(() => {
    fetch('https://cdn.jsdelivr.net/npm/world-atlas/land-110m.json')
      .then((res) => res.json())
      .then((landTopo) => {
        const featureCollection = topojson.feature(landTopo, landTopo.objects.land);
        setLandData(featureCollection as unknown as { features: any[] });
      });

    fetchData();
  }, [fetchData]);
  const handleEnterDashboard = () => {
    router.push('/dashboard'); // Navigate to the dashboard page
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
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#000',
          color: 'white',
          fontFamily: 'Arial, sans-serif',
          overflow: 'hidden'
        }}>
          {/* Globe positioned off-screen to the right */}
          <div style={{
            position: 'absolute',
            right: '-50%',
            top: '50%',
            transform: 'translateY(-50%)',
            width: '100%',
            height: '100%',
          }}>
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
                el.style.color = d.registered ? GREEN : RED;
                el.style.width = `${40 + d.count / 200}px`;
                el.style.height = 'auto';
                el.style.pointerEvents = 'none'; // Disable interaction for background
                return el;
              }}
              htmlElementVisibilityModifier={(el: any, isVisible: Boolean) => {
                if (isVisible) {
                  el.style.opacity = '1';
                } else {
                  el.style.opacity = '0';
                }
              }}
              onGlobeReady={() => { 
                if (globeEl.current) {
                  globeEl.current.pointOfView({ lat: 25, lng: 0, altitude: 0.6 });
                  globeEl.current.controls().autoRotate = true;
                  globeEl.current.controls().autoRotateSpeed = 1;
                }
              }}
            />
          </div>

          {/* Landing page content */}
          <div style={{
            position: 'relative',
            zIndex: 10,
            textAlign: 'left',
            maxWidth: '600px',
            padding: '0 60px',
            marginLeft: '-400px'
          }}>
            {/* Logo and Title */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '20px'
            }}>
              <img 
                src="/OverSEAlogo.png" 
                alt="OverSea" 
                style={{ 
                  width: '60px', 
                  height: '60px', 
                  marginRight: '20px',
                  borderRadius: '8px'
                }} 
              />
              <h1 style={{
                fontSize: '4rem',
                fontWeight: 'bold',
                margin: 0,
                color: '#ffffff',
                letterSpacing: '0.1em'
              }}>
                OverSea
              </h1>
            </div>

            {/* Subtitle */}
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '300',
              margin: '0 0 40px 0',
              color: '#ccc',
              lineHeight: '1.4'
            }}>
              OverSEAing the sustainability of our seas.
            </h2>

            {/* Enter Button */}
            <button
              onClick={handleEnterDashboard} // Changed to navigate
              style={{
                padding: '15px 40px',
                fontSize: '1.2rem',
                fontWeight: '600',
                backgroundColor: '#2eb700',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: '0 4px 20px rgba(46, 183, 0, 0.3)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#51cf66';
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 6px 25px rgba(46, 183, 0, 0.4)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#2eb700';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 20px rgba(46, 183, 0, 0.3)';
              }}
            >
              Enter Dashboard
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LandingPage;
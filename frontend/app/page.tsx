'use client';

import dynamic from 'next/dynamic';
import React, { useRef, useEffect, useState } from 'react';
import * as topojson from 'topojson-client';

const Globe = dynamic(() => import('react-globe.gl'), { ssr: false });

const HomePage: React.FC = () => {
  const globeEl = useRef();
  const [landData, setLandData] = useState({ features: [] });

  useEffect(() => {
    fetch('//cdn.jsdelivr.net/npm/world-atlas/land-110m.json')
      .then(res => res.json())
      .then(landTopo => {
        setLandData(topojson.feature(landTopo, landTopo.objects.land));
      });
  }, []);

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', backgroundColor: 'black' }}>
      <Globe
        ref={globeEl}
        globeImageUrl={null}
        bumpImageUrl={null}
        backgroundImageUrl={null}
        showGlobe={false}
        showAtmosphere={false}
        backgroundColor={'rgba(0,0,0,0)'}

        // Polygon rendering for landmasses
        polygonsData={landData.features}
        polygonCapColor={() => 'rgba(130, 130, 130, 0.5)'} // Landmass fill color
        polygonSideColor={() => 'rgba(0,0,0,0)'} // Keep sides transparent
        polygonAltitude={0} // Small altitude for stroke visibility
        polygonStrokeColor={() => 'rgba(255, 255, 255, 1)'} // White stroke color

        // Graticule (longitude and latitude lines) properties
        showGraticules={true} // Enable graticule lines
        graticuleColor={() => 'rgba(255, 255, 255, 0.5)'} // Light grey with some transparency
        graticuleLineResolution={20} // Lines every 10 degrees (adjust as needed)
      />
    </div>
  );
};

export default HomePage;
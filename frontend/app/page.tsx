'use client';

import dynamic from 'next/dynamic';
import React, { useRef, useEffect, useState } from 'react';
import * as topojson from 'topojson-client';

const Globe = dynamic(() => import('react-globe.gl'), { ssr: false });

const HomePage: React.FC = () => {
  const globeEl = useRef<any>(null);
  const [landData, setLandData] = useState<{ features: any[] }>({ features: [] });

  useEffect(() => {
    fetch('https://cdn.jsdelivr.net/npm/world-atlas/land-110m.json')
      .then((res) => res.json())
      .then((landTopo) => {
        const featureCollection = topojson.feature(landTopo, landTopo.objects.land);
        setLandData(featureCollection as { features: any[] });
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

        // Land polygons
        polygonsData={landData.features}
        polygonCapColor={() => 'rgba(130, 130, 130, 0.5)'}
        polygonSideColor={() => 'rgba(0,0,0,0)'}
        polygonAltitude={0}
        polygonStrokeColor={() => 'rgba(255, 255, 255, 1)'}

        // Graticules
        showGraticules={true}
        graticuleColor={() => 'rgba(255, 255, 255, 0.5)'}
        graticuleLineResolution={20}
      />
    </div>
  );
};

export default HomePage;
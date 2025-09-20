'use client';
import dynamic from 'next/dynamic';
import React, { useRef, useEffect, useState } from 'react';

const Globe = dynamic(() => import('react-globe.gl'), { ssr: false });

const HomePage: React.FC = () => {
  const globeEl = useRef();
  const [countries, setCountries] = useState({ features: [] });

  useEffect(() => {
    fetch('/ne_110m_admin_0_countries.geojson')
      .then(res => res.json())
      .then(setCountries);
  }, []);

  return (
    <div className="flex-1 relative">
      <Globe
        ref={globeEl}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        hexPolygonsData={countries.features}
        hexPolygonResolution={3}
        hexPolygonMargin={0.7}
        hexPolygonColor={() => `rgba(255, 255, 255, 0.8)`}
        width={window.innerWidth - 256} // HACK: Subtract sidebar width
        height={window.innerHeight}
      />
    </div>
  );
};

export default HomePage;
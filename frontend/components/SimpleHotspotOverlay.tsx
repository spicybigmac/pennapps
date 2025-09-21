'use client';

import React, { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';

interface SimpleHotspot {
  id: string;
  lat: number;
  lon: number;
  risk_score: number;
  risk_level: string;
  vessel_count: number;
  untracked_ratio: number;
  size: number;
  color: string;
  created_at: string;
  rank?: number;
}

interface SimpleHotspotOverlayProps {
  hotspots: SimpleHotspot[];
  globeRef: any;
  isVisible: boolean;
  pulseSpeed?: number;
  opacity?: number;
}

const SimpleHotspotOverlay: React.FC<SimpleHotspotOverlayProps> = ({ 
  hotspots, 
  globeRef, 
  isVisible,
  pulseSpeed = 1.0,
  opacity = 0.7
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const hotspotMeshesRef = useRef<THREE.Mesh[]>([]);
  const animationIdRef = useRef<number | null>(null);
  const clockRef = useRef<THREE.Clock>(new THREE.Clock());

  // Convert lat/lon to 3D coordinates on globe
  const latLonToVector3 = (lat: number, lon: number, radius: number = 1.01) => {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    
    return new THREE.Vector3(
      -(radius * Math.sin(phi) * Math.cos(theta)),
      radius * Math.cos(phi),
      radius * Math.sin(phi) * Math.sin(theta)
    );
  };

  // Create hotspot mesh
  const createHotspotMesh = (hotspot: SimpleHotspot) => {
    // Create ring geometry for pulsating effect
    const geometry = new THREE.RingGeometry(0.005, 0.015, 32);
    
    // Create material with transparency
    const material = new THREE.MeshBasicMaterial({
      color: hotspot.color,
      transparent: true,
      opacity: opacity,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending
    });
    
    // Create mesh
    const mesh = new THREE.Mesh(geometry, material);
    
    // Position on globe
    const position = latLonToVector3(hotspot.lat, hotspot.lon);
    mesh.position.copy(position);
    
    // Store hotspot data and animation properties
    mesh.userData = {
      hotspot: hotspot,
      originalScale: hotspot.size,
      pulsePhase: Math.random() * Math.PI * 2,
      baseOpacity: opacity
    };
    
    return mesh;
  };

  // Initialize Three.js scene
  useEffect(() => {
    if (!containerRef.current || !globeRef.current) return;

    // Create scene
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // Create camera
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    cameraRef.current = camera;

    // Create renderer
    const renderer = new THREE.WebGLRenderer({ 
      alpha: true, 
      antialias: true,
      powerPreference: "high-performance"
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.domElement.style.position = 'absolute';
    renderer.domElement.style.top = '0';
    renderer.domElement.style.left = '0';
    renderer.domElement.style.pointerEvents = 'none';
    renderer.domElement.style.zIndex = '10';
    
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Create hotspot meshes
    const meshes: THREE.Mesh[] = [];
    hotspots.forEach((hotspot) => {
      const mesh = createHotspotMesh(hotspot);
      scene.add(mesh);
      meshes.push(mesh);
    });
    hotspotMeshesRef.current = meshes;

    // Animation loop
    const animate = () => {
      if (!sceneRef.current || !cameraRef.current || !rendererRef.current) return;

      const time = clockRef.current.getElapsedTime();
      
      // Update hotspot animations
      hotspotMeshesRef.current.forEach((mesh) => {
        if (mesh.userData.hotspot) {
          const { originalScale, pulsePhase, baseOpacity } = mesh.userData;
          
          // Pulsating scale effect
          const pulseScale = 1 + 0.4 * Math.sin(time * pulseSpeed + pulsePhase);
          mesh.scale.setScalar(originalScale * pulseScale);
          
          // Pulsating opacity effect
          const pulseOpacity = baseOpacity * (0.6 + 0.4 * Math.sin(time * pulseSpeed * 0.8 + pulsePhase));
          mesh.material.opacity = pulseOpacity;
          
          // Color intensity based on risk score
          const intensity = Math.min(1, mesh.userData.hotspot.risk_score);
          const color = new THREE.Color(mesh.userData.hotspot.color);
          color.multiplyScalar(0.7 + 0.3 * intensity);
          mesh.material.color.copy(color);
        }
      });

      // Sync camera with globe camera
      if (globeRef.current && globeRef.current.camera && globeRef.current.camera.position) {
        camera.position.copy(globeRef.current.camera.position);
        camera.quaternion.copy(globeRef.current.camera.quaternion);
        camera.updateMatrixWorld();
      }

      renderer.render(scene, camera);
      animationIdRef.current = requestAnimationFrame(animate);
    };

    animate();

    // Handle resize
    const handleResize = () => {
      if (cameraRef.current && rendererRef.current) {
        cameraRef.current.aspect = window.innerWidth / window.innerHeight;
        cameraRef.current.updateProjectionMatrix();
        rendererRef.current.setSize(window.innerWidth, window.innerHeight);
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      window.removeEventListener('resize', handleResize);
      if (rendererRef.current && containerRef.current) {
        containerRef.current.removeChild(rendererRef.current.domElement);
      }
    };
  }, [hotspots, globeRef, pulseSpeed, opacity]);

  // Update hotspot visibility
  useEffect(() => {
    if (rendererRef.current) {
      rendererRef.current.domElement.style.display = isVisible ? 'block' : 'none';
    }
  }, [isVisible]);

  // Update hotspots when data changes
  useEffect(() => {
    if (!sceneRef.current) return;

    // Remove existing meshes
    hotspotMeshesRef.current.forEach(mesh => {
      sceneRef.current?.remove(mesh);
    });

    // Create new meshes
    const meshes: THREE.Mesh[] = [];
    hotspots.forEach((hotspot) => {
      const mesh = createHotspotMesh(hotspot);
      sceneRef.current?.add(mesh);
      meshes.push(mesh);
    });
    hotspotMeshesRef.current = meshes;
  }, [hotspots, pulseSpeed, opacity]);

  return (
    <div 
      ref={containerRef} 
      style={{ 
        position: 'absolute', 
        top: 0, 
        left: 0, 
        width: '100%', 
        height: '100%',
        pointerEvents: 'none',
        zIndex: 10
      }} 
    />
  );
};

export default SimpleHotspotOverlay;

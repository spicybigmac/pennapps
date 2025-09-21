'use client';

import { useState, useEffect, useCallback } from 'react';

export interface SimpleHotspot {
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

export interface HotspotResponse {
  hotspots: SimpleHotspot[];
  total: number;
  filters?: {
    limit: number;
    min_risk: number;
    risk_level?: string;
  };
}

export interface GlobeHotspotResponse {
  hotspots: Array<{
    id: string;
    rank: number;
    position: {
      lat: number;
      lon: number;
    };
    risk: {
      score: number;
      level: string;
      color: string;
      size: number;
    };
    metadata: {
      vessel_count: number;
      untracked_ratio: number;
      created_at: string;
    };
    name: string;
    description: string;
  }>;
  metadata: {
    total_hotspots: number;
    last_updated: string;
    data_source: string;
  };
}

export interface UseSimpleHotspotsOptions {
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
  realTime?: boolean;
  hoursBack?: number;
  minRiskThreshold?: number;
  limit?: number;
  riskLevel?: string;
}

export const useSimpleHotspots = (options: UseSimpleHotspotsOptions = {}) => {
  const {
    autoRefresh = true,
    refreshInterval = 30000, // 30 seconds
    realTime = false,
    hoursBack = 24,
    minRiskThreshold = 0.3,
    limit = 50,
    riskLevel
  } = options;

  const [hotspots, setHotspots] = useState<SimpleHotspot[]>([]);
  const [globeHotspots, setGlobeHotspots] = useState<GlobeHotspotResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchHotspots = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      let url = 'http://127.0.0.1:8000/api/hotspots/';
      
      // Add query parameters
      const params = new URLSearchParams();
      if (limit) params.append('limit', limit.toString());
      if (minRiskThreshold) params.append('min_risk', minRiskThreshold.toString());
      if (riskLevel) params.append('risk_level', riskLevel);
      
      if (realTime) {
        url = 'http://127.0.0.1:8000/api/hotspots/real-time';
        params.append('hours_back', hoursBack.toString());
        params.append('min_risk_threshold', minRiskThreshold.toString());
      }
      
      if (params.toString()) {
        url += '?' + params.toString();
      }

      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch hotspots: ${response.statusText}`);
      }

      const data: HotspotResponse = await response.json();
      setHotspots(data.hotspots || []);
      setLastUpdated(new Date().toISOString());
    } catch (err) {
      console.error('Error fetching hotspots:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch hotspots');
    } finally {
      setLoading(false);
    }
  }, [realTime, hoursBack, minRiskThreshold, limit, riskLevel]);

  const fetchGlobeHotspots = useCallback(async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/hotspots/globe-data', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch globe hotspots: ${response.statusText}`);
      }

      const data: GlobeHotspotResponse = await response.json();
      setGlobeHotspots(data);
    } catch (err) {
      console.error('Error fetching globe hotspots:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch globe hotspots');
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchHotspots();
    fetchGlobeHotspots();
  }, [fetchHotspots, fetchGlobeHotspots]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchHotspots();
      fetchGlobeHotspots();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchHotspots, fetchGlobeHotspots]);

  // Manual refresh function
  const refresh = useCallback(() => {
    fetchHotspots();
    fetchGlobeHotspots();
  }, [fetchHotspots, fetchGlobeHotspots]);

  // Get hotspots by risk level
  const getHotspotsByRiskLevel = useCallback((level: string) => {
    return hotspots.filter(hotspot => hotspot.risk_level === level);
  }, [hotspots]);

  // Get hotspots by region
  const getHotspotsByRegion = useCallback((minLat: number, maxLat: number, minLon: number, maxLon: number) => {
    return hotspots.filter(hotspot => 
      hotspot.lat >= minLat && 
      hotspot.lat <= maxLat &&
      hotspot.lon >= minLon && 
      hotspot.lon <= maxLon
    );
  }, [hotspots]);

  // Get top N hotspots
  const getTopHotspots = useCallback((n: number = 10) => {
    return hotspots
      .sort((a, b) => b.risk_score - a.risk_score)
      .slice(0, n);
  }, [hotspots]);

  // Get hotspot statistics
  const getStatistics = useCallback(() => {
    if (hotspots.length === 0) {
      return {
        total: 0,
        byRiskLevel: {},
        averageRisk: 0,
        totalVessels: 0
      };
    }

    const byRiskLevel = hotspots.reduce((acc, hotspot) => {
      const level = hotspot.risk_level;
      acc[level] = (acc[level] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const riskScores = hotspots.map(h => h.risk_score);
    const averageRisk = riskScores.reduce((sum, score) => sum + score, 0) / riskScores.length;
    const totalVessels = hotspots.reduce((sum, h) => sum + h.vessel_count, 0);

    return {
      total: hotspots.length,
      byRiskLevel,
      averageRisk: Math.round(averageRisk * 1000) / 1000,
      totalVessels,
      lastUpdated
    };
  }, [hotspots, lastUpdated]);

  return {
    hotspots,
    globeHotspots,
    loading,
    error,
    lastUpdated,
    refresh,
    getHotspotsByRiskLevel,
    getHotspotsByRegion,
    getTopHotspots,
    getStatistics
  };
};

export default useSimpleHotspots;

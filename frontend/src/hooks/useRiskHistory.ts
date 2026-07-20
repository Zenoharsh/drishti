import { useState, useCallback, useRef } from 'react';

interface HistoryMetadata {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
}

interface RiskSnapshot {
  id: string;
  corridor_id: string;
  disruption_score: number;
  created_at: string;
  // ... other fields
}

export function useRiskHistory(corridorId: string) {
  const [data, setData] = useState<RiskSnapshot[]>([]);
  const [metadata, setMetadata] = useState<HistoryMetadata | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Use a ref to prevent overlapping fetches
  const fetchingRef = useRef(false);

  const fetchPage = useCallback(async (page: number) => {
    if (!corridorId || fetchingRef.current) return;
    if (metadata && page > metadata.total_pages) return;

    fetchingRef.current = true;
    setLoading(true);
    setError(null);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://drishti-on9a.onrender.com";
      const res = await fetch(`${API_BASE}/risk/history/${corridorId}?page=${page}&page_size=50`);
      if (!res.ok) throw new Error("Failed to fetch historical risk data");
      
      const json = await res.json();
      
      setData(prev => page === 1 ? json.history : [...prev, ...json.history]);
      setMetadata(json.metadata);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
      fetchingRef.current = false;
    }
  }, [corridorId, metadata]);

  const loadMore = useCallback(() => {
    if (metadata && metadata.page < metadata.total_pages) {
      fetchPage(metadata.page + 1);
    }
  }, [metadata, fetchPage]);

  const refresh = useCallback(() => {
    fetchPage(1);
  }, [fetchPage]);

  return { data, metadata, loading, error, loadMore, refresh };
}

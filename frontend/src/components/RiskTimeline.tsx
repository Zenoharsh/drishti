"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Play, Activity, AlertTriangle, Target, Clock } from "lucide-react";
import { useRiskHistory } from "../hooks/useRiskHistory";

export default function RiskTimeline({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
  const { data: history, metadata, loading, loadMore } = useRiskHistory("hormuz");
  const [simulating, setSimulating] = useState(false);

  const handleRunSimulation = async () => {
    setSimulating(true);
    try {
      const res = await fetch("http://127.0.0.1:8080/run-simulation", {
        method: "POST"
      });
      if (res.ok) {
        // Wait a second then tell user to refresh
        setTimeout(() => {
          alert("Simulation Complete! The intelligence engine has digested the event. Close the timeline and click 'Refresh Signals' to view the catastrophic impact.");
        }, 1500);
      } else {
        alert("Simulation failed to run.");
      }
    } catch (e) {
      console.error(e);
      alert("Error triggering simulation.");
    } finally {
      setSimulating(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100 }}
            onClick={onClose}
          />
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            style={{ 
              position: 'fixed', top: 0, right: 0, bottom: 0, width: '400px', 
              background: 'var(--md-sys-color-surface-container-high, #2b2d31)', 
              zIndex: 101, display: 'flex', flexDirection: 'column', 
              boxShadow: '-8px 0 32px rgba(0,0,0,0.7)',
              borderLeft: '1px solid rgba(255,255,255,0.05)'
            }}
          >
            <div style={{ padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Activity size={24} color="var(--md-sys-color-primary)" /> Intelligence Feed
              </h2>
              <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', padding: '0.25rem' }}>
                <X size={24} />
              </button>
            </div>

            <div style={{ padding: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <button 
                onClick={handleRunSimulation} 
                disabled={simulating}
                style={{ 
                  width: '100%', padding: '0.75rem', borderRadius: '8px', 
                  background: 'var(--md-sys-color-error)', color: '#fff', 
                  border: 'none', fontWeight: 600, fontSize: '1rem',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                  cursor: simulating ? 'not-allowed' : 'pointer',
                  opacity: simulating ? 0.7 : 1
                }}
              >
                <Play size={18} /> {simulating ? "Running AI Simulation..." : "Trigger Crisis Simulation"}
              </button>
              <p style={{ margin: '0.75rem 0 0 0', fontSize: '0.75rem', color: 'var(--md-sys-color-on-surface-variant)', textAlign: 'center' }}>
                Injects a severe geopolitical event into the knowledge graph.
              </p>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
              {history.map((snapshot: any, idx: number) => {
                const score = snapshot.disruption_score;
                const isCritical = score > 0.6;
                const isElevated = score > 0.2;
                const color = isCritical ? 'var(--md-sys-color-error)' : (isElevated ? 'var(--md-sys-color-tertiary)' : 'var(--md-sys-color-primary)');
                
                return (
                  <motion.div 
                    key={snapshot.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    style={{ 
                      padding: '1rem', marginBottom: '1rem', borderRadius: '12px',
                      background: 'var(--md-sys-color-surface-container, #1e1f22)',
                      borderLeft: `4px solid ${color}`
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--md-sys-color-on-surface-variant)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Clock size={12} /> {new Date(snapshot.created_at).toLocaleString()}
                      </span>
                      <strong style={{ color }}>{(score * 100).toFixed(1)}% Risk</strong>
                    </div>
                    
                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <span style={{ color: 'var(--md-sys-color-on-surface-variant)', fontSize: '0.6875rem', textTransform: 'uppercase' }}>Severity</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <AlertTriangle size={14} color={snapshot.severity > 0.5 ? 'var(--md-sys-color-error)' : 'inherit'} />
                          {snapshot.severity.toFixed(2)}
                        </div>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <span style={{ color: 'var(--md-sys-color-on-surface-variant)', fontSize: '0.6875rem', textTransform: 'uppercase' }}>Sanctions</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <Target size={14} color={snapshot.sanctions_flag > 0 ? 'var(--md-sys-color-error)' : 'inherit'} />
                          {snapshot.sanctions_flag > 0 ? "Active" : "None"}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
              
              {metadata && metadata.page < metadata.total_pages && (
                <button 
                  onClick={loadMore}
                  disabled={loading}
                  style={{ 
                    width: '100%', padding: '0.75rem', borderRadius: '8px', 
                    background: 'transparent', border: '1px solid var(--md-sys-color-outline)',
                    color: 'var(--md-sys-color-primary)', fontWeight: 600,
                    cursor: loading ? 'not-allowed' : 'pointer'
                  }}
                >
                  {loading ? "Loading..." : "Load Older Records"}
                </button>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, ShieldAlert, Zap, RefreshCcw, TrendingUp, Info, AlertTriangle, CheckCircle } from "lucide-react";
import styles from "./Dashboard.module.css";
import MapWrapper from "../components/MapWrapper";
import RiskTimeline from "../components/RiskTimeline";

const DrishtiLogo = ({ className = "", size = 28, color = "currentColor" }) => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    width={size} 
    height={size} 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke={color} 
    strokeWidth="1.5" 
    strokeLinecap="round" 
    strokeLinejoin="round" 
    className={className}
    style={{ filter: "drop-shadow(0px 2px 4px rgba(0,0,0,0.5))" }}
  >
    {/* Top Lashes */}
    <path d="M12 4.5v-2" />
    <path d="M17 5.5l1.5-1.5" />
    <path d="M7 5.5L5.5 4" />
    {/* Eye Shape with Depth */}
    <path d="M2 12C2 12 5 5 12 5C19 5 22 12 22 12C22 12 19 19 12 19C5 19 2 12 2 12Z" />
    {/* Iris & Pupil */}
    <circle cx="12" cy="12" r="3" fill={color} fillOpacity="0.2" />
    <circle cx="12" cy="12" r="1.5" fill={color} />
  </svg>
);

const Tooltip = ({ text }: { text: string }) => (
  <span className={styles.tooltipContainer}>
    <Info size={14} style={{ marginLeft: '4px', verticalAlign: 'middle' }} />
    <span className={styles.tooltipText}>{text}</span>
  </span>
);

const WireframeLoader = () => (
  <div className={styles.wireframeLoader}>
    <div className={styles.skeletonLine} style={{ width: '40%' }}></div>
    <div className={styles.skeletonLine} style={{ width: '100%', height: '60px' }}></div>
    <div className={styles.skeletonLine} style={{ width: '80%' }}></div>
    <div className={styles.skeletonLine} style={{ width: '60%' }}></div>
  </div>
);

const TrendGraph = ({ spikePct, isCrisis }: { spikePct: number, isCrisis: boolean }) => {
  const points = Array.from({ length: 30 }, (_, i) => {
    const day = i;
    // Logistic curve simulation for 30-day projection
    const val = spikePct / (1 + Math.exp(-0.4 * (day - 12)));
    return { day, val };
  });

  const maxVal = Math.max(10, spikePct * 1.1);
  const pathData = points.map((p, i) => {
    const x = (i / 29) * 300;
    const y = 80 - (p.val / maxVal) * 70;
    return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
  }).join(' ');

  const color = isCrisis ? "var(--md-sys-color-error)" : "var(--md-sys-color-primary)";

  return (
    <div style={{ width: '100%', height: '80px', marginTop: '1.5rem', marginBottom: '0.5rem', position: 'relative' }}>
      <svg width="100%" height="100%" viewBox="0 0 300 80" preserveAspectRatio="none">
        <defs>
          <linearGradient id="spikeGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0.0} />
          </linearGradient>
        </defs>
        <path d={`${pathData} L 300 80 L 0 80 Z`} fill="url(#spikeGrad)" />
        <path d={pathData} fill="none" stroke={color} strokeWidth="2.5" />
      </svg>
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, borderBottom: '1px solid rgba(255,255,255,0.1)' }} />
      <span style={{ position: 'absolute', bottom: -20, left: 0, fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '1px' }}>Day 0</span>
      <span style={{ position: 'absolute', bottom: -20, right: 0, fontSize: '0.65rem', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '1px' }}>Day 30 Projection</span>
    </div>
  );
};

export default function Dashboard() {
  const [scenarioData, setScenarioData] = useState<any>(null);
  const [procurementData, setProcurementData] = useState<any>(null);
  const [reserveData, setReserveData] = useState<any>(null);
  const [corridorsData, setCorridorsData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timelineOpen, setTimelineOpen] = useState(false);

  const corridor = "hormuz";
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://drishti-on9a.onrender.com";

  const fetchDashboardData = async () => {
    setLoading(true);
    setError("");
    try {
      const headers = { "Content-Type": "application/json" };
      const body = JSON.stringify({ corridor });

      const scenRes = await fetch(`${API_BASE}/scenario/quick`, { method: "POST", headers, body });
      const procRes = await fetch(`${API_BASE}/procurement/quick`, { method: "POST", headers, body });
      const resRes = await fetch(`${API_BASE}/reserve?corridor=${corridor}`);
      const corrRes = await fetch(`${API_BASE}/risk/corridors`);

      if (!scenRes.ok || !procRes.ok || !resRes.ok || !corrRes.ok) {
        throw new Error("Failed to fetch data from backend. Is it running?");
      }

      setScenarioData(await scenRes.json());
      setProcurementData(await procRes.json());
      setReserveData(await resRes.json());
      const corrData = await corrRes.json();
      setCorridorsData(corrData.corridors || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const disruptionScore = scenarioData ? (scenarioData.disruption_score * 100).toFixed(1) : 0;
  const isCrisis = scenarioData && scenarioData.disruption_score > 0.3;

  return (
    <div className={styles.container}>
      {error && (
        <motion.div initial={{ y: -50, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className={styles.error}>
          <ShieldAlert size={24} /> {error}
        </motion.div>
      )}

      <RiskTimeline isOpen={timelineOpen} onClose={() => setTimelineOpen(false)} />

      {/* Header Navbar */}
      <header className={styles.header}>
        <div className={styles.headerTitle}>
          <DrishtiLogo className={isCrisis ? styles.spikeIndicator : ""} size={28} color={isCrisis ? "var(--md-sys-color-error)" : "var(--md-sys-color-primary)"} />
          <h1>Drishti</h1>
        </div>
        
        <nav className={styles.navLinks}>
          <span className={`${styles.navLink} ${styles.active}`}>Live Operations</span>
          <span className={styles.navLink} onClick={() => setTimelineOpen(!timelineOpen)} style={{ cursor: 'pointer' }}>Intelligence Feed</span>
        </nav>
        <button onClick={fetchDashboardData} disabled={loading}>
          <RefreshCcw size={18} className={loading ? "animate-spin" : ""} />
          {loading ? "Analyzing..." : "Refresh Signals"}
        </button>
      </header>

      {/* AI Summary Banner */}
      <AnimatePresence>
        {!loading && scenarioData && (
          <motion.div 
            initial={{ y: -20, opacity: 0, x: "-50%" }}
            animate={{ y: 0, opacity: 1, x: "-50%" }}
            exit={{ y: -20, opacity: 0, x: "-50%" }}
            className={`${styles.aiBanner} ${isCrisis ? styles.crisis : styles.stable}`}
            style={{ borderRadius: '12px', alignItems: 'center' }}
          >
            {isCrisis ? <AlertTriangle size={24} style={{ flexShrink: 0 }} /> : <CheckCircle size={24} style={{ flexShrink: 0 }} />}
            <span style={{ textAlign: 'left', lineHeight: 1.4 }}>
              {isCrisis 
                ? "CRITICAL ALERT: Severe disruption in the Strait of Hormuz. Global crude supply is restricted, triggering immediate fuel price spikes and GDP drag."
                : "Global energy transit corridors are stable. No active supply chain disruptions detected."}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hero Map Section */}
      <div className={styles.heroSection}>
        <MapWrapper corridors={corridorsData} />
      </div>

      {/* Content Grid */}
      <div className={styles.contentGrid}>
        
        {/* 1: Macro Impact */}
        <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className={`${styles.surfaceCard} ${styles.card}`}
          >
            <div className={styles.cardHeader}>
              <Activity size={24} color="var(--md-sys-color-primary)" className={styles.cardHeaderIcon} />
              <div className={styles.cardHeaderTexts}>
                <h2>Global Economic Impact</h2>
                <p>Estimated real-world consequences of the current supply disruption.</p>
              </div>
            </div>
            
            {loading && !scenarioData ? <WireframeLoader /> : (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, justifyContent: 'space-between' }}>
                <div className={styles.stats} style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', gap: '1rem' }}>
                  <div className={styles.statBox} style={{ flex: 1 }}>
                    <span style={{ whiteSpace: 'nowrap' }}>Supply Chain Risk <Tooltip text="Probability of a sustained global supply shortage based on real-time news and AIS vessel tracking." /></span>
                    <strong className={isCrisis ? styles.spikeIndicator : ""}>{disruptionScore}%</strong>
                  </div>
                  <div className={styles.statBox} style={{ flex: 1 }}>
                    <span style={{ whiteSpace: 'nowrap' }}>Est. Fuel Price Spike</span>
                    <strong className={isCrisis ? styles.spikeIndicator : ""}>
                      +{scenarioData?.economic_impact_30_days?.fuel_price_spike_pct}%
                    </strong>
                  </div>
                  <div className={styles.statBox} style={{ flex: 1 }}>
                    <span style={{ whiteSpace: 'nowrap' }}>GDP Drag (30d)</span>
                    <strong className={styles.danger}>
                      -{scenarioData?.economic_impact_30_days?.gdp_drag_pct}%
                    </strong>
                  </div>
                </div>
                <TrendGraph spikePct={scenarioData?.economic_impact_30_days?.fuel_price_spike_pct || 0} isCrisis={isCrisis} />
              </div>
            )}
          </motion.div>
        {/* 2: Procurement Optimization */}
        <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className={`${styles.surfaceCard} ${styles.card}`}
          >
            <div className={styles.cardHeader}>
              <TrendingUp size={24} color="var(--md-sys-color-tertiary)" className={styles.cardHeaderIcon} />
              <div className={styles.cardHeaderTexts}>
                <h2>Alternative Supply Routes</h2>
                <p>AI-recommended global sources to replace the restricted oil supply.</p>
              </div>
            </div>
            
            {loading && !procurementData ? <WireframeLoader /> : (
              <div className={styles.gridTable}>
                <div className={`${styles.gridRow} ${styles.gridHeader}`}>
                  <span>Target Source</span>
                  <span>Arrival</span>
                  <span>Landed Price <Tooltip text="Total estimated cost per barrel including spot price and shipping freight." /></span>
                  <span>AI Match Score <Tooltip text="A composite score (out of 100) balancing chemical compatibility, arrival speed, and cost." /></span>
                </div>
                {procurementData?.substitutes.map((sub: any, idx: number) => (
                  <motion.div 
                    key={sub.source_id}
                    className={styles.gridRow}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + (idx * 0.1) }}
                  >
                    <span className={styles.gridCell}>{sub.source_name}</span>
                    <span className={styles.gridCell}>{sub.estimated_replacement_arrival_days}d</span>
                    <span className={styles.gridCell}>${(sub.current_spot_price_usd + sub.freight_cost_per_bbl).toFixed(2)}</span>
                    <span className={styles.gridCell}>{sub.procurement_score}</span>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>

          <motion.div 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className={`${styles.surfaceCard} ${styles.card}`}
          >
            <div className={styles.cardHeader}>
              <Zap size={24} color="var(--md-sys-color-error)" className={styles.cardHeaderIcon} />
              <div className={styles.cardHeaderTexts}>
                <h2>Emergency Reserve Release</h2>
                <p>Required release from national strategic reserves to prevent a domestic shortage.</p>
              </div>
            </div>
            
            {loading && !reserveData ? <WireframeLoader /> : (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', color: "var(--md-sys-color-on-surface-variant)", marginBottom: "1.5rem", gap: '1rem' }}>
                  <span style={{ flex: 1, fontSize: '1.1rem' }}>
                    <strong>Total Release Required:</strong> <br/>
                    <span style={{ color: '#fff', fontSize: '1.4rem' }}>{(reserveData?.total_drawn_m3 * 6.2898 / 1000000).toFixed(2)} Million Barrels</span>
                  </span>
                  <span style={{ flexShrink: 0, color: reserveData?.fully_covered ? 'var(--md-sys-color-tertiary)' : 'var(--md-sys-color-error)' }}>
                    {reserveData?.fully_covered ? "100% Covered" : "Shortfall Detected"}
                  </span>
                </div>
                <div className={styles.schedule}>
                  {reserveData?.schedule?.slice(0, 5).map((s: any, idx: number) => (
                    <motion.div 
                      key={s.day} 
                      className={styles.scheduleBar}
                      initial={{ opacity: 0, scaleX: 0 }}
                      animate={{ opacity: 1, scaleX: 1 }}
                      transition={{ delay: 0.4 + (idx * 0.1) }}
                      style={{ display: 'flex', alignItems: 'center', transformOrigin: "left", marginBottom: '0.5rem' }}
                    >
                      <span className={styles.day} style={{ flexShrink: 0, width: '45px' }}>Day {s.day}</span>
                      <div className={styles.barWrap} style={{ flexGrow: 1, margin: '0 1rem' }}>
                        <div 
                          className={styles.bar} 
                          style={{ width: `${(s.volume_m3 / reserveData.schedule[0].volume_m3) * 100}%` }}
                        />
                      </div>
                      <span className={styles.vol} style={{ flexShrink: 0, width: '60px', textAlign: 'right' }}>
                        {Math.round((s.volume_m3 * 6.2898) / 1000)}k bbl
                      </span>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        {/* End Grid */}
      </div>
    </div>
  );
}

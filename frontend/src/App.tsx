import { useState } from "react";
import { useQueries } from "@tanstack/react-query";
import TrafficMap from "./components/TrafficMap";
import AlertPanel from "./components/AlertPanel";
import PredictionCard from "./components/PredictionCard";
import CongestionChart from "./components/CongestionChart";
import PeakHoursChart from "./components/PeakHoursChart";
import WeatherCard from "./components/WeatherCard";
import SummaryStats from "./components/SummaryStats";
import TransportPanel from "./components/TransportPanel";
import LiveIndicator from "./components/LiveIndicator";
import { JUNCTIONS } from "./data/junctions";
import { fetchFusedPredict } from "./api/client";

type Tab = "trend" | "peak";

export default function App() {
  const [fromId, setFromId] = useState(JUNCTIONS[0].id);
  const [toId, setToId] = useState(JUNCTIONS[1].id);
  const [chartTab, setChartTab] = useState<Tab>("trend");

  // Active analysis is based on the "from" location
  const selectedId = fromId;
  const selectedJunction = JUNCTIONS.find(j => j.id === selectedId)!;

  const congestionQueries = useQueries({
    queries: JUNCTIONS.map(j => ({
      queryKey: ["fused-predict-map", j.id],
      queryFn: () => fetchFusedPredict(j.id),
      retry: false,
    })),
  });

  const congestionMap: Record<string, number> = {};
  JUNCTIONS.forEach((j, i) => {
    const d = congestionQueries[i].data as { congestion_level: number } | undefined;
    if (d) congestionMap[j.id] = d.congestion_level;
  });

  const swapLocations = () => {
    setFromId(toId);
    setToId(fromId);
  };

  return (
    <div className="app">
      <header className="header">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/>
        </svg>
        <h1>Traffic Intelligence System</h1>
        <span className="subtitle">Real-time · Predictive · Multi-modal</span>
        <div style={{ marginLeft: "auto" }}>
          <LiveIndicator junctionId={selectedId} />
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">

          {/* Route selector */}
          <div className="card">
            <h3>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M3 12h18M3 6h18M3 18h18"/>
              </svg>
              Route
            </h3>
            <div className="route-box">
              <div className="route-row">
                <span className="route-dot from" />
                <span className="route-label">FROM</span>
                <select className="route-select" value={fromId} onChange={e => setFromId(e.target.value)}>
                  {JUNCTIONS.map(j => <option key={j.id} value={j.id}>{j.name}</option>)}
                </select>
              </div>
              <div className="route-divider" onClick={swapLocations} style={{ cursor: "pointer" }} />
              <div className="route-row">
                <span className="route-dot to" />
                <span className="route-label">TO</span>
                <select className="route-select" value={toId} onChange={e => setToId(e.target.value)}>
                  {JUNCTIONS.map(j => <option key={j.id} value={j.id}>{j.name}</option>)}
                </select>
              </div>
            </div>
          </div>

          <div className="card">
            <h3>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
              Congestion Forecast
            </h3>
            <PredictionCard junctionId={selectedId} />
          </div>

          <div className="card">
            <h3>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
              </svg>
              24h Summary
            </h3>
            <SummaryStats junctionId={selectedId} />
          </div>

          <div className="card">
            <h3>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/>
              </svg>
              Weather Impact
            </h3>
            <WeatherCard junction={selectedJunction} />
          </div>

          <div className="card">
            <h3>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <rect x="1" y="3" width="15" height="13" rx="2"/><path d="M16 8h4l3 3v5h-7V8zM5.5 21a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM18.5 21a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/>
              </svg>
              Transport Mix
            </h3>
            <TransportPanel junctionId={selectedId} />
          </div>

          <div className="card">
            <h3>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              Active Alerts
            </h3>
            <AlertPanel junctionId={selectedId} />
          </div>

        </aside>

        <main className="main">
          <div className="map-container">
            <TrafficMap
              junctions={JUNCTIONS}
              congestionMap={congestionMap}
              selectedId={selectedId}
              onSelect={setFromId}
            />
          </div>

          <div className="chart-area">
            <div style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
              <button className={`tab-btn ${chartTab === "trend" ? "active" : ""}`} onClick={() => setChartTab("trend")}>
                Congestion Trend
              </button>
              <button className={`tab-btn ${chartTab === "peak" ? "active" : ""}`} onClick={() => setChartTab("peak")}>
                Peak Hours
              </button>
            </div>
            {chartTab === "trend"
              ? <CongestionChart junctionId={selectedId} />
              : <PeakHoursChart junctionId={selectedId} />
            }
          </div>
        </main>
      </div>
    </div>
  );
}

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import TrafficMap from "./components/TrafficMap";
import TISIcon from "./components/TISIcon";
import MobileNav from "./components/MobileNav";
import AlertPanel from "./components/AlertPanel";
import PredictionCard from "./components/PredictionCard";
import CongestionChart from "./components/CongestionChart";
import PeakHoursChart from "./components/PeakHoursChart";
import WeatherCard from "./components/WeatherCard";
import SummaryStats from "./components/SummaryStats";
import TransportPanel from "./components/TransportPanel";
import LiveIndicator from "./components/LiveIndicator";
import { JUNCTIONS } from "./data/junctions";
import { fetchBulkCongestion } from "./api/client";

type ChartTab = "trend" | "peak";
type MobileTab = "map" | "route" | "forecast" | "alerts" | "stats";

export default function App() {
  const [fromId, setFromId] = useState(JUNCTIONS[0].id);
  const [toId, setToId] = useState(JUNCTIONS[1].id);
  const [chartTab, setChartTab] = useState<ChartTab>("trend");
  const [mobileTab, setMobileTab] = useState<MobileTab>("map");

  const selectedId = fromId;
  const selectedJunction = JUNCTIONS.find(j => j.id === selectedId)!;

  // Single request for all junction congestion levels (replaces N individual calls)
  const { data: bulkData } = useQuery({
    queryKey: ["bulk-congestion"],
    queryFn: fetchBulkCongestion,
    refetchInterval: 60_000, // refresh every 60s instead of on every render
    retry: false,
  });

  const congestionMap: Record<string, number> = {};
  if (bulkData) {
    for (const [jId, info] of Object.entries(bulkData)) {
      congestionMap[jId] = info.congestion_level;
    }
  }

  const swapLocations = () => { setFromId(toId); setToId(fromId); };

  const routeCard = (
    <div className="card">
      <h3>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <circle cx="6" cy="19" r="3"/><circle cx="18" cy="5" r="3"/>
          <path d="M6 16V7a6 6 0 0 1 6-6h0a6 6 0 0 1 6 6v10"/>
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
        <div className="route-divider" onClick={swapLocations} />
        <div className="route-row">
          <span className="route-dot to" />
          <span className="route-label">TO</span>
          <select className="route-select" value={toId} onChange={e => setToId(e.target.value)}>
            {JUNCTIONS.map(j => <option key={j.id} value={j.id}>{j.name}</option>)}
          </select>
        </div>
      </div>
    </div>
  );

  const forecastCard = (
    <div className="card">
      <h3>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
        </svg>
        Congestion Forecast
      </h3>
      <PredictionCard junctionId={selectedId} />
    </div>
  );

  const weatherCard = (
    <div className="card">
      <h3>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
        </svg>
        Weather Impact
      </h3>
      <WeatherCard junction={selectedJunction} />
    </div>
  );

  const transportCard = (
    <div className="card">
      <h3>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <rect x="1" y="3" width="15" height="13" rx="2"/>
          <path d="M16 8h4l3 3v5h-7V8zM5.5 21a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM18.5 21a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"/>
        </svg>
        Transport Mix
      </h3>
      <TransportPanel junctionId={selectedId} />
    </div>
  );

  const alertsCard = (
    <div className="card">
      <h3>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        Active Alerts
      </h3>
      <AlertPanel junctionId={selectedId} />
    </div>
  );

  const summaryCard = (
    <div className="card">
      <h3>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
        </svg>
        24h Summary
      </h3>
      <SummaryStats junctionId={selectedId} />
    </div>
  );

  // Mobile panel content per tab
  const mobilePanelContent: Record<string, React.ReactNode> = {
    map: null,
    route: <>{routeCard}{forecastCard}{weatherCard}</>,
    forecast: <>{forecastCard}{summaryCard}</>,
    alerts: <>{alertsCard}</>,
    stats: <>{summaryCard}{transportCard}</>,
  };

  return (
    <div className={`app ${mobileTab === "map" ? "mobile-map-active" : ""}`}>
      <header className="header">
        <TISIcon size={32} />
        <h1>Traffic Intelligence System</h1>
        <span className="subtitle">Real-time · Predictive · Multi-modal</span>
        <div style={{ marginLeft: "auto" }}>
          <LiveIndicator junctionId={selectedId} />
        </div>
      </header>

      <div className="layout">
        {/* Desktop sidebar */}
        <aside className="sidebar">
          {routeCard}
          {forecastCard}
          {summaryCard}
          {weatherCard}
          {transportCard}
          {alertsCard}
        </aside>

        {/* Main content */}
        <main className="main">
          {/* Map always rendered, hidden on mobile non-map tabs via CSS */}
          <div className="map-container" style={{ display: mobileTab !== "map" ? undefined : undefined }}>
            <TrafficMap
              junctions={JUNCTIONS}
              congestionMap={congestionMap}
              selectedId={selectedId}
              onSelect={setFromId}
            />
          </div>

          {/* Desktop chart */}
          <div className="chart-area">
            <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
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

          {/* Mobile panel */}
          {mobileTab !== "map" && (
            <div className="mobile-panel">
              {mobilePanelContent[mobileTab]}
            </div>
          )}
        </main>
      </div>

      {/* Mobile bottom nav */}
      <MobileNav activeTab={mobileTab} onChange={(t) => setMobileTab(t as MobileTab)} />
    </div>
  );
}

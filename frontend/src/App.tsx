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
  const [selectedId, setSelectedId] = useState(JUNCTIONS[0].id);
  const [chartTab, setChartTab] = useState<Tab>("trend");
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

  return (
    <div className="app">
      <header className="header">
        <span style={{ fontSize: 22 }}>🔮</span>
        <h1>Traffic Intelligence System</h1>
        <span className="subtitle">Real-time · Predictive · Multi-modal</span>
        <div style={{ marginLeft: "auto" }}>
          <LiveIndicator junctionId={selectedId} />
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <div className="card">
            <h3>Junction</h3>
            <select
              className="junction-select"
              value={selectedId}
              onChange={e => setSelectedId(e.target.value)}
            >
              {JUNCTIONS.map(j => (
                <option key={j.id} value={j.id}>{j.name}</option>
              ))}
            </select>
          </div>

          <div className="card">
            <h3>🔮 Congestion Forecast</h3>
            <PredictionCard junctionId={selectedId} />
          </div>

          <div className="card">
            <h3>📊 24h Summary</h3>
            <SummaryStats junctionId={selectedId} />
          </div>

          <div className="card">
            <h3>🌧️ Weather Impact</h3>
            <WeatherCard junction={selectedJunction} />
          </div>

          <div className="card">
            <h3>🚗 Transport Mix</h3>
            <TransportPanel junctionId={selectedId} />
          </div>

          <div className="card">
            <h3>🚨 Active Alerts</h3>
            <AlertPanel junctionId={selectedId} />
          </div>
        </aside>

        <main className="main">
          <div className="map-container">
            <TrafficMap
              junctions={JUNCTIONS}
              congestionMap={congestionMap}
              selectedId={selectedId}
              onSelect={setSelectedId}
            />
          </div>

          <div className="chart-area">
            {/* Tab switcher */}
            <div style={{ display: "flex", gap: 12, marginBottom: 8 }}>
              {(["trend", "peak"] as Tab[]).map(tab => (
                <button
                  key={tab}
                  onClick={() => setChartTab(tab)}
                  style={{
                    background: chartTab === tab ? "#7c83fd" : "transparent",
                    border: `1px solid ${chartTab === tab ? "#7c83fd" : "#2d3148"}`,
                    color: chartTab === tab ? "#fff" : "#64748b",
                    padding: "3px 12px", borderRadius: 6,
                    fontSize: 12, cursor: "pointer",
                  }}
                >
                  {tab === "trend" ? "Congestion Trend" : "Peak Hours"}
                </button>
              ))}
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

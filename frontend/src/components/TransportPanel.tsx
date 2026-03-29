import { useQuery } from "@tanstack/react-query";
import { fetchTransportInsight } from "../api/client";
import { TransportInsight } from "../types";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

interface Props { junctionId: string; }

const COLORS = ["#7c83fd", "#4ade80", "#fbbf24"];

export default function TransportPanel({ junctionId }: Props) {
  const { data, isLoading } = useQuery<TransportInsight>({
    queryKey: ["transport", junctionId],
    queryFn: () => fetchTransportInsight(junctionId),
  });

  if (isLoading) return <div className="loading">Loading transport data...</div>;
  if (!data || "error" in data) return <div className="loading">No transport data yet</div>;

  const pieData = [
    { name: "Rideshare", value: Math.round(data.avg_rideshare_trips) },
    { name: "Metro", value: Math.round(data.avg_metro_boardings) },
    { name: "Bus", value: Math.round(data.avg_bus_boardings) },
  ];

  const pressureColor = data.avg_road_pressure > 0.6 ? "#f87171"
    : data.avg_road_pressure > 0.4 ? "#fbbf24" : "#4ade80";

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
        <div style={{ width: 80, height: 80 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={22} outerRadius={36}
                dataKey="value" strokeWidth={0}>
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#21253a", border: "1px solid #2d3148", borderRadius: 8, fontSize: 11 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div style={{ flex: 1 }}>
          {pieData.map((d, i) => (
            <div key={d.name} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 3 }}>
              <span style={{ color: COLORS[i] }}>● {d.name}</span>
              <span style={{ color: "#e2e8f0" }}>{d.value}/hr</span>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
        <span style={{ fontSize: 12, color: "#94a3b8" }}>Road pressure</span>
        <span style={{ fontSize: 13, fontWeight: 600, color: pressureColor }}>
          {(data.avg_road_pressure * 100).toFixed(0)}%
        </span>
      </div>

      <div style={{ fontSize: 12, color: "#64748b", fontStyle: "italic", borderTop: "1px solid #2d3148", paddingTop: 8 }}>
        {data.recommendation}
      </div>
    </div>
  );
}

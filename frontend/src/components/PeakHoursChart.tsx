import { useQuery } from "@tanstack/react-query";
import { fetchPeakHours } from "../api/client";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Cell,
} from "recharts";

interface Props { junctionId: string; }

function congestionColor(level: number): string {
  if (level < 0.25) return "#4ade80";
  if (level < 0.5)  return "#fbbf24";
  if (level < 0.75) return "#f97316";
  return "#ef4444";
}

export default function PeakHoursChart({ junctionId }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["peak-hours", junctionId],
    queryFn: () => fetchPeakHours(junctionId),
  });

  if (isLoading) return <div className="loading">Loading peak hours...</div>;
  if (!data?.length) return <div className="loading">No peak hour data yet</div>;

  const chartData = data.map((d: { hour: number; congestion_estimate: number; avg_speed_kmh: number }) => ({
    hour: `${String(d.hour).padStart(2, "0")}:00`,
    congestion: +(d.congestion_estimate * 100).toFixed(1),
    speed: d.avg_speed_kmh,
    raw: d.congestion_estimate,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData} margin={{ top: 4, right: 16, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
        <XAxis dataKey="hour" tick={{ fill: "#64748b", fontSize: 10 }} interval={2} />
        <YAxis tick={{ fill: "#64748b", fontSize: 11 }} domain={[0, 100]} unit="%" />
        <Tooltip
          contentStyle={{ background: "#21253a", border: "1px solid #2d3148", borderRadius: 8 }}
          labelStyle={{ color: "#94a3b8" }}
          formatter={(val: number) => [`${val}%`, "Congestion"]}
        />
        <Bar dataKey="congestion" radius={[3, 3, 0, 0]}>
          {chartData.map((entry: { raw: number }, i: number) => (
            <Cell key={i} fill={congestionColor(entry.raw)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

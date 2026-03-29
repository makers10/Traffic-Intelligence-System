import { useQuery } from "@tanstack/react-query";
import { fetchTrend } from "../api/client";
import { TrendPoint } from "../types";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { format } from "date-fns";

interface Props { junctionId: string; }

export default function CongestionChart({ junctionId }: Props) {
  const { data, isLoading } = useQuery<TrendPoint[]>({
    queryKey: ["trend", junctionId],
    queryFn: () => fetchTrend(junctionId),
  });

  if (isLoading) return <div className="loading">Loading trend...</div>;
  if (!data?.length) return <div className="loading">No trend data yet</div>;

  const chartData = data.map(d => ({
    time: format(new Date(d.predicted_at), "HH:mm"),
    congestion: +(d.congestion_level * 100).toFixed(1),
    speed: d.predicted_speed,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 4, right: 16, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
        <XAxis dataKey="time" tick={{ fill: "#64748b", fontSize: 11 }} />
        <YAxis tick={{ fill: "#64748b", fontSize: 11 }} domain={[0, 100]} unit="%" />
        <Tooltip
          contentStyle={{ background: "#21253a", border: "1px solid #2d3148", borderRadius: 8 }}
          labelStyle={{ color: "#94a3b8" }}
        />
        <Line type="monotone" dataKey="congestion" stroke="#7c83fd" strokeWidth={2} dot={false} name="Congestion %" />
      </LineChart>
    </ResponsiveContainer>
  );
}

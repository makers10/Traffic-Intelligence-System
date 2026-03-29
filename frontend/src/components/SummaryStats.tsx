import { useQuery } from "@tanstack/react-query";
import { fetchSummary } from "../api/client";
import { Summary } from "../types";

interface Props { junctionId: string; }

export default function SummaryStats({ junctionId }: Props) {
  const { data, isLoading } = useQuery<Summary>({
    queryKey: ["summary", junctionId],
    queryFn: () => fetchSummary(junctionId),
  });

  if (isLoading) return <div className="loading">Loading stats...</div>;
  if (!data || "error" in data) return <div className="loading">No data yet</div>;

  return (
    <div className="stats-row">
      <div className="stat-box">
        <div className="val">{data.avg_speed_kmh}</div>
        <div className="lbl">avg km/h</div>
      </div>
      <div className="stat-box">
        <div className="val">{data.avg_vehicle_density}</div>
        <div className="lbl">vehicles/km</div>
      </div>
      <div className="stat-box">
        <div className="val" style={{ color: data.accident_alerts > 0 ? "#f87171" : "#4ade80" }}>
          {data.accident_alerts}
        </div>
        <div className="lbl">alerts (24h)</div>
      </div>
    </div>
  );
}

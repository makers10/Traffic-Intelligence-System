import { useQuery } from "@tanstack/react-query";
import { fetchAlerts } from "../api/client";
import { Alert } from "../types";
import { formatDistanceToNow } from "date-fns";

interface Props { junctionId?: string; }

export default function AlertPanel({ junctionId }: Props) {
  const { data, isLoading } = useQuery<Alert[]>({
    queryKey: ["alerts", junctionId],
    queryFn: () => fetchAlerts(junctionId),
  });

  if (isLoading) return <div className="loading">Loading alerts...</div>;
  if (!data?.length) return <div className="loading">No active alerts</div>;

  return (
    <div>
      {data.map(alert => (
        <div key={alert.id} className={`alert-item ${alert.severity}`}>
          <div className="alert-title">
            🚨 {alert.severity.toUpperCase()} — {alert.junction_id}
          </div>
          <div className="alert-meta">
            Speed drop: {alert.speed_drop_pct?.toFixed(1)}% &nbsp;|&nbsp;
            Density spike: {alert.density_spike_pct?.toFixed(1)}%
          </div>
          <div className="alert-meta">
            {formatDistanceToNow(new Date(alert.detected_at), { addSuffix: true })}
          </div>
        </div>
      ))}
    </div>
  );
}

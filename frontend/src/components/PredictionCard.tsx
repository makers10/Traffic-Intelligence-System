import { useQuery } from "@tanstack/react-query";
import { fetchFusedPredict } from "../api/client";
import { FusedPrediction } from "../types";

interface Props { junctionId: string; }

export default function PredictionCard({ junctionId }: Props) {
  const { data, isLoading, error } = useQuery<FusedPrediction>({
    queryKey: ["fused-predict", junctionId],
    queryFn: () => fetchFusedPredict(junctionId),
  });

  if (isLoading) return <div className="loading">Predicting...</div>;
  if (error) return <div className="error-msg">No prediction data yet</div>;
  if (!data) return null;

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <span className={`badge ${data.label}`}>{data.label.toUpperCase()}</span>
        <span style={{ fontSize: 22, fontWeight: 700, color: "#7c83fd" }}>
          {(data.congestion_level * 100).toFixed(0)}%
        </span>
      </div>
      <div className="stats-row" style={{ marginBottom: 10 }}>
        <div className="stat-box">
          <div className="val">{data.predicted_speed?.toFixed(0)}</div>
          <div className="lbl">km/h predicted</div>
        </div>
        <div className="stat-box">
          <div className="val">{(data.confidence * 100).toFixed(0)}%</div>
          <div className="lbl">confidence</div>
        </div>
        <div className="stat-box">
          <div className="val">{(data.event_impact * 100).toFixed(0)}%</div>
          <div className="lbl">event impact</div>
        </div>
      </div>
      <div style={{ fontSize: 12, color: "#64748b" }}>
        <strong style={{ color: "#94a3b8" }}>Factors:</strong>
        <ul style={{ marginTop: 4, paddingLeft: 16 }}>
          {data.contributing_factors.map((f, i) => <li key={i}>{f}</li>)}
        </ul>
      </div>
    </div>
  );
}

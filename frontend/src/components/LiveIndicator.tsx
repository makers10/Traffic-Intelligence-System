import { useTrafficSocket } from "../hooks/useTrafficSocket";
import { formatDistanceToNow } from "date-fns";

interface Props { junctionId: string; }

export default function LiveIndicator({ junctionId }: Props) {
  const { update, connected } = useTrafficSocket(junctionId);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span className={`live-dot ${connected ? "on" : "off"}`} />
      <span style={{ fontSize: 11, fontWeight: 600, color: connected ? "#86efac" : "#94a3b8" }}>
        {connected ? "LIVE" : "offline"}
      </span>
      {update?.timestamp && (
        <span style={{ fontSize: 11, color: "#90b4d4" }}>
          · {formatDistanceToNow(new Date(update.timestamp), { addSuffix: true })}
        </span>
      )}
      {update && update.active_alerts > 0 && (
        <span style={{
          fontSize: 11, fontWeight: 700,
          color: "#fca5a5", background: "rgba(239,68,68,0.2)",
          padding: "2px 8px", borderRadius: 10,
        }}>
          {update.active_alerts} alert{update.active_alerts > 1 ? "s" : ""}
        </span>
      )}
    </div>
  );
}

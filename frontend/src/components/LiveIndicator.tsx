import { useTrafficSocket } from "../hooks/useTrafficSocket";
import { formatDistanceToNow } from "date-fns";

interface Props { junctionId: string; }

export default function LiveIndicator({ junctionId }: Props) {
  const { update, connected } = useTrafficSocket(junctionId);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0" }}>
      {/* Connection dot */}
      <span style={{
        width: 8, height: 8, borderRadius: "50%",
        background: connected ? "#4ade80" : "#64748b",
        display: "inline-block",
        boxShadow: connected ? "0 0 6px #4ade80" : "none",
      }} />
      <span style={{ fontSize: 12, color: connected ? "#4ade80" : "#64748b" }}>
        {connected ? "LIVE" : "disconnected"}
      </span>

      {update?.prediction && (
        <>
          <span style={{ fontSize: 12, color: "#64748b", marginLeft: 8 }}>
            {formatDistanceToNow(new Date(update.timestamp), { addSuffix: true })}
          </span>
          {update.active_alerts > 0 && (
            <span style={{
              marginLeft: "auto", fontSize: 11, fontWeight: 600,
              color: "#f87171", background: "#450a0a",
              padding: "2px 8px", borderRadius: 12,
            }}>
              🚨 {update.active_alerts} alert{update.active_alerts > 1 ? "s" : ""}
            </span>
          )}
        </>
      )}
    </div>
  );
}

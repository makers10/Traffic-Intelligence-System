import { useEffect, useRef, useState } from "react";

export interface LiveUpdate {
  type: string;
  junction_id: string;
  timestamp: string;
  prediction?: {
    congestion_level: number;
    label: string;
    predicted_speed: number;
    contributing_factors: string[];
  };
  active_alerts: number;
  alert_severity: string | null;
}

export function useTrafficSocket(junctionId: string) {
  const [update, setUpdate] = useState<LiveUpdate | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const wsUrl = `ws://${window.location.hostname}:8000/ws/${junctionId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as LiveUpdate;
        if (data.type === "update") setUpdate(data);
      } catch {}
    };

    return () => {
      ws.close();
      setConnected(false);
    };
  }, [junctionId]);

  return { update, connected };
}

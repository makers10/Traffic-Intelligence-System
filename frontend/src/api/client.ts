import axios from "axios";

export const api = axios.create({ baseURL: "/api/v1" });

export const fetchAlerts = (junctionId?: string) =>
  api.get("/alerts", { params: junctionId ? { junction_id: junctionId } : {} }).then(r => r.data);

export const fetchSummary = (junctionId: string, hours = 24) =>
  api.get(`/analytics/${junctionId}/summary`, { params: { hours } }).then(r => r.data);

export const fetchTrend = (junctionId: string, hours = 6) =>
  api.get(`/analytics/${junctionId}/trend`, { params: { hours } }).then(r => r.data);

export const fetchPeakHours = (junctionId: string) =>
  api.get(`/analytics/${junctionId}/peak-hours`).then(r => r.data);

export const fetchFusedPredict = (junctionId: string, horizon = 30) =>
  api.post(`/analytics/${junctionId}/fused-predict`, null, { params: { horizon_minutes: horizon } }).then(r => r.data);

export const fetchBulkCongestion = (): Promise<Record<string, { junction_id: string; congestion_level: number; predicted_speed: number | null; confidence: number | null }>> =>
  api.get("/analytics/bulk-congestion").then(r => r.data);

export const fetchWeather = (junctionId: string, lat: number, lon: number) =>
  api.post("/weather", { junction_id: junctionId, lat, lon }).then(r => r.data);

export const fetchTransportInsight = (junctionId: string) =>
  api.get(`/transport/${junctionId}/insight`).then(r => r.data);

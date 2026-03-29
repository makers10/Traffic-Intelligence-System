export interface Junction {
  id: string;
  name: string;
  lat: number;
  lon: number;
}

export interface Alert {
  id: number;
  junction_id: string;
  detected_at: string;
  severity: "low" | "medium" | "high";
  speed_drop_pct: number;
  density_spike_pct: number;
  is_confirmed: boolean;
}

export interface Summary {
  junction_id: string;
  avg_speed_kmh: number;
  min_speed_kmh: number;
  max_speed_kmh: number;
  avg_vehicle_density: number;
  total_readings: number;
  accident_alerts: number;
}

export interface TrendPoint {
  predicted_at: string;
  congestion_level: number;
  predicted_speed: number;
  confidence: number;
}

export interface FusedPrediction {
  junction_id: string;
  congestion_level: number;
  label: string;
  predicted_speed: number;
  confidence: number;
  event_impact: number;
  road_pressure_index: number;
  contributing_factors: string[];
}

export interface WeatherData {
  condition: string;
  temperature: number;
  impact_score: number;
  explanation: string;
  visibility_m: number;
  precipitation_mm: number;
}

export interface TransportInsight {
  avg_rideshare_trips: number;
  avg_metro_boardings: number;
  avg_bus_boardings: number;
  avg_road_pressure: number;
  recommendation: string;
}

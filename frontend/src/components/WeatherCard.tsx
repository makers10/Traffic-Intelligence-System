import { useQuery } from "@tanstack/react-query";
import { fetchWeather } from "../api/client";
import { WeatherData, Junction } from "../types";

const WEATHER_ICONS: Record<string, string> = {
  clear: "☀️", clouds: "☁️", rain: "🌧️",
  thunderstorm: "⛈️", snow: "❄️", fog: "🌫️",
  mist: "🌫️", drizzle: "🌦️", haze: "🌁",
};

interface Props { junction: Junction; }

export default function WeatherCard({ junction }: Props) {
  const { data, isLoading } = useQuery<WeatherData>({
    queryKey: ["weather", junction.id],
    queryFn: () => fetchWeather(junction.id, junction.lat, junction.lon),
  });

  if (isLoading) return <div className="loading">Fetching weather...</div>;
  if (!data) return null;

  const icon = WEATHER_ICONS[data.condition?.toLowerCase()] ?? "🌡️";
  const impactColor = data.impact_score > 0.5 ? "#f87171" : data.impact_score > 0.2 ? "#fbbf24" : "#4ade80";

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
        <span style={{ fontSize: 28 }}>{icon}</span>
        <div>
          <div style={{ fontWeight: 600 }}>{data.condition} · {data.temperature?.toFixed(1)}°C</div>
          <div style={{ fontSize: 12, color: "#64748b" }}>
            Visibility: {(data.visibility_m / 1000).toFixed(1)} km &nbsp;|&nbsp;
            Rain: {data.precipitation_mm?.toFixed(1)} mm
          </div>
        </div>
        <div style={{ marginLeft: "auto", textAlign: "right" }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: impactColor }}>
            {(data.impact_score * 100).toFixed(0)}%
          </div>
          <div style={{ fontSize: 11, color: "#64748b" }}>impact</div>
        </div>
      </div>
      <div style={{ fontSize: 12, color: "#94a3b8", fontStyle: "italic" }}>{data.explanation}</div>
    </div>
  );
}

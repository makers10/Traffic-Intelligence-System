import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { Junction } from "../types";

interface Props {
  junctions: Junction[];
  congestionMap: Record<string, number>;
  selectedId: string;
  onSelect: (id: string) => void;
}

function congestionColor(level: number): string {
  if (level < 0.25) return "#4ade80";
  if (level < 0.5)  return "#fbbf24";
  if (level < 0.75) return "#f97316";
  return "#ef4444";
}

export default function TrafficMap({ junctions, congestionMap, selectedId, onSelect }: Props) {
  const center: [number, number] = [12.9716, 77.5946];

  return (
    <MapContainer center={center} zoom={12} className="leaflet-container" style={{ height: "100%", width: "100%" }}>
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
      />
      {junctions.map(j => {
        const level = congestionMap[j.id] ?? 0;
        return (
          <CircleMarker
            key={j.id}
            center={[j.lat, j.lon]}
            radius={selectedId === j.id ? 18 : 12}
            pathOptions={{
              color: congestionColor(level),
              fillColor: congestionColor(level),
              fillOpacity: 0.8,
              weight: selectedId === j.id ? 3 : 1,
            }}
            eventHandlers={{ click: () => onSelect(j.id) }}
          >
            <Popup>
              <strong>{j.name}</strong><br />
              Congestion: {(level * 100).toFixed(0)}%
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}

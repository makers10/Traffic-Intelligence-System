import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { useEffect } from "react";
import { Junction } from "../types";

interface Props {
  junctions: Junction[];
  congestionMap: Record<string, number>;
  selectedId: string;
  onSelect: (id: string) => void;
}

function congestionColor(level: number): string {
  if (level < 0.25) return "#22c55e";
  if (level < 0.5)  return "#eab308";
  if (level < 0.75) return "#f97316";
  return "#ef4444";
}

// Auto-pan to selected junction
function PanToSelected({ junctions, selectedId }: { junctions: Junction[]; selectedId: string }) {
  const map = useMap();
  useEffect(() => {
    const j = junctions.find(j => j.id === selectedId);
    if (j) map.setView([j.lat, j.lon], 14, { animate: true });
  }, [selectedId]);
  return null;
}

export default function TrafficMap({ junctions, congestionMap, selectedId, onSelect }: Props) {
  // Centered on Bengaluru, zoomed in
  const center: [number, number] = [12.9716, 77.5946];

  return (
    <MapContainer
      center={center}
      zoom={13}
      className="leaflet-container"
      style={{ height: "100%", width: "100%" }}
      zoomControl={true}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
      />
      <PanToSelected junctions={junctions} selectedId={selectedId} />
      {junctions.map(j => {
        const level = congestionMap[j.id] ?? 0;
        const isSelected = selectedId === j.id;
        return (
          <CircleMarker
            key={j.id}
            center={[j.lat, j.lon]}
            radius={isSelected ? 16 : 10}
            pathOptions={{
              color: "#fff",
              fillColor: congestionColor(level),
              fillOpacity: 0.9,
              weight: isSelected ? 3 : 1.5,
            }}
            eventHandlers={{ click: () => onSelect(j.id) }}
          >
            <Popup>
              <div style={{ fontFamily: "sans-serif", minWidth: 140 }}>
                <strong style={{ fontSize: 13 }}>{j.name}</strong><br />
                <span style={{ fontSize: 12, color: "#64748b" }}>
                  Congestion: {(level * 100).toFixed(0)}%
                </span>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}

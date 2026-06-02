import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import type { Chamado, Equipe, Abrigo, Estacao, Geofence, Rota } from "../types";

// Basemaps selecionáveis — todos sem API key.
const STYLES: Record<string, any> = {
  escuro: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
  claro: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
  satelite: {
    version: 8,
    sources: {
      esri: {
        type: "raster",
        tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
        tileSize: 256, attribution: "Esri World Imagery",
      },
      esriRef: {
        type: "raster",
        tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}"],
        tileSize: 256,
      },
    },
    layers: [
      { id: "esri", type: "raster", source: "esri" },
      { id: "esriRef", type: "raster", source: "esriRef" },
    ],
  },
};

const ESTILOS_UI: { id: keyof typeof STYLES; rotulo: string; icone: string }[] = [
  { id: "escuro", rotulo: "Escuro", icone: "🌙" },
  { id: "claro", rotulo: "Claro", icone: "☀️" },
  { id: "satelite", rotulo: "Satélite", icone: "🛰️" },
];

const SEV_COR: Record<string, string> = {
  normal: "#64748b", atencao: "#eab308", alerta: "#f97316", inundacao: "#ef4444",
};

const COR_POR_ESTADO: any = [
  "match", ["get", "estado"],
  "aguardando", "#ef4444", "triado", "#ef4444",
  "despachado", "#f97316", "assumido", "#f97316",
  "no_local", "#eab308", "resgatado", "#22c55e",
  "em_abrigo", "#3b82f6", "perdido_contato", "#a855f7",
  "#ef4444",
];

interface Props {
  chamados: Chamado[];
  equipes: Equipe[];
  abrigos: Abrigo[];
  estacoes: Estacao[];
  geofences: Geofence[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  rota?: Rota | null;
}

function parsePoly(p: any): any {
  if (!p) return null;
  return typeof p === "string" ? JSON.parse(p) : p;
}

function domMarker(bg: string, emoji: string, title: string): HTMLElement {
  const el = document.createElement("div");
  el.style.cssText = `width:30px;height:30px;border-radius:50%;background:${bg};
    border:2px solid rgba(255,255,255,.85);box-shadow:0 2px 8px rgba(0,0,0,.6);
    display:flex;align-items:center;justify-content:center;font-size:15px;cursor:default;`;
  el.textContent = emoji;
  el.title = title;
  return el;
}

function estacaoMarker(sev: string, label: string): HTMLElement {
  const cor = SEV_COR[sev] ?? "#64748b";
  const alarme = sev === "alerta" || sev === "inundacao";
  const el = document.createElement("div");
  el.style.cssText = "display:flex;align-items:center;gap:6px;pointer-events:none;";
  el.innerHTML =
    `<span style="width:20px;height:20px;border-radius:50%;background:${cor};` +
    `border:2px solid #fff;box-shadow:0 0 0 ${alarme ? "6px" : "2px"} ${cor}55;"></span>` +
    `<span style="background:rgba(2,6,23,.88);color:#e2e8f0;font-size:12px;font-weight:700;` +
    `padding:3px 7px;border-radius:7px;white-space:nowrap;border:1px solid ${cor};">${label}</span>`;
  return el;
}

function chamadosFC(chamados: Chamado[]): any {
  return {
    type: "FeatureCollection",
    features: chamados
      .filter((c) => c.lat != null && c.lng != null && c.estado !== "duplicado")
      .map((c) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: [c.lng, c.lat] },
        properties: { id: c.id, estado: c.estado, score: c.prioridade_score },
      })),
  };
}

function rotaFC(rota?: Rota | null): any {
  if (!rota?.geometry) return { type: "FeatureCollection", features: [] };
  return { type: "FeatureCollection", features: [{ type: "Feature", geometry: rota.geometry, properties: {} }] };
}

function geofencesFC(geofences: Geofence[]): any {
  return {
    type: "FeatureCollection",
    features: geofences
      .map((g) => ({ g, poly: parsePoly(g.poligono) }))
      .filter((x) => x.poly)
      .map(({ g, poly }) => ({
        type: "Feature",
        geometry: poly,
        properties: { id: g.id, severidade: g.severidade ?? "nenhuma" },
      })),
  };
}

// Adiciona sources + layers (chamado no load e após cada troca de estilo,
// pois setStyle remove tudo que é customizado).
function addLayers(m: maplibregl.Map) {
  if (m.getSource("geofences")) return;
  m.addSource("geofences", { type: "geojson", data: geofencesFC([]) });
  m.addSource("chamados", { type: "geojson", data: chamadosFC([]) });
  m.addSource("rota", { type: "geojson", data: rotaFC(null) });

  m.addLayer({
    id: "geofence-fill", type: "fill", source: "geofences",
    paint: {
      "fill-color": ["match", ["get", "severidade"],
        "inundacao", "#ef4444", "alerta", "#f97316", "atencao", "#eab308", "#3b82f6"],
      "fill-opacity": ["match", ["get", "severidade"],
        "inundacao", 0.32, "alerta", 0.24, "atencao", 0.15, 0.07],
    },
  });
  m.addLayer({
    id: "geofence-line", type: "line", source: "geofences",
    paint: {
      "line-color": ["match", ["get", "severidade"],
        "inundacao", "#ef4444", "alerta", "#f97316", "atencao", "#eab308", "#3b82f6"],
      "line-width": 2.5, "line-dasharray": [2, 1],
    },
  });
  // Rota traçada (abaixo dos chamados): contorno escuro + linha clara por cima.
  m.addLayer({
    id: "rota-casing", type: "line", source: "rota",
    layout: { "line-cap": "round", "line-join": "round" },
    paint: { "line-color": "#0c4a6e", "line-width": 9, "line-opacity": 0.9 },
  });
  m.addLayer({
    id: "rota-line", type: "line", source: "rota",
    layout: { "line-cap": "round", "line-join": "round" },
    paint: { "line-color": "#38bdf8", "line-width": 5 },
  });
  m.addLayer({
    id: "chamados-heat", type: "heatmap", source: "chamados",
    paint: {
      "heatmap-weight": ["interpolate", ["linear"], ["get", "score"], 0, 0, 150, 1],
      "heatmap-color": ["interpolate", ["linear"], ["heatmap-density"],
        0, "rgba(0,0,0,0)", 0.4, "rgba(234,179,8,0.5)", 0.8, "rgba(239,68,68,0.85)"],
      "heatmap-radius": 34,
      "heatmap-opacity": ["interpolate", ["linear"], ["zoom"], 11, 0.6, 15, 0.12],
    },
  });
  m.addLayer({
    id: "chamados-sel", type: "circle", source: "chamados",
    filter: ["==", ["get", "id"], ""],
    paint: { "circle-radius": 16, "circle-color": "rgba(56,189,248,0.15)",
      "circle-stroke-color": "#38bdf8", "circle-stroke-width": 3 },
  });
  m.addLayer({
    id: "chamados-circ", type: "circle", source: "chamados",
    paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 11, 5, 16, 11],
      "circle-color": COR_POR_ESTADO,
      "circle-stroke-color": "#fff", "circle-stroke-width": 1.5, "circle-opacity": 0.92,
    },
  });
}

export default function CommandMap(props: Props) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const ready = useRef(false);
  const domMarkers = useRef<maplibregl.Marker[]>([]);
  const dataRef = useRef(props);
  dataRef.current = props;
  const [estilo, setEstilo] = useState<keyof typeof STYLES>("satelite");

  function aplicar() {
    const m = map.current;
    if (!m || !ready.current || !m.getSource("geofences")) return;
    const { chamados, equipes, abrigos, estacoes, geofences, selectedId } = dataRef.current;

    (m.getSource("geofences") as maplibregl.GeoJSONSource).setData(geofencesFC(geofences));
    (m.getSource("chamados") as maplibregl.GeoJSONSource).setData(chamadosFC(chamados));
    const rotaSrc = m.getSource("rota") as maplibregl.GeoJSONSource | undefined;
    if (rotaSrc) rotaSrc.setData(rotaFC(dataRef.current.rota));
    m.setFilter("chamados-sel", ["==", ["get", "id"], selectedId ?? ""]);

    domMarkers.current.forEach((mk) => mk.remove());
    domMarkers.current = [];
    estacoes.forEach((e) => {
      if (e.lat == null || e.lng == null) return;
      const label = `${e.rio ?? e.nome}: ${e.nivel_atual ?? "?"}${e.unidade}`;
      domMarkers.current.push(
        new maplibregl.Marker({ element: estacaoMarker(e.severidade, label) })
          .setLngLat([e.lng, e.lat]).addTo(m));
    });
    abrigos.forEach((a) => {
      if (a.lat == null) return;
      const cheio = a.ocupacao >= a.capacidade;
      const el = domMarker(cheio ? "#7f1d1d" : "#0ea5e9", a.pet_friendly ? "🐾" : "🏠",
        `${a.nome} — ${a.ocupacao}/${a.capacidade}${a.pet_friendly ? " (pet)" : ""}`);
      domMarkers.current.push(new maplibregl.Marker({ element: el }).setLngLat([a.lng, a.lat]).addTo(m));
    });
    equipes.forEach((e) => {
      if (e.lat == null) return;
      const el = domMarker(e.status === "disponivel" ? "#16a34a" : "#6b7280", "🚤", `${e.nome} (${e.status})`);
      domMarkers.current.push(new maplibregl.Marker({ element: el }).setLngLat([e.lng!, e.lat]).addTo(m));
    });
  }

  function trocarEstilo(novo: keyof typeof STYLES) {
    const m = map.current;
    if (!m || novo === estilo) return;
    setEstilo(novo);
    // setStyle remove sources/layers customizados. Reaplicamos quando o novo
    // basemap terminou de carregar — 'idle' é o momento confiável p/ isso.
    m.setStyle(STYLES[novo]);
    m.once("idle", () => { addLayers(m); aplicar(); });
  }

  useEffect(() => {
    if (!container.current || map.current) return;
    const m = new maplibregl.Map({
      container: container.current,
      style: STYLES.satelite,
      center: [-51.9614, -29.4669],
      zoom: 13,
    });
    map.current = m;
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    m.on("load", () => {
      addLayers(m);
      m.on("click", "chamados-circ", (e) => {
        const id = e.features?.[0]?.properties?.id;
        if (id) dataRef.current.onSelect(String(id));
      });
      m.on("mouseenter", "chamados-circ", () => { m.getCanvas().style.cursor = "pointer"; });
      m.on("mouseleave", "chamados-circ", () => { m.getCanvas().style.cursor = ""; });
      ready.current = true;
      aplicar();
    });

    return () => { m.remove(); map.current = null; ready.current = false; };
  }, []);

  useEffect(() => { aplicar(); });

  // Ao traçar uma rota, enquadra o mapa para mostrá-la inteira.
  useEffect(() => {
    const m = map.current;
    const coords = props.rota?.geometry?.coordinates;
    if (!m || !ready.current || !coords?.length) return;
    const b = coords.reduce(
      (bb: maplibregl.LngLatBounds, c: [number, number]) => bb.extend(c),
      new maplibregl.LngLatBounds(coords[0], coords[0]),
    );
    m.fitBounds(b, { padding: 70, maxZoom: 16, duration: 700 });
  }, [props.rota]);

  return (
    <div className="w-full h-full relative">
      <div ref={container} className="w-full h-full" />
      <div className="absolute bottom-3 left-3 z-10 flex rounded-lg overflow-hidden shadow-lg border border-slate-700">
        {ESTILOS_UI.map((s) => (
          <button
            key={s.id}
            onClick={() => trocarEstilo(s.id)}
            className={`px-3 py-2 text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              estilo === s.id ? "bg-sky-600 text-white" : "bg-slate-900/90 text-slate-300 hover:bg-slate-800"
            }`}
          >
            <span>{s.icone}</span>{s.rotulo}
          </button>
        ))}
      </div>
    </div>
  );
}

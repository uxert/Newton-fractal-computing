import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type {config} from "./model.ts";

let tileLayer: L.TileLayer | null = null;

function buildTileUrl(configObj: config) {
  const params = new URLSearchParams();
  Object.entries(configObj).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
          params.set(key, String(value));
      }
  });

  return `http://127.0.0.1:8000/api/tiles/{z}/{x}/{y}.png?${params.toString()}`;
}

const DEFAULT_CONFIG: config = {
    coeffs: [1, 0, -3, 2],
    n: 200,
    iterations: 100,
}

export function createMap(elementId: string) {
  const MyCRS = L.extend({}, L.CRS.Simple, {
    transformation: new L.Transformation(40, 0, -40, 0),
  });

  const map = L.map(elementId, {
    crs: MyCRS,
    minZoom: 0,
    maxZoom: 30,
    zoomSnap: 1,
  }).setView([0.0, 0.0], 0);

  tileLayer = L.tileLayer(buildTileUrl(DEFAULT_CONFIG), {
    tileSize: 200,
    maxZoom: 30,
    attribution: "me",
  }).addTo(map);

  return map;
}

export function setParameters(configObj: config) {
  if (!tileLayer) {
    throw new Error("Tile layer not initialized. Call createMap() first.");
  }

  tileLayer.setUrl(buildTileUrl(configObj));
}
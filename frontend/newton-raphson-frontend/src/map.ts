import L from "leaflet";
import "leaflet/dist/leaflet.css";

let tileLayer: L.TileLayer | null = null;

function buildTileUrl(coefficients: number[]) {
  const coeffs = encodeURIComponent(coefficients.join(","));

  return `http://127.0.0.1:8000/api/tiles/{z}/{x}/{y}.png?coeffs=${coeffs}`;
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

  tileLayer = L.tileLayer(buildTileUrl([1, 0, -3, 2]), {
    tileSize: 200,
    maxZoom: 30,
    attribution: "me",
  }).addTo(map);

  return map;
}

export function setParameters(coefficients: number[]) {
  if (!tileLayer) {
    throw new Error("Tile layer not initialized. Call createMap() first.");
  }

  tileLayer.setUrl(buildTileUrl(coefficients));
}
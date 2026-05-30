import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type {config} from "./model.ts";
import {MAP_CONFIG as MC, DEFAULTS} from "./constants.ts";

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
    coeffs: DEFAULTS.DEFAULT_COEFFICIENTS,
    n: DEFAULTS.DEFAULT_N,
    iterations: DEFAULTS.DEFAULT_ITERS,
}

export function createMap(elementId: string) {
  const MyCRS = L.extend({}, L.CRS.Simple, {
    transformation: new L.Transformation(40, 0, -40, 0),
  });

  const map = L.map(elementId, {
    crs: MyCRS,
    minZoom: MC.MIN_ZOOM,
    maxZoom: MC.MAX_ZOOM,
    zoomSnap: MC.ZOOM_SNAP,
  }).setView([MC.STARTING_VIEW[0], MC.STARTING_VIEW[1]], MC.STARTING_ZOOM);

  tileLayer = L.tileLayer(buildTileUrl(DEFAULT_CONFIG), {
    tileSize: MC.TILE_SIZE,
    maxZoom: MC.MAX_ZOOM,
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
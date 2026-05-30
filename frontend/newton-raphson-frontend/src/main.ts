import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./style.css";

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App container not found");
}

app.innerHTML = `
  <div id="map"></div>

  <div id="config-panel">
    <h3>Backend Config</h3>

    <label>
      Radius
      <input id="radius" type="number" value="1000" />
    </label>

    <label>
      Mode
      <select id="mode">
        <option value="fast">Fast</option>
        <option value="accurate">Accurate</option>
      </select>
    </label>

    <button id="save-btn">Save</button>

    <div id="status"></div>
  </div>
`;

const MyCRS = L.extend({}, L.CRS.Simple, {
      transformation: new L.Transformation(40, 0, -40, 0)
    });



const map = L.map('map', {
      crs: MyCRS,
      minZoom: 0,
      maxZoom: 30,
      zoomSnap: 1
    }).setView([0.0, 0.0], 0);


L.tileLayer('http://127.0.0.1:8000/api/tiles/{z}/{x}/{y}.png', {
tileSize: 200,
maxZoom: 30,
attribution: 'me'
}).addTo(map);

type Config = {
  radius: number;
  mode: "fast" | "accurate";
};

const saveButton =
  document.querySelector<HTMLButtonElement>("#save-btn")!;

const status =
  document.querySelector<HTMLDivElement>("#status")!;

saveButton.addEventListener("click", async () => {
  const radius =
    document.querySelector<HTMLInputElement>("#radius")!;

  const mode =
    document.querySelector<HTMLSelectElement>("#mode")!;

  const config: Config = {
    radius: Number(radius.value),
    mode: mode.value as Config["mode"],
  };

  try {
    const response = await fetch(
      "http://localhost:8000/config",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(config),
      }
    );

    if (!response.ok) {
      throw new Error("Backend error");
    }

    status.textContent = "Saved";
  } catch (err) {
    console.error(err);
    status.textContent = "Failed";
  }
});
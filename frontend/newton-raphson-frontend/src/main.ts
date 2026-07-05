import "./style.css";
import { createConfigPanel } from "./configPanel";
import { createMap } from "./map";

document.querySelector<HTMLDivElement>("#app")!.innerHTML = `
  <div id="map"></div>
  <div id="config-panel"></div>
`;

createConfigPanel("config-panel");
createMap("map");

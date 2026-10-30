import { formatPolynomial, parseCoefficients } from "./polynomial";
import { setParameters } from "./map";
import type {config} from "./model.ts";
import {DEFAULTS} from "./constants.ts";

export function createConfigPanel(elementId: string) {
  const panel = document.querySelector<HTMLDivElement>(`#${elementId}`);

  if (!panel) {
    throw new Error(`Config panel #${elementId} not found`);
  }

panel.innerHTML = `
  <button id="config-fab" class="config-fab" hidden>⚙ Config</button>

  <div id="config-content" class="config-content">
    <div class="config-header">
      <h3>Parameters config</h3>
      <button id="minimize-config" type="button">×</button>
    </div>

    <label>
      Coefficients
      <input
        id="coefficients"
        type="text"
        value="${DEFAULTS.DEFAULT_COEFFICIENTS_PLACEHOLDER}"
        placeholder="e.g. ${DEFAULTS.DEFAULT_COEFFICIENTS_PLACEHOLDER}"
      />
    </label>

    <div id="polynomial-preview"></div>

    <label>
      Pixels per unit (resolution)
      <input
        id="n"
        type="number"
        value="${DEFAULTS.DEFAULT_N}"
        placeholder="${DEFAULTS.DEFAULT_N}"
      />
    </label>

    <label>
      Iterations
      <input
        id="iterations"
        type="number"
        value="${DEFAULTS.DEFAULT_ITERS}"
      />
    </label>

    <button id="save-btn">Save</button>

    <div id="status"></div>
  </div>
  `;

      // hide and show the panel
  const fab = panel.querySelector<HTMLButtonElement>("#config-fab");
  const content = panel.querySelector<HTMLDivElement>("#config-content");
  const minimizeBtn = panel.querySelector<HTMLButtonElement>("#minimize-config");

  if (!fab || !content || !minimizeBtn || !panel) {
    throw new Error("Config panel controls not found");
  }

  function setConfigMinimized(minimized: boolean) {
  if (!fab || !content || !minimizeBtn || !panel) {
    throw new Error("Config panel controls not found");
  }
    fab.hidden = !minimized;
    content.hidden = minimized;
    panel.classList.toggle("config-panel-minimized", minimized);
  }

  minimizeBtn.addEventListener("click", () => {
    setConfigMinimized(true);
  });

  fab.addEventListener("click", () => {
    setConfigMinimized(false);
  });

  // Inputs

  const coefficientsInput =
    panel.querySelector<HTMLInputElement>("#coefficients")!;

  const nInput =
      panel.querySelector<HTMLInputElement>("#n")!;

  const iterationsInput =
      panel.querySelector<HTMLInputElement>("#iterations")!;

  const polynomialPreview =
    panel.querySelector<HTMLDivElement>("#polynomial-preview")!;

  const saveButton =
    panel.querySelector<HTMLButtonElement>("#save-btn")!;

  const status =
    panel.querySelector<HTMLDivElement>("#status")!;

  function updatePreview() {
    const coefficients = parseCoefficients(coefficientsInput.value);

    if (!coefficients) {
      polynomialPreview.textContent = "Invalid polynomial";
      return;
    }

    polynomialPreview.innerHTML = formatPolynomial(coefficients);
  }

  async function onFormSubmit() {
    const coefficients = parseCoefficients(coefficientsInput.value);
    console.log("Button sth sth")

    if (!coefficients) {
      status.textContent = "Invalid coefficients";
      return;
    }
    const configObj: config = {
        coeffs: coefficients,
        n: nInput.valueAsNumber,
        iterations: iterationsInput.valueAsNumber,
    }
    setParameters(configObj);
  }

  saveButton.addEventListener("click", onFormSubmit);

  coefficientsInput.addEventListener("input", updatePreview);

  const allInputs = content.querySelectorAll<HTMLInputElement>("input");
  allInputs.forEach((input) => {
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        saveButton.click();
      }
    });
  });

  updatePreview();
}
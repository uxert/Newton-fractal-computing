import { formatPolynomial, parseCoefficients } from "./polynomial";
import { setParameters } from "./map";
import type {config} from "./model.ts";


export function createConfigPanel(elementId: string) {
  const panel = document.querySelector<HTMLDivElement>(`#${elementId}`);

  if (!panel) {
    throw new Error(`Config panel #${elementId} not found`);
  }

  panel.innerHTML = `
    <h3>Polynomial Config</h3>

    <label>
      Coefficients
      <input
        id="coefficients"
        type="text"
        value="1, 0, -3, 2"
        placeholder="e.g. 1, 0, -3, 2"
      />
    </label>

    <div id="polynomial-preview"></div>
    <label>
    N
    <input
      id="n"
      type="number"
      value="200"
      placeholder="200">
    </label>
    <label>
    Iterations
    <input
    id="iterations"
    type="number"
    value="100"
    placeholder="100">
    </label>

    <button id="save-btn">Save</button>

    <div id="status"></div>
  `;

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

  saveButton.addEventListener("click", async () => {
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
  });

  coefficientsInput.addEventListener("input", updatePreview);

  coefficientsInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      saveButton.click();
    }
  });

  updatePreview();
}
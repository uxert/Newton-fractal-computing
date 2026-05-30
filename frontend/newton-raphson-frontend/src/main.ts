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
    <div id="polynomial-preview">Enter coefficients...</div>  

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
  coefficients: number[];
};

const saveButton =
  document.querySelector<HTMLButtonElement>("#save-btn")!;

const status =
  document.querySelector<HTMLDivElement>("#status")!;

saveButton.addEventListener("click", async () => {
  const coefficientsInput =
    document.querySelector<HTMLInputElement>("#coefficients")!;

  const coefficients = coefficientsInput.value
    .split(",")
    .map((value) => Number(value.trim()));

  const hasInvalidCoefficient = coefficients.some(Number.isNaN);

  if (hasInvalidCoefficient || coefficients.length === 0) {
    status.textContent = "Invalid coefficients";
    return;
  }

  const config: Config = {
    coefficients,
  };

  try {
    const response = await fetch("http://localhost:8000/config", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      throw new Error("Backend error");
    }

    status.textContent = "Saved";
  } catch (err) {
    console.error(err);
    status.textContent = "Failed";
  }
});

const coefficientsInput =
  document.querySelector<HTMLInputElement>("#coefficients")!;

const polynomialPreview =
  document.querySelector<HTMLDivElement>("#polynomial-preview")!;

function formatPolynomial(coefficients: number[]): string {
  const degree = coefficients.length - 1;

  const terms = coefficients
    .map((coef, index) => {
      if (coef === 0) return null;

      const power = degree - index;
      const absCoef = Math.abs(coef);

      let variablePart = "";

      if (power === 1) {
        variablePart = "x";
      } else if (power > 1) {
        variablePart = `x<sup>${power}</sup>`;
      }

      let coefficientPart = "";

      if (power === 0) {
        coefficientPart = String(absCoef);
      } else if (absCoef !== 1) {
        coefficientPart = String(absCoef);
      }

      return {
        sign: coef < 0 ? "-" : "+",
        term: `${coefficientPart}${variablePart}`,
      };
    })
    .filter(Boolean);

  if (terms.length === 0) {
    return "0";
  }

  return terms
    .map((term, index) => {
      if (index === 0) {
        return term!.sign === "-"
          ? `-${term!.term}`
          : term!.term;
      }

      return ` ${term!.sign} ${term!.term}`;
    })
    .join("");
}

function parseCoefficients(value: string): number[] | null {
  const coefficients = value
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part.length > 0)
    .map(Number);

  if (coefficients.some(Number.isNaN)) {
    return null;
  }

  return coefficients;
}

function updatePolynomialPreview() {
  const coefficients = parseCoefficients(coefficientsInput.value);

  if (!coefficients) {
    polynomialPreview.textContent = "Invalid coefficients";
    return;
  }

  polynomialPreview.innerHTML =
    formatPolynomial(coefficients);
}

coefficientsInput.addEventListener("input", updatePolynomialPreview);
updatePolynomialPreview();
export type PolynomialConfig = {
  coefficients: number[];
};

export async function saveConfig(config: PolynomialConfig) {
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
}
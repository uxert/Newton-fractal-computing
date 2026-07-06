export function formatPolynomial(coefficients: number[]): string {
  const degree = coefficients.length - 1;

  const terms = coefficients
    .reverse()  // coefficients are given in ascending order, processed in descending order...
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
    .filter(Boolean)
    .reverse()  // ...but should be rendered again in ascending order :);

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

export function parseCoefficients(value: string): number[] | null {
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

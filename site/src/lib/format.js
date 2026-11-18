// Formats français : espace fine pour les milliers, virgule décimale.
const nf = (digits) =>
  new Intl.NumberFormat("fr-FR", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const num = (v, digits = 0) => nf(digits).format(v);

export const pct = (v, digits = 0) => `${nf(digits).format(v * 100)}\u202f%`;

export const pts = (v, digits = 0) => `${nf(digits).format(v * 100)} point${Math.abs(v * 100) >= 2 ? "s" : ""}`;

// 13 900 000 -> "13,9 millions"
export const big = (v) => {
  if (v >= 1e6) return `${nf(1).format(v / 1e6).replace(",0", "")} million${v >= 2e6 ? "s" : ""}`;
  if (v >= 1e4) return `${nf(0).format(Math.round(v / 1e3))} 000`;
  return nf(0).format(v);
};

// 0.21 -> "un sur cinq" quand la fraction est proche d'une fraction simple
export const oneIn = (p) => {
  const n = Math.round(1 / p);
  const words = { 2: "deux", 3: "trois", 4: "quatre", 5: "cinq", 6: "six", 7: "sept", 8: "huit", 9: "neuf", 10: "dix" };
  return words[n] && Math.abs(1 / n - p) < 0.015 ? `un sur ${words[n]}` : pct(p);
};

export const hour = (h) => `${h} h`;

export const MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
export const MONTHS_LONG = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];

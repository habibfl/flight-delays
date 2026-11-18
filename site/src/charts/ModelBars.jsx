import { useInView, useWidth } from "../lib/hooks";
import { num } from "../lib/format";

const LABELS = {
  "Référence naïve (taux moyen)": "Deviner au hasard",
  Calendrier: "Date et heure",
  "Calendrier + compagnie et liaison": "+ compagnie et trajet",
  "Tout, avec la météo": "+ météo au départ",
};

// AUC sur la période de test : 0,5 = hasard, 1 = prédiction parfaite.
export default function ModelBars({ scores }) {
  const [ref, width] = useWidth(620);
  const [viewRef, seen] = useInView();
  const rows = scores
    .filter((s) => s.modele !== "Régression logistique")
    .map((s) => ({ ...s, label: LABELS[s.variables] || LABELS[s.modele] || s.variables }));
  const m = { left: 170, right: 56 };
  const x = (v) => m.left + ((v - 0.5) / 0.5) * (width - m.left - m.right);
  const rowH = 44;

  return (
    <div className="chart" ref={ref}>
      <svg width={width} height={rows.length * rowH + 30} ref={viewRef}>
        {[0.5, 0.6, 0.7, 0.8, 0.9, 1].map((t) => (
          <g key={t} className="axis" transform={`translate(${x(t)},0)`}>
            <line y1="0" y2={rows.length * rowH} stroke="#efeee9" />
            <text y={rows.length * rowH + 20} textAnchor="middle">{num(t, 1)}</text>
          </g>
        ))}
        {rows.map((r, i) => {
          const color = r.modele.startsWith("Référence") ? "#b5b2aa" : r.variables.includes("météo") ? "#eb6834" : "#2a78d6";
          const w = Math.max(2, x(r.auc) - x(0.5));
          return (
            <g key={i} transform={`translate(0,${i * rowH})`}>
              <text x={m.left - 14} y={rowH / 2} dy="0.35em" textAnchor="end" fontSize="15">{r.label}</text>
              <rect x={x(0.5)} y="9" height={rowH - 18} width={seen ? w : 0} fill={color} rx="3"
                style={{ transition: `width .9s ${i * 0.12}s cubic-bezier(.2,.8,.2,1)` }} />
              <text className="value-label" x={x(0.5) + (seen ? w : 0) + 8} y={rowH / 2} dy="0.35em"
                style={{ transition: `x .9s ${i * 0.12}s cubic-bezier(.2,.8,.2,1)` }}>
                {num(r.auc, 2)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

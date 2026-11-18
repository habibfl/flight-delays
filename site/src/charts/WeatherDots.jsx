import * as d3 from "d3";
import { useState } from "react";
import { useWidth } from "../lib/hooks";
import { num, pct } from "../lib/format";
import { Toggle, Tooltip } from "../components/ui";

// Météo au départ : taux de retard brut par condition, ou effet à conditions égales
// (odds ratio de la régression logistique, 1 = comme par ciel dégagé).
export default function WeatherDots({ weather, adjusted }) {
  const [ref, width] = useWidth(620);
  const [mode, setMode] = useState("raw");
  const [tip, setTip] = useState(null);
  const raw = mode === "raw";

  const clear = weather.find((w) => w.condition === "Dégagé");
  const adjMap = Object.fromEntries(adjusted.map((a) => [a.condition, a]));
  const rows = raw
    ? weather
    : [{ condition: "Dégagé", odds_ratio: 1, lo: 1, hi: 1 }, ...adjusted];
  const order = [...rows].sort((a, b) => (raw ? a.delayed - b.delayed : a.odds_ratio - b.odds_ratio));

  // Odds ratio brut, pour montrer ce que l'ajustement enlève.
  const odds = (p) => p / (1 - p);
  const rawOR = (c) => (clear ? odds(weather.find((w) => w.condition === c).delayed) / odds(clear.delayed) : null);

  const m = { top: 8, right: 70, bottom: 34, left: 92 };
  const rowH = 38;
  const height = m.top + m.bottom + rowH * order.length;
  const vals = raw
    ? order.flatMap((d) => [d.lo, d.hi])
    : order.flatMap((d) => [d.lo, d.hi, rawOR(d.condition)]).filter(Boolean);
  const x = (raw ? d3.scaleLinear().domain([0, d3.max(vals) * 1.08]) : d3.scaleLog().domain([Math.min(0.85, d3.min(vals)), d3.max(vals) * 1.12]))
    .range([m.left, width - m.right]);
  if (raw) x.nice();
  const y = (i) => m.top + rowH * i + rowH / 2;
  const ref0 = raw ? clear?.delayed : 1;

  return (
    <div className="chart" ref={ref}>
      <Toggle
        options={[
          { value: "raw", label: "Taux de retard" },
          { value: "adj", label: "À conditions égales" },
        ]}
        value={mode}
        onChange={setMode}
      />
      <div style={{ position: "relative" }}>
        <svg width={width} height={height} onMouseLeave={() => setTip(null)}>
          <g className="axis">
            {(raw ? x.ticks(5) : [0.9, 1, 1.5, 2, 3, 5, 7, 10].filter((t) => t >= x.domain()[0] && t <= x.domain()[1])).map((t) => (
              <g key={t} transform={`translate(${x(t)},0)`}>
                <line y1={m.top} y2={height - m.bottom} stroke="#efeee9" />
                <text y={height - m.bottom + 20} textAnchor="middle">{raw ? pct(t) : `×${num(t, t % 1 ? 2 : 0)}`}</text>
              </g>
            ))}
          </g>
          {ref0 != null && (
            <line x1={x(ref0)} x2={x(ref0)} y1={m.top} y2={height - m.bottom} stroke="#1a1a1a" strokeDasharray="3 4" />
          )}
          {order.map((d, i) => {
            const v = raw ? d.delayed : d.odds_ratio;
            const above = v > ref0 * (raw ? 1.15 : 1.1);
            const color = d.condition === "Dégagé" ? "#1a1a1a" : above ? "#eb6834" : "#2a78d6";
            const r0 = !raw && d.condition !== "Dégagé" ? rawOR(d.condition) : null;
            const w = weather.find((ww) => ww.condition === d.condition);
            return (
              <g key={d.condition}
                onMouseEnter={() =>
                  setTip({
                    x: x(v),
                    y: y(i) - 6,
                    content: raw ? (
                      <>
                        <b>{d.condition}</b>
                        {pct(d.delayed, 1)} des vols en retard
                        <br />
                        {pct(d.cancelled, 1)} annulés
                        <br />
                        <span className="muted">{num(d.flights)} vols</span>
                      </>
                    ) : (
                      <>
                        <b>{d.condition}</b>
                        Cote de retard ×{num(v, 2)}
                        {r0 && (<><br /><span className="muted">×{num(r0, 2)} sans ajustement</span></>)}
                        {w && (<><br /><span className="muted">{num(w.flights)} vols</span></>)}
                      </>
                    ),
                  })
                }>
                <rect x="0" y={y(i) - rowH / 2} width={width} height={rowH} fill="transparent" />
                <text x={m.left - 14} y={y(i)} dy="0.35em" textAnchor="end" fontSize="15">{d.condition}</text>
                <line x1={x(d.lo)} x2={x(d.hi)} y1={y(i)} y2={y(i)} stroke={color} strokeWidth="2" strokeOpacity="0.5"
                  style={{ transition: "all .6s" }} />
                {r0 && <circle cx={x(r0)} cy={y(i)} r="5" fill="none" stroke="#8a8880" strokeWidth="1.5" style={{ transition: "all .6s" }} />}
                <circle cx={x(v)} cy={y(i)} r="7.5" fill={color} stroke="#fff" strokeWidth="2" style={{ transition: "all .6s" }} />
                <text className="value-label" x={x(Math.max(v, d.hi)) + 12} y={y(i)} dy="0.35em" style={{ transition: "all .6s" }}>
                  {raw ? pct(v) : d.condition === "Dégagé" ? "référence" : `×${num(v, 1)}`}
                </text>
              </g>
            );
          })}
        </svg>
        <Tooltip tip={tip} />
      </div>
      {!raw && (
        <p className="caption" style={{ marginTop: 4 }}>
          Point plein : effet à heure, mois, jour, aéroport et compagnie égaux. Cercle gris : écart brut, avant
          ajustement. ×2 = la cote d'un retard double par rapport à un ciel dégagé.
          {Object.keys(adjMap).length === 0 && " Ajustement indisponible."}
        </p>
      )}
    </div>
  );
}

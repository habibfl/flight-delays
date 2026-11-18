import * as d3 from "d3";
import { useMemo, useState } from "react";
import { useWidth } from "../lib/hooks";
import { num, pct } from "../lib/format";
import { Toggle, Tooltip } from "../components/ui";

const TYPE_COLORS = {
  "Grande compagnie": "#2a78d6",
  "Low cost": "#1baf7a",
  "Ultra low cost": "#eb6834",
  "Régionale": "#6250d6",
  Inconnue: "#8a8880",
};

// Une bulle par compagnie, placée selon sa part de vols en retard
// (essaim de points : les bulles se poussent pour ne pas se chevaucher).
export default function CarrierSwarm({ carriers }) {
  const [ref, width] = useWidth(900);
  const [year, setYear] = useState("all");
  const [tip, setTip] = useState(null);

  const years = Object.keys(carriers[0] || {})
    .filter((k) => /^delayed_\d{4}$/.test(k))
    .map((k) => k.slice(8));
  const field = year === "all" ? "delayed" : `delayed_${year}`;
  const height = width < 600 ? 260 : 290;
  const m = { top: 20, right: 30, bottom: 34, left: 30 };

  const { nodes, x, mean } = useMemo(() => {
    const vals = carriers.flatMap((c) => [c.delayed, ...years.map((y) => c[`delayed_${y}`])]).filter((v) => v != null);
    const x = d3.scaleLinear().domain([d3.min(vals) - 0.015, d3.max(vals) + 0.015]).range([m.left, width - m.right]).nice();
    const r = d3.scaleSqrt().domain([0, d3.max(carriers, (c) => c.flights)]).range([0, width < 600 ? 20 : 30]);
    const nodes = carriers
      .filter((c) => c[field] != null)
      .map((c) => ({ ...c, value: c[field], r: Math.max(9, r(c.flights)), x: x(c[field]), y: height / 2 }));
    const sim = d3
      .forceSimulation(nodes)
      .force("x", d3.forceX((d) => x(d.value)).strength(1))
      .force("y", d3.forceY((height - m.bottom) / 2 + 4).strength(0.06))
      .force("collide", d3.forceCollide((d) => d.r + 1.5).iterations(3))
      .stop();
    for (let i = 0; i < 280; i++) sim.tick();
    // Étiquette sous la bulle si une autre bulle occupe l'espace au-dessus.
    for (const d of nodes) {
      const ly = d.y - d.r - 9;
      d.below = nodes.some((o) => o !== d && Math.abs(o.x - d.x) < o.r + 10 && Math.abs(o.y - ly) < o.r + 6);
    }
    const total = d3.sum(carriers, (c) => c.flights);
    const mean = d3.sum(nodes, (c) => c.value * c.flights) / total;
    return { nodes, x, mean };
  }, [carriers, field, width, height, years, m.left, m.right, m.bottom]);

  return (
    <div className="chart" ref={ref}>
      {years.length > 1 && (
        <Toggle
          options={[...years.map((y) => ({ value: y, label: y })), { value: "all", label: "Les deux ans" }]}
          value={year}
          onChange={setYear}
        />
      )}
      <div style={{ position: "relative" }}>
      <svg width={width} height={height} onMouseLeave={() => setTip(null)}>
        <g className="axis" transform={`translate(0,${height - m.bottom})`}>
          {x.ticks(width < 600 ? 4 : 7).map((t) => (
            <g key={t} transform={`translate(${x(t)},0)`}>
              <line y1={-(height - m.bottom - m.top)} y2="0" stroke="#efeee9" />
              <text y="20" textAnchor="middle">{pct(t)}</text>
            </g>
          ))}
        </g>
        <line x1={x(mean)} x2={x(mean)} y1={m.top - 8} y2={height - m.bottom} stroke="#1a1a1a" strokeDasharray="3 4" />
        <text className="mark-label" x={x(mean) + 6} y={m.top} >moyenne {pct(mean, 1)}</text>
        {nodes.map((d) => (
          <g
            key={d.code}
            style={{ transform: `translate(${d.x}px, ${d.y}px)`, transition: "transform 0.7s cubic-bezier(.2,.8,.2,1)", cursor: "pointer" }}
            onMouseEnter={() =>
              setTip({
                x: d.x,
                y: d.y - d.r,
                content: (
                  <>
                    <b>{d.name}</b>
                    <span className="muted">{d.type}</span>
                    <br />
                    {pct(d.value, 1)} des vols en retard
                    <br />
                    <span className="muted">{num(d.flights)} vols</span>
                  </>
                ),
              })
            }
          >
            <circle r={d.r} fill={TYPE_COLORS[d.type] || TYPE_COLORS.Inconnue} stroke="#fff" strokeWidth="2" />
            {d.r >= 13 ? (
              <text textAnchor="middle" dy="0.35em" fill="#fff" fontFamily="var(--mono)" fontSize={d.r > 20 ? 12 : 10} fontWeight="700">
                {d.code}
              </text>
            ) : (
              <text textAnchor="middle" y={d.below ? d.r + 13 : -d.r - 5} fill="#4d4c48" fontFamily="var(--mono)" fontSize="10" fontWeight="700">
                {d.code}
              </text>
            )}
          </g>
        ))}
      </svg>
      <Tooltip tip={tip} />
      </div>
      <div className="ends">
        <span>← plus ponctuelles</span>
        <span>plus souvent en retard →</span>
      </div>
      <div className="toggle" style={{ marginTop: 14 }}>
        {Object.entries(TYPE_COLORS)
          .filter(([t]) => carriers.some((c) => c.type === t))
          .map(([t, c]) => (
            <span key={t} style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 13.5, color: "var(--ink-2)", marginRight: 10 }}>
              <svg width="12" height="12"><circle cx="6" cy="6" r="6" fill={c} /></svg>
              {t}
            </span>
          ))}
      </div>
    </div>
  );
}

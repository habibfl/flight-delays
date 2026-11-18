import * as d3 from "d3";
import { feature, mesh } from "topojson-client";
import us from "us-atlas/states-albers-10m.json";
import { useMemo, useState } from "react";
import { useWidth } from "../lib/hooks";
import { num, pct } from "../lib/format";
import { Tooltip } from "../components/ui";

// Le fond us-atlas est déjà projeté (Albers, 975 × 610) : on projette les
// aéroports avec la même projection pour qu'ils tombent au bon endroit.
const projection = d3.geoAlbersUsa().scale(1300).translate([487.5, 305]);
const nation = feature(us, us.objects.nation);
const borders = mesh(us, us.objects.states, (a, b) => a !== b);
const path = d3.geoPath();

// Étiquettes des plus gros aéroports, en sautant celles qui chevaucheraient une autre.
function labelled(points, max) {
  const kept = [];
  for (const a of points) {
    if (kept.length >= max) break;
    const ly = a.py - a.r - 5;
    if (kept.every((b) => Math.abs(b.px - a.px) > 38 || Math.abs(b.py - b.r - 5 - ly) > 16)) kept.push(a);
  }
  return kept;
}

export default function AirportMap({ airports, mean }) {
  const [ref, width] = useWidth(960);
  const [tip, setTip] = useState(null);
  const k = width / 975;
  const height = 610 * k;

  const points = useMemo(() => {
    const r = d3.scaleSqrt().domain([0, d3.max(airports, (a) => a.flights)]).range([0, 26]);
    const ext = d3.max(airports, (a) => Math.abs(a.delayed - mean)) || 0.01;
    const color = d3.scaleLinear().domain([-ext, 0, ext]).range(["#2a78d6", "#d9d6cf", "#eb6834"]).clamp(true);
    return airports
      .map((a) => {
        const p = projection([a.lon, a.lat]);
        return p && { ...a, px: p[0], py: p[1], r: Math.max(3, r(a.flights)), fill: color(a.delayed - mean) };
      })
      .filter(Boolean)
      .sort((a, b) => b.flights - a.flights);
  }, [airports, mean]);

  return (
    <div className="chart" ref={ref}>
      <div style={{ position: "relative" }}>
        <svg width={width} height={height} viewBox="0 0 975 610" onMouseLeave={() => setTip(null)}>
          <path d={path(nation)} fill="#f3f2ee" />
          <path d={path(borders)} fill="none" stroke="#fff" strokeWidth="1.2" />
          {points.map((a) => (
            <circle key={a.code} cx={a.px} cy={a.py} r={a.r} fill={a.fill} stroke="#fff" strokeWidth="1.2" fillOpacity="0.92"
              style={{ cursor: "pointer" }}
              onMouseEnter={() =>
                setTip({
                  x: a.px * k,
                  y: (a.py - a.r) * k,
                  content: (
                    <>
                      <b>{a.code} · {a.city}</b>
                      {pct(a.delayed, 1)} des départs en retard
                      <br />
                      {pct(a.cancelled, 1)} annulés
                      <br />
                      <span className="muted">{num(a.flights)} vols au départ</span>
                    </>
                  ),
                })
              } />
          ))}
          {labelled(points, width < 600 ? 6 : 14).map((a) => (
            <text key={a.code} x={a.px} y={a.py - a.r - 5} textAnchor="middle" fontFamily="var(--mono)" fontSize={13 / Math.max(k, 0.6)}
              fontWeight="700" fill="#1a1a1a" pointerEvents="none" paintOrder="stroke" stroke="#fff" strokeWidth={3 / Math.max(k, 0.6)}>
              {a.code}
            </text>
          ))}
        </svg>
        <Tooltip tip={tip} />
      </div>
      <div className="ends" style={{ justifyContent: "flex-start", gap: 22, flexWrap: "wrap" }}>
        <span><span style={{ color: "#2a78d6" }}>●</span> plus ponctuel que la moyenne</span>
        <span><span style={{ color: "#eb6834" }}>●</span> plus souvent en retard</span>
        <span>taille = nombre de départs</span>
      </div>
    </div>
  );
}

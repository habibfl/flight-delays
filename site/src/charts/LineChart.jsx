import * as d3 from "d3";
import { useId, useState } from "react";
import { useInView, useWidth } from "../lib/hooks";
import { pct } from "../lib/format";
import { Tooltip } from "../components/ui";

// Courbes avec étiquette en bout de ligne et repère vertical au survol.
// series : [{ name, color, values: [{ x, y }] }] ; x : nombres ordonnés.
export default function LineChart({ series, xTicks, xLabel = (v) => v, yFormat = (v) => pct(v), height = 320, yMin = 0, tipTitle = xLabel }) {
  const [ref, width] = useWidth(640);
  const [viewRef, seen] = useInView();
  const [hover, setHover] = useState(null);
  const clipId = `reveal-${useId().replace(/:/g, "")}`;
  const m = { top: 16, right: 86, bottom: 32, left: 44 };

  const xs = series[0].values.map((v) => v.x);
  const x = d3.scalePoint().domain(xs).range([m.left, width - m.right]).padding(0.2);
  const all = series.flatMap((s) => s.values.map((v) => v.y));
  const y = d3.scaleLinear().domain([yMin, d3.max(all) * 1.1]).range([height - m.bottom, m.top]).nice();
  const line = d3.line().x((d) => x(d.x)).y((d) => y(d.y)).curve(d3.curveMonotoneX);

  // Étiquettes de fin écartées si elles se chevauchent.
  const ends = series.map((s) => ({ s, y: y(s.values.at(-1).y) })).sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 16) ends[i].y = ends[i - 1].y + 16;

  const onMove = (e) => {
    const [mx] = d3.pointer(e);
    const step = x.step();
    const i = Math.max(0, Math.min(xs.length - 1, Math.round((mx - x(xs[0])) / step)));
    setHover(xs[i]);
  };

  return (
    <div className="chart" ref={ref}>
      <div ref={viewRef} style={{ position: "relative" }}>
        <svg width={width} height={height} onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
          <defs>
            <clipPath id={clipId}>
              <rect x="0" y="0" height={height} width={seen ? width : 0} style={{ transition: "width 1.4s ease-out" }} />
            </clipPath>
          </defs>
          <g className="axis">
            {y.ticks(4).map((t) => (
              <g key={t} transform={`translate(0,${y(t)})`}>
                <line x1={m.left} x2={width - m.right} stroke="#efeee9" />
                <text x={m.left - 8} dy="0.32em" textAnchor="end">{yFormat(t)}</text>
              </g>
            ))}
            {(xTicks || xs).map((t) => (
              <text key={t} x={x(t)} y={height - m.bottom + 20} textAnchor="middle">{xLabel(t)}</text>
            ))}
          </g>
          {hover != null && <line x1={x(hover)} x2={x(hover)} y1={m.top} y2={height - m.bottom} stroke="#1a1a1a" strokeOpacity="0.25" />}
          <g clipPath={`url(#${clipId})`}>
            {series.map((s) => (
              <g key={s.name}>
                <path d={line(s.values)} fill="none" stroke={s.color} strokeWidth="2.5" strokeLinejoin="round" />
                {s.values.map((v) => (
                  <circle key={v.x} cx={x(v.x)} cy={y(v.y)} r={hover === v.x ? 5.5 : 3.5} fill={s.color} stroke="#fff" strokeWidth="1.5" />
                ))}
              </g>
            ))}
          </g>
          {ends.map(({ s, y: ly }) => (
            <text key={s.name} x={width - m.right + 10} y={ly} dy="0.35em" fill={s.color} fontWeight="700" fontSize="13.5"
              style={{ opacity: seen ? 1 : 0, transition: "opacity .4s 1.3s" }}>
              {s.name}
            </text>
          ))}
        </svg>
        {hover != null && (
          <Tooltip
            tip={{
              x: x(hover),
              y: y(d3.max(series, (s) => s.values.find((v) => v.x === hover)?.y ?? 0)),
              content: (
                <>
                  <b>{tipTitle(hover)}</b>
                  {series.map((s) => {
                    const v = s.values.find((vv) => vv.x === hover);
                    return v ? (
                      <div key={s.name}>
                        <span style={{ color: s.color, fontWeight: 700 }}>●</span> {s.name} : {yFormat(v.y, 1)}
                      </div>
                    ) : null;
                  })}
                </>
              ),
            }}
          />
        )}
      </div>
    </div>
  );
}

import * as d3 from "d3";
import { useId, useState } from "react";
import { useInView, useWidth } from "../lib/hooks";
import { pct } from "../lib/format";
import { Hatch, Tooltip } from "../components/ui";

// Barres hachurées « dessinées à la main ». data : [{ key, label, value, tip, highlight }]
// labels : clés des barres dont on écrit la valeur au-dessus.
export default function HatchedBars({ data, labels = [], height = 300, format = (v) => pct(v), yMax }) {
  const [ref, width] = useWidth(640);
  const [viewRef, seen] = useInView();
  const [tip, setTip] = useState(null);
  const id = useId().replace(/:/g, "");
  const m = { top: 26, right: 4, bottom: 30, left: 40 };

  const x = d3.scaleBand().domain(data.map((d) => d.key)).range([m.left, width - m.right]).padding(0.28);
  const y = d3.scaleLinear().domain([0, yMax ?? d3.max(data, (d) => d.value) * 1.12]).range([height - m.bottom, m.top]).nice();
  const every = Math.ceil(data.length / Math.max(4, Math.floor(width / 48)));

  return (
    <div className="chart" ref={ref}>
      <div ref={viewRef}>
        <svg width={width} height={height} onMouseLeave={() => setTip(null)}>
          <defs>
            <Hatch id={`h-${id}`} color="#1a1a1a" />
            <Hatch id={`hh-${id}`} color="#eb6834" />
          </defs>
          <g className="axis">
            {y.ticks(4).map((t) => (
              <g key={t} transform={`translate(0,${y(t)})`}>
                <line x1={m.left} x2={width - m.right} stroke="#efeee9" />
                <text x={m.left - 8} dy="0.32em" textAnchor="end">{format(t)}</text>
              </g>
            ))}
          </g>
          {data.map((d, i) => {
            const h = seen ? y(0) - y(d.value) : 0;
            return (
              <g key={d.key}
                onMouseEnter={() => d.tip && setTip({ x: x(d.key) + x.bandwidth() / 2, y: y(d.value), content: d.tip })}>
                <rect x={x(d.key) - 2} y={m.top} width={x.bandwidth() + 4} height={height - m.top - m.bottom} fill="transparent" />
                <rect
                  x={x(d.key)}
                  width={x.bandwidth()}
                  y={y(0) - h}
                  height={h}
                  fill={`url(#${d.highlight ? "hh" : "h"}-${id})`}
                  stroke={d.highlight ? "#eb6834" : "#1a1a1a"}
                  strokeWidth="1.5"
                  rx="1.5"
                  style={{ transition: `y 0.8s ${i * 0.03}s cubic-bezier(.2,.8,.2,1), height 0.8s ${i * 0.03}s cubic-bezier(.2,.8,.2,1)` }}
                />
                {labels.includes(d.key) && (
                  <text className="value-label" x={x(d.key) + x.bandwidth() / 2} y={y(d.value) - 8} textAnchor="middle"
                    style={{ opacity: seen ? 1 : 0, transition: "opacity 0.4s 0.8s" }}>
                    {format(d.value)}
                  </text>
                )}
                {i % every === 0 && (
                  <text className="tick-label" x={x(d.key) + x.bandwidth() / 2} y={height - m.bottom + 18} textAnchor="middle">
                    {d.label}
                  </text>
                )}
              </g>
            );
          })}
          <line x1={m.left} x2={width - m.right} y1={y(0)} y2={y(0)} stroke="#1a1a1a" />
        </svg>
      </div>
      <Tooltip tip={tip} />
    </div>
  );
}

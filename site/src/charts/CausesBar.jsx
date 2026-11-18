import { useInView, useWidth } from "../lib/hooks";
import { pct } from "../lib/format";

const COLORS = {
  late_aircraft: "#eb6834",
  carrier: "#2a78d6",
  nas: "#7fb3f0",
  weather: "#1baf7a",
  security: "#b5b2aa",
};

// Une seule barre empilée à 100 % : la part des minutes de retard par cause.
export default function CausesBar({ causes }) {
  const [ref, width] = useWidth(620);
  const [viewRef, seen] = useInView();
  const starts = causes.map((_, i) => causes.slice(0, i).reduce((acc, c) => acc + c.share, 0));
  const segs = causes.map((c, i) => ({ ...c, x0: starts[i] * width, w: c.share * width }));

  return (
    <div className="chart" ref={ref}>
      <svg width={width} height="64" ref={viewRef}>
        {segs.map((s, i) => (
          <g key={s.key}>
            <rect
              x={seen ? s.x0 : 0}
              width={seen ? Math.max(0, s.w - 2) : 0}
              y="0"
              height="64"
              fill={COLORS[s.key]}
              rx="3"
              style={{ transition: `all 0.9s ${i * 0.12}s cubic-bezier(.2,.8,.2,1)` }}
            />
            {s.w > 56 && (
              <text x={s.x0 + 10} y="38" fill="#fff" fontWeight="700" fontSize="16"
                style={{ opacity: seen ? 1 : 0, transition: "opacity .4s 1s" }}>
                {pct(s.share)}
              </text>
            )}
          </g>
        ))}
      </svg>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "6px 18px", marginTop: 14 }}>
        {causes.map((c) => (
          <div key={c.key} style={{ display: "flex", gap: 8, alignItems: "baseline", fontSize: 15 }}>
            <span style={{ width: 11, height: 11, borderRadius: 3, background: COLORS[c.key], flex: "none", transform: "translateY(1px)" }} />
            <span>
              {c.label} <b>{pct(c.share, c.share < 0.01 ? 1 : 0)}</b>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

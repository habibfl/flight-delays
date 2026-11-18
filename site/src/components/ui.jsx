// Briques communes : cadre de figure, boutons « Afficher : », info-bulle.

export function Figure({ title, sub, caption, wide = false, children }) {
  return (
    <figure className={`figure ${wide ? "wide" : "col"}`}>
      {title && <p className="figure-title">{title}</p>}
      {sub && <p className="figure-sub">{sub}</p>}
      {children}
      {caption && <figcaption className="caption">{caption}</figcaption>}
    </figure>
  );
}

export function Toggle({ label = "Afficher :", options, value, onChange }) {
  return (
    <div className="toggle" role="group" aria-label={label}>
      <span className="label">{label}</span>
      {options.map((o) => (
        <button key={o.value} type="button" aria-pressed={value === o.value} onClick={() => onChange(o.value)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Tooltip({ tip }) {
  if (!tip) return null;
  return (
    <div className="tooltip" style={{ left: tip.x, top: tip.y }} role="status">
      {tip.content}
    </div>
  );
}

// Motif de hachures dessinées à la main pour les barres.
export function Hatch({ id, color = "#1a1a1a", gap = 5 }) {
  return (
    <pattern id={id} patternUnits="userSpaceOnUse" width={gap} height={gap} patternTransform="rotate(-35)">
      <line x1="0" y1="0" x2="0" y2={gap} stroke={color} strokeWidth={gap * 0.55} />
    </pattern>
  );
}

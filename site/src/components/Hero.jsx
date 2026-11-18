import { big, num, oneIn } from "../lib/format";

// Silhouette d'avion, orientée vers la droite (sens de la rotation en haut de l'orbite).
const PLANE =
  "M11 0c0 .9-.9 1.5-2.1 1.5H3.3L-1.3 9.2h-2.1L-1.1 1.5h-4.7l-1.8 2.4h-1.7L-8.3 0l-1-3.9h1.7l1.8 2.4h4.7L-3.4-9.2h2.1l4.6 7.7h5.6C10.1-1.5 11-.9 11 0z";

const ORBITS = [
  { r: 92, color: "#3a8de0", speed: 16, start: 20 },
  { r: 138, color: "#eb6834", speed: 26, start: 200 },
  { r: 184, color: "#1baf7a", speed: 40, start: 110 },
];

// Arc derrière l'avion : sa traînée sur l'orbite.
function trail(r, degrees) {
  const a = (-90 - degrees) * (Math.PI / 180);
  const x = 200 + r * Math.cos(a);
  const y = 200 + r * Math.sin(a);
  return `M${x.toFixed(2)},${y.toFixed(2)} A${r},${r} 0 0 1 200,${200 - r}`;
}

function Orbits() {
  return (
    <svg className="hero-orbits" viewBox="0 0 400 400" role="img" aria-label="Trois avions en orbite autour d'un aéroport">
      <defs>
        {ORBITS.map((o, i) => (
          <linearGradient key={i} id={`trail-${i}`} gradientUnits="userSpaceOnUse"
            x1={200 + o.r * Math.cos(-2.3)} y1={200 + o.r * Math.sin(-2.3)} x2="200" y2={200 - o.r}>
            <stop offset="0" stopColor={o.color} stopOpacity="0" />
            <stop offset="1" stopColor={o.color} stopOpacity="0.9" />
          </linearGradient>
        ))}
      </defs>
      {ORBITS.map((o) => (
        <circle key={o.r} cx="200" cy="200" r={o.r} fill="none" stroke="#8f8bb3" strokeOpacity="0.35" strokeWidth="1" />
      ))}
      {/* L'aéroport, au centre */}
      <circle cx="200" cy="200" r="38" fill="#f6c945" />
      <rect x="174" y="196" width="52" height="8" rx="2" fill="#110f2e" opacity="0.85" transform="rotate(-35 200 200)" />
      <g transform="rotate(-35 200 200)" fill="#f6c945">
        {[-18, -6, 6, 18].map((x) => <rect key={x} x={200 + x - 2.5} y="199" width="5" height="2" />)}
      </g>
      {ORBITS.map((o, i) => (
        <g key={i} style={{ transform: `rotate(${o.start}deg)`, transformOrigin: "200px 200px" }}>
          <g className="orbit" style={{ animationDuration: `${o.speed}s` }}>
            <path d={trail(o.r, 55)} fill="none" stroke={`url(#trail-${i})`} strokeWidth="2.5" strokeLinecap="round" />
            <path d={PLANE} fill={o.color} transform={`translate(200 ${200 - o.r}) scale(1.35)`} />
          </g>
        </g>
      ))}
    </svg>
  );
}

export default function Hero({ k }) {
  return (
    <header className="hero">
      <div className="hero-nav">
        <span className="brand">flight-delays</span>
        <nav>
          <a href="#histoire">L'histoire</a>
          <a href="#methode">Méthode</a>
          <a href="https://github.com/habibfl/flight-delays">Code</a>
        </nav>
      </div>
      <div className="hero-body">
        <Orbits />
        <div className="hero-text">
          {k ? (
            <h1>
              Chaque jour, <b>{num(Math.round(k.flights_per_day / 1000) * 1000)} vols</b> décollent aux États-Unis.{" "}
              {oneIn(k.delayed).startsWith("un") ? (
                <><b>{oneIn(k.delayed).replace(/^un/, "Un")}</b> arrive en retard.</>
              ) : (
                <><b>{oneIn(k.delayed)}</b> arrivent en retard.</>
              )} Ce qui les retarde n'est pas
              toujours <b>ce que l'on croit</b>.
            </h1>
          ) : (
            <h1>Ce qui retarde vraiment un avion.</h1>
          )}
          <p>
            Une data story sur {k ? big(k.flights) : "des millions de"} vols intérieurs en 2024 et 2025, croisés
            heure par heure avec la météo de leur aéroport de départ.
          </p>
        </div>
      </div>
      <a className="hero-cue" href="#histoire">
        Faire défiler
        <span aria-hidden="true">↓</span>
      </a>
    </header>
  );
}

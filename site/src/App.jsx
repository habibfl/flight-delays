import * as d3 from "d3";
import Hero from "./components/Hero";
import { Figure } from "./components/ui";
import AirportMap from "./charts/AirportMap";
import CarrierSwarm from "./charts/CarrierSwarm";
import CausesBar from "./charts/CausesBar";
import HatchedBars from "./charts/HatchedBars";
import LineChart from "./charts/LineChart";
import ModelBars from "./charts/ModelBars";
import WeatherDots from "./charts/WeatherDots";
import { useStory } from "./lib/hooks";
import { big, hour, MONTHS, MONTHS_LONG, num, pct } from "./lib/format";

const REPO = "https://github.com/habibfl/flight-delays";
const SOURCE = "Source : BTS (vols), Open-Meteo (météo), OurAirports. Traitement : flight-delays.";

// Les chiffres cités dans le texte sont tous calculés à partir des données.
function facts(d) {
  const k = d.kpis;
  const c = d.carriers;
  const hours = d.hourly.filter((h) => h.flights >= 20000);
  const bestH = d3.least(hours, (h) => h.delayed);
  const worstH = d3.greatest(hours, (h) => h.delayed);
  const after = d.cascade.after_previous;
  const byCause = Object.fromEntries(d.causes.map((x) => [x.key, x]));
  const topCause = d.causes[0];
  const w = Object.fromEntries(d.weather.map((x) => [x.condition, x]));
  const adj = Object.fromEntries((d.weather_adjusted || []).map((x) => [x.condition, x]));
  const worstWeather = d3.greatest(d.weather, (x) => x.delayed);
  const months = d3.rollups(d.monthly, (v) => d3.sum(v, (x) => x.delayed * x.flights) / d3.sum(v, (x) => x.flights), (x) => x.month);
  const worstM = d3.greatest(months, (x) => x[1]);
  const bestM = d3.least(months, (x) => x[1]);
  const bigAirports = d.airports.filter((a) => a.flights >= 100000);
  const pool = bigAirports.length >= 4 ? bigAirports : d.airports;
  const scores = d.model?.scores || [];
  const auc = (v) => scores.find((s) => s.modele === "Gradient boosting" && s.variables === v)?.auc;
  return {
    k,
    best: c[0],
    worst: c[c.length - 1],
    bestH,
    worstH,
    after,
    byCause,
    topCause,
    w,
    adj,
    worstWeather,
    worstM: worstM && { month: worstM[0], value: worstM[1] },
    bestM: bestM && { month: bestM[0], value: bestM[1] },
    worstAirport: d3.greatest(pool, (a) => a.delayed),
    bestAirport: d3.least(pool, (a) => a.delayed),
    aucNoWeather: auc("Calendrier + compagnie et liaison"),
    aucWeather: auc("Tout, avec la météo"),
  };
}

export default function App() {
  const { data, error } = useStory();
  const f = data && facts(data);

  return (
    <>
      <Hero k={data?.kpis} />
      {error && <div className="loading">Données indisponibles ({error.message}).</div>}
      {!data && !error && <div className="loading">Chargement des données…</div>}
      {f && <Story d={data} f={f} />}
      <Footer />
    </>
  );
}

function Story({ d, f }) {
  const { k } = f;
  const clear = f.w["Dégagé"];
  const worstW = f.worstWeather;
  const worstAdj = f.adj[worstW.condition];
  const worstRawOR = clear ? (worstW.delayed / (1 - worstW.delayed)) / (clear.delayed / (1 - clear.delayed)) : null;
  const under = { Neige: "Sous la neige", Pluie: "Sous la pluie", Bruine: "Sous la bruine", Orage: "Par temps d'orage", Brouillard: "Dans le brouillard" };
  const m10 = (y, mo) => d.monthly.find((x) => x.year === y && x.month === mo)?.delayed;
  const shutdownGap = [10, 11].map((mo) => (m10(2025, mo) ?? 0) - (m10(2024, mo) ?? 0));
  const mean = d3.sum(d.airports, (a) => a.delayed * a.flights) / d3.sum(d.airports, (a) => a.flights);

  return (
    <main id="histoire">
      <section className="prose intro">
        <p className="lede">
          En 2024 et 2025, {big(k.flights)} de vols ont décollé d'un aéroport américain.{" "}
          <span className="hl">{pct(k.delayed)}</span> sont arrivés avec au moins un quart d'heure de retard, et{" "}
          {pct(k.cancelled, 1)} ont été annulés.
        </p>
        <p>
          Mis bout à bout, ces retards font <strong>{num(Math.round(k.hours_lost / 1e5) * 1e5)} heures</strong>,
          soit plus de {num(Math.floor(k.hours_lost / 24 / 365))} années passées à attendre. Mais tous les vols ne
          sont pas égaux. Voici chaque compagnie, placée selon la part de ses vols arrivés en retard.
        </p>
      </section>

      <Figure
        wide
        title="Part des vols arrivés avec 15 minutes de retard ou plus, par compagnie"
        sub="Chaque bulle est une compagnie ; sa taille indique le nombre de vols. Survoler ou toucher pour le détail."
        caption={`${SOURCE} Compagnies ayant opéré au moins 20 000 vols.`}
      >
        <CarrierSwarm carriers={d.carriers} />
      </Figure>

      <section className="prose">
        <p>
          L'écart est large : <strong>{f.best.name}</strong> arrive en retard sur {pct(f.best.delayed)} de ses vols,{" "}
          <strong>{f.worst.name}</strong> sur {pct(f.worst.delayed)}. Mais la compagnie n'explique qu'une partie de
          l'histoire. L'heure du décollage, l'avion lui-même et le ciel jouent aussi, et pas toujours dans le sens que
          l'on imagine.
        </p>
      </section>

      <section className="masthead">
        <h2>Ce qui retarde vraiment un avion</h2>
        <p className="byline">
          Par <a href="https://github.com/habibfl">Cheikh Mouhamadou Habib Fall</a> · {big(k.flights)} de vols analysés
        </p>
      </section>

      {/* 1. L'heure */}
      <section className="chapter prose">
        <p className="kicker">1 · L'heure du départ</p>
        <h2>Le premier vol de la journée est presque toujours le plus sûr</h2>
        <p>
          À <strong>{hour(f.bestH.hour)}</strong>, seuls {pct(f.bestH.delayed)} des vols arrivent en retard. À{" "}
          <strong>{hour(f.worstH.hour)}</strong>, c'est <span className="hl">{pct(f.worstH.delayed)}</span>. Les
          retards ne disparaissent pas au cours de la journée : ils s'additionnent.
        </p>
      </section>
      <Figure
        title="Part des vols en retard selon l'heure de départ prévue"
        sub="Heure locale de l'aéroport de départ"
        caption={SOURCE}
      >
        <HatchedBars
          data={d.hourly.map((h) => ({
            key: h.hour,
            label: hour(h.hour),
            value: h.delayed,
            highlight: h.hour === f.worstH.hour,
            tip: (<><b>Départ à {hour(h.hour)}</b>{pct(h.delayed, 1)} en retard<br /><span className="muted">{num(h.flights)} vols</span></>),
          }))}
          labels={[f.bestH.hour, f.worstH.hour]}
        />
      </Figure>

      {/* 2. La cascade */}
      <section className="chapter prose">
        <p className="kicker">2 · L'effet domino</p>
        <h2>Un avion en retard emporte ses vols suivants avec lui</h2>
        <p>
          Un même avion enchaîne plusieurs vols dans la journée. En suivant chaque appareil par son immatriculation,
          on peut relier chaque vol au précédent.
        </p>
        <div className="bigstat">
          <div className="warm">
            <b>{pct(f.after.true)}</b>
            <span>des vols sont en retard quand le vol précédent du même avion l'était</span>
          </div>
          <div>
            <b>{pct(f.after.false)}</b>
            <span>quand le vol précédent était à l'heure</span>
          </div>
        </div>
        <p>
          C'est d'ailleurs la cause que les compagnies déclarent le plus souvent : un avion arrivé en retard explique{" "}
          <span className="hl">{pct(f.byCause.late_aircraft?.share ?? 0)}</span> des minutes de retard.
        </p>
      </section>
      <Figure
        title="Part des vols en retard selon le rang du vol dans la journée de l'avion"
        caption={`${SOURCE} Vols non annulés, avions identifiés par leur immatriculation.`}
      >
        <HatchedBars
          data={d.cascade.by_rank.map((r) => ({
            key: r.rank,
            label: r.rank === 1 ? "1er vol" : r.rank >= 6 ? "6e et +" : `${r.rank}e`,
            value: r.delayed,
            highlight: r.rank === d3.max(d.cascade.by_rank, (x) => x.rank),
            tip: (<><b>{r.rank === 1 ? "1er vol" : `${r.rank}e vol`} de l'avion</b>{pct(r.delayed, 1)} en retard<br /><span className="muted">{num(r.flights)} vols</span></>),
          }))}
          labels={d.cascade.by_rank.map((r) => r.rank)}
          height={260}
        />
      </Figure>

      {/* 3. Les causes */}
      <section className="chapter prose">
        <p className="kicker">3 · Les causes déclarées</p>
        <h2>La météo extrême ne pèse que {pct(f.byCause.weather?.share ?? 0)} des minutes de retard</h2>
        <p>
          Pour chaque vol en retard, la compagnie répartit les minutes entre cinq causes. La première,{" "}
          <strong>{f.topCause.label.toLowerCase()}</strong>, représente {pct(f.topCause.share)} du total.
        </p>
        <Figure caption="Minutes de retard des vols arrivés avec 15 minutes ou plus, selon la cause déclarée par la compagnie.">
          <CausesBar causes={d.causes} />
        </Figure>
        <p>
          Attention toutefois : la catégorie « météo » ne couvre que les conditions extrêmes. Une météo simplement
          mauvaise, qui ralentit le trafic, est rangée dans « trafic aérien ». Pour mesurer le vrai poids du ciel, il
          faut regarder la météo elle-même.
        </p>
      </section>

      {/* 4. La météo */}
      <section className="chapter prose">
        <p className="kicker">4 · La météo au départ</p>
        <h2>
          {clear
            ? `${under[worstW.condition] || worstW.condition}, ${pct(worstW.delayed)} des vols arrivent en retard, contre ${pct(clear.delayed)} par ciel dégagé`
            : "Le temps qu'il fait au décollage"}
        </h2>
        <p>
          Chaque vol a été relié à la météo de son aéroport de départ, à l'heure prévue du décollage. Plus le temps se
          dégrade, plus le risque monte, et {worstW.condition === "Neige" ? "la neige" : worstW.condition.toLowerCase()}{" "}
          fait aussi grimper les annulations à {pct(worstW.cancelled)}.
        </p>
        <p>
          Mais le mauvais temps ne tombe pas au hasard : il dépend de la saison, de l'heure et de la région. Le bouton
          « À conditions égales » montre l'effet de la météo une fois l'heure, le mois, l'aéroport et la compagnie
          neutralisés.
          {worstAdj && worstRawOR
            ? worstAdj.odds_ratio > worstRawOR
              ? ` Pour ${worstW.condition === "Neige" ? "la neige" : worstW.condition.toLowerCase()}, l'effet est même plus fort : la cote d'un retard est multipliée par ${num(worstAdj.odds_ratio, 1)}, contre ${num(worstRawOR, 1)} sans ajustement.`
              : ` Pour ${worstW.condition === "Neige" ? "la neige" : worstW.condition.toLowerCase()}, l'effet diminue un peu mais reste net : la cote d'un retard est multipliée par ${num(worstAdj.odds_ratio, 1)}.`
            : ""}
        </p>
      </section>
      <Figure
        title="Vols en retard selon la météo à l'aéroport de départ"
        sub="Barres : intervalle de confiance à 95 %. Pointillés : ciel dégagé."
        caption={`${SOURCE} Les ${k.weather_airports} aéroports de départ les plus fréquentés.`}
      >
        <WeatherDots weather={d.weather} adjusted={d.weather_adjusted || []} />
      </Figure>
      <section className="prose">
        <p>
          Le vent raconte la même chose. Plus les rafales sont fortes au décollage, plus les retards, et surtout les
          annulations, augmentent.
        </p>
      </section>
      <Figure title="Retards et annulations selon les rafales de vent au départ" caption={SOURCE}>
        <LineChart
          series={[
            { name: "En retard", color: "#2a78d6", values: d.gusts.map((g) => ({ x: g.gusts, y: g.delayed })) },
            { name: "Annulés", color: "#eb6834", values: d.gusts.map((g) => ({ x: g.gusts, y: g.cancelled })) },
          ]}
          xLabel={(v) => (v >= 80 ? "80+" : `${v}`)}
          tipTitle={(v) => (v >= 80 ? "Rafales de 80 km/h et plus" : `Rafales de ${v} à ${v + 10} km/h`)}
          height={280}
        />
        <p className="caption" style={{ marginTop: 0 }}>Rafales en km/h</p>
      </Figure>

      {/* 5. La saison */}
      <section className="chapter prose">
        <p className="kicker">5 · La saison</p>
        <h2>
          {f.worstM ? `${MONTHS_LONG[f.worstM.month - 1][0].toUpperCase()}${MONTHS_LONG[f.worstM.month - 1].slice(1)} est le mois le plus difficile` : "Les retards au fil de l'année"}
        </h2>
        <p>
          Sur les deux années, {f.worstM && MONTHS_LONG[f.worstM.month - 1]} compte {pct(f.worstM?.value ?? 0)} de vols en
          retard, contre {pct(f.bestM?.value ?? 0)} en {f.bestM && MONTHS_LONG[f.bestM.month - 1]}, le mois le plus calme.
        </p>
        {Math.min(...shutdownGap) > 0.03 && (
          <p>
            Un écart saute aux yeux : en octobre et novembre 2025, les retards montent à {pct(m10(2025, 10))} et{" "}
            {pct(m10(2025, 11))}, contre {pct(m10(2024, 10))} et {pct(m10(2024, 11))} un an plus tôt. Ces deux mois
            coïncident avec le <strong>shutdown du gouvernement fédéral</strong>, du 1er octobre au 12 novembre 2025 : les
            contrôleurs aériens ont travaillé sans salaire et l'administration a imposé des réductions de vols. Les
            données montrent la coïncidence, pas à elles seules la cause.
          </p>
        )}
      </section>
      <Figure title="Part des vols en retard par mois" caption={SOURCE}>
        <LineChart
          series={d3.groups(d.monthly, (m) => m.year).map(([year, v], i) => ({
            name: String(year),
            color: ["#1a1a1a", "#eb6834", "#2a78d6"][i],
            values: v.map((m) => ({ x: m.month, y: m.delayed })),
          }))}
          xLabel={(v) => MONTHS[v - 1]}
          tipTitle={(v) => MONTHS_LONG[v - 1]}
        />
      </Figure>

      {/* 6. Les aéroports */}
      <section className="chapter prose">
        <p className="kicker">6 · Les aéroports</p>
        <h2>D'un aéroport à l'autre, le risque varie fortement</h2>
        <p>
          Parmi les grands aéroports, <strong>{f.worstAirport.city} ({f.worstAirport.code})</strong> a le plus de départs
          en retard ({pct(f.worstAirport.delayed)}), <strong>{f.bestAirport.city} ({f.bestAirport.code})</strong> le
          moins ({pct(f.bestAirport.delayed)}).
        </p>
      </section>
      <Figure wide title="Part des départs en retard, par aéroport" sub="Aéroports d'au moins 20 000 départs. Survoler ou toucher pour le détail." caption={SOURCE}>
        <AirportMap airports={d.airports} mean={mean} />
      </Figure>

      {/* 7. Le modèle */}
      {f.aucWeather != null && (
        <>
          <section className="chapter prose">
            <p className="kicker">7 · Peut-on le prévoir ?</p>
            <h2>Un modèle entraîné sur 2024, testé sur 2025</h2>
            <p>
              Avec seulement ce que l'on sait avant le départ (date, heure, compagnie, trajet, météo prévue), un modèle
              de machine learning entraîné sur 2024 place un vol qui sera en retard au-dessus d'un vol à l'heure dans{" "}
              <strong>{pct(f.aucWeather)}</strong> des cas en 2025, contre 50 % au hasard. Ajouter la météo fait passer
              ce score (l'AUC) de {num(f.aucNoWeather, 2)} à {num(f.aucWeather, 2)}.
            </p>
            <p>
              C'est un vrai signal, mais modeste : l'essentiel d'un retard se joue le jour même, avec un avion qui
              arrive en retard ou un ciel saturé, des informations qu'aucun modèle ne connaît au moment de réserver.
            </p>
          </section>
          <Figure title="Qualité de la prédiction (AUC) sur l'année 2025" sub="0,5 = hasard, 1 = prédiction parfaite" caption="Gradient boosting évalué sur des vols que le modèle n'a jamais vus.">
            <ModelBars scores={d.model.scores} />
          </Figure>
        </>
      )}

      {/* À retenir */}
      <section className="chapter prose">
        <p className="kicker">En résumé</p>
        <h2>Ce qu'il faut retenir</h2>
        <ul className="takeaways">
          <li>
            <strong>Partir tôt.</strong> Un vol de {hour(f.bestH.hour)} a {pct(f.bestH.delayed)} de risque d'être en retard,
            un vol de {hour(f.worstH.hour)} {pct(f.worstH.delayed)}.
          </li>
          <li>
            <strong>Le retard se propage.</strong> Quand l'avion arrive en retard de son vol précédent, le risque passe de{" "}
            {pct(f.after.false)} à {pct(f.after.true)}.
          </li>
          <li>
            <strong>La météo pèse peu en volume, mais lourd quand elle frappe.</strong> La météo extrême ne représente que{" "}
            {pct(f.byCause.weather?.share ?? 0)} des minutes de retard déclarées ; pourtant, {(under[worstW.condition] || worstW.condition).toLowerCase()},{" "}
            {pct(worstW.delayed)} des vols arrivent en retard.
          </li>
        </ul>
      </section>

      <Method k={k} quality={d.quality} />
    </main>
  );
}

function Method({ k, quality }) {
  const passed = quality.filter((q) => q.passed).length;
  return (
    <section className="method" id="methode">
      <div className="prose">
        <h2>Méthode</h2>
        <p>
          Données : tous les vols intérieurs des compagnies qui déclarent leur ponctualité au ministère américain des
          Transports, du {new Date(k.start).toLocaleDateString("fr-FR")} au {new Date(k.end).toLocaleDateString("fr-FR")},
          soit {num(k.flights)} vols.
        </p>
        <h3>Définitions</h3>
        <ul>
          <li>Un vol est <strong>en retard</strong> s'il arrive avec 15 minutes ou plus de retard (définition officielle du BTS).</li>
          <li>La <strong>météo au départ</strong> est celle de l'aéroport, à l'heure locale prévue du décollage.</li>
        </ul>
        <h3>Sources</h3>
        <ul>
          <li><a href="https://www.transtats.bts.gov/DatabaseInfo.asp?QO_VQ=EFD">BTS, Reporting Carrier On-Time Performance</a> : un fichier par mois.</li>
          <li><a href="https://open-meteo.com/en/docs/historical-weather-api">Open-Meteo</a> : météo horaire des {k.weather_airports} aéroports les plus fréquentés.</li>
          <li><a href="https://ourairports.com/data/">OurAirports</a> : noms et coordonnées des aéroports.</li>
        </ul>
        <h3>Traitement</h3>
        <ul>
          <li>Pipeline Python, entrepôt DuckDB en schéma en étoile, jointure vol × météo à l'heure près.</li>
          <li>{passed} contrôles qualité sur {quality.length} validés à la dernière construction (doublons, cohérence des causes, jours manquants…).</li>
          <li>Effet de la météo « à conditions égales » : régression logistique contrôlant l'heure, le mois, le jour, l'aéroport et la compagnie.</li>
          <li>Modèle prédictif : gradient boosting entraîné sur 2024 et testé sur 2025.</li>
        </ul>
        <h3>Limites</h3>
        <ul>
          <li>La cause du retard est déclarée par la compagnie, pas mesurée.</li>
          <li>Seule la météo au départ est prise en compte ; elle provient d'une réanalyse (ERA5), pas des stations des aéroports. Son code météo ne signale ni les orages ni le brouillard.</li>
        </ul>
        <p style={{ marginTop: 22 }}>
          Code, requêtes SQL, notebooks et rapport Power BI : <a href={REPO}>github.com/habibfl/flight-delays</a>.
        </p>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div className="inner">
        <span><span className="brand">flight-delays</span> · Cheikh Mouhamadou Habib Fall</span>
        <span>
          <a href={REPO}>Code source</a> · <a href="https://github.com/habibfl">GitHub</a>
        </span>
        <span>Données publiques, usage non commercial.</span>
      </div>
    </footer>
  );
}

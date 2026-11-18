"""Lance tout le pipeline, ou seulement certaines étapes.

    python pipeline/run_pipeline.py                 # tout
    python pipeline/run_pipeline.py warehouse export

Chaque étape saute ce qui est déjà fait : on peut relancer sans risque
après une coupure réseau.
"""
import sys
import time

import build_warehouse
import export_powerbi
import extract_airports
import extract_flights
import extract_weather
from utils import log

STEPS = {
    "flights": extract_flights.run,
    "airports": extract_airports.run,
    "weather": extract_weather.run,
    "warehouse": build_warehouse.run,
    "export": export_powerbi.run,
}


def main(names):
    for name in names or STEPS:
        if name not in STEPS:
            raise SystemExit(f"Étape inconnue : {name}. Choix : {', '.join(STEPS)}")
        t0 = time.time()
        log.info("=== %s ===", name)
        STEPS[name]()
        log.info("%s terminé en %.0f s", name, time.time() - t0)


if __name__ == "__main__":
    main(sys.argv[1:])

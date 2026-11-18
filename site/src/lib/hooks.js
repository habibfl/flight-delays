import { useEffect, useRef, useState } from "react";

// Largeur réelle d'un conteneur, mise à jour au redimensionnement.
export function useWidth(initial = 640) {
  const ref = useRef(null);
  const [width, setWidth] = useState(initial);
  useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([entry]) => setWidth(Math.round(entry.contentRect.width)));
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);
  return [ref, width];
}

// Vrai une fois que l'élément est entré à l'écran (pour animer à l'arrivée).
export function useInView(threshold = 0.35) {
  const ref = useRef(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    if (!ref.current || seen) return;
    const io = new IntersectionObserver(([e]) => e.isIntersecting && setSeen(true), { threshold });
    io.observe(ref.current);
    return () => io.disconnect();
  }, [seen, threshold]);
  return [ref, seen];
}

// Données du récit, exportées par analysis/export_site.py.
export function useStory() {
  const [state, setState] = useState({ data: null, error: null });
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/story.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data) => setState({ data, error: null }))
      .catch((error) => setState({ data: null, error }));
  }, []);
  return state;
}

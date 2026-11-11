import { useEffect, useState } from "react";
import Picks from "./Picks.jsx";
import Results from "./Results.jsx";

const TABS = [
  { key: "picks", label: "Today" },
  { key: "results", label: "Results" },
];

const tabFromHash = () => (window.location.hash.replace("#", "") === "results" ? "results" : "picks");

function useJson(url) {
  const [state, setState] = useState({ status: "loading", data: null });
  useEffect(() => {
    let live = true;
    fetch(`${url}?v=${Date.now()}`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((data) => live && setState({ status: "ready", data }))
      .catch(() => live && setState({ status: "error", data: null }));
    return () => { live = false; };
  }, [url]);
  return state;
}

export default function App() {
  const [tab, setTab] = useState(tabFromHash);
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || "light");
  const picks = useJson("/latest.json");
  const results = useJson("/results/results.json");

  useEffect(() => {
    const onHash = () => setTab(tabFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = (key) => {
    setTab(key);
    window.history.replaceState(null, "", key === "picks" ? window.location.pathname : `#${key}`);
    window.scrollTo(0, 0);
  };

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("ce-theme", next); } catch { /* private mode */ }
    setTheme(next);
  };

  return (
    <>
      <header className="topbar">
        <div className="wrap topbar-in">
          <div className="brand"><span className="brand-mark" aria-hidden="true" />Courtside Edge</div>
          <nav className="tabs" role="tablist" aria-label="Pages">
            {TABS.map((t) => (
              <button key={t.key} role="tab" className="tab" aria-selected={tab === t.key} onClick={() => go(t.key)}>
                {t.label}
              </button>
            ))}
          </nav>
          <button className="icon-btn" onClick={toggleTheme} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`} title="Toggle light / dark">
            <span aria-hidden="true">{theme === "dark" ? "☀" : "☾"}</span>
          </button>
        </div>
      </header>

      <main className="wrap">
        {tab === "picks" && <Picks state={picks} results={results.data} onNavigate={go} />}
        {tab === "results" && <Results state={results} />}
      </main>
    </>
  );
}

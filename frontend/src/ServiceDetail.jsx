import React, { useState, useEffect, useRef } from "react";
import { CopyIcon } from "./components/icons";

const TABS = ["sam", "proxy", "tunnel", "build"];

export default function ServiceDetail({ service, onBack, onStart, onStop, onRestart, onRestartSam, onBuild, onClean, onKillPorts }) {
  const { name, sam_port, proxy_port, status, tunnel_url } = service;
  const [activeTab, setActiveTab] = useState("sam");
  const [logs, setLogs] = useState({ sam: [], proxy: [], tunnel: [], build: [] });
  const logRef = useRef(null);
  const disabled = status === "building";

  useEffect(() => {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/logs/${name}`);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      setLogs((prev) => {
        const key = msg.process in prev ? msg.process : "sam";
        return { ...prev, [key]: [...prev[key].slice(-499), msg.line] };
      });
    };
    return () => ws.close();
  }, [name]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs, activeTab]);

  return (
    <div className="app">
      <button className="detail-back" onClick={onBack}>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M8 1L3 6l5 5" />
        </svg>
        All services
      </button>

      <div className="detail-header">
        <div className="detail-title">
          <span className="app-title-mark" style={{ fontSize: 18 }}>⬡</span>
          <span className="detail-name">{name}</span>
          <span className="card-ports" style={{ fontSize: 12, alignSelf: "flex-end", marginBottom: 2 }}>
            :{sam_port} → :{proxy_port}
          </span>
        </div>
        <span className={`status-badge ${status}`} style={{ fontSize: 11, padding: "3px 9px" }}>
          {status === "building" ? "building…" : status}
        </span>
      </div>

      {tunnel_url && (
        <div style={{ marginTop: 6, marginBottom: 16 }}>
          <a href={tunnel_url} target="_blank" rel="noreferrer" className="tunnel-link" style={{ fontSize: 12 }}>
            {tunnel_url}
          </a>
          <button className="btn-copy" onClick={() => navigator.clipboard.writeText(tunnel_url)} title="Copy tunnel URL" aria-label="Copy tunnel URL">
            <CopyIcon />
          </button>
        </div>
      )}

      <div className="detail-actions">
        <button className="btn btn-start" disabled={disabled} onClick={onStart}>Start</button>
        <button className="btn" disabled={disabled} onClick={onStop}>Stop</button>
        <button className="btn" disabled={disabled} onClick={onRestart}>Restart</button>
        <button className="btn" disabled={disabled} onClick={onRestartSam}>Restart SAM only</button>
        <button className="btn" disabled={disabled} onClick={onBuild}>
          {status === "building" ? "Building…" : "Build"}
        </button>
        <button className="btn btn-danger" disabled={disabled} onClick={onClean}>Clean</button>
        {/* always enabled — recovery action, must work even when service is broken */}
        <button className="btn btn-danger" onClick={onKillPorts}>Kill Ports</button>
      </div>

      <div className="detail-log-panel">
        <div className="tab-bar">
          {TABS.map((tab) => (
            <button
              key={tab}
              className={`tab-btn${activeTab === tab ? " active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
        <div ref={logRef} className="detail-log-pane">
          {logs[activeTab].length === 0
            ? <span className="log-empty">— no output —</span>
            : logs[activeTab].map((line, i) => <div key={i} className="log-line">{line}</div>)
          }
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect, useRef } from "react";
import { CopyIcon, ExpandIcon } from "./components/icons";

const TABS = ["sam", "proxy", "tunnel", "build"];

export default function ServiceCard({ service, onStart, onStop, onRestart, onRestartSam, onBuild, onClean, onKillPorts, onFocus }) {
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
        const tab = msg.process in prev ? msg.process : "sam";
        return { ...prev, [tab]: [...prev[tab].slice(-499), msg.line] };
      });
    };
    return () => ws.close();
  }, [name]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs, activeTab]);

  return (
    <div className="card">
      <div className={`card-strip ${status}`} />
      <div className="card-body">

        <div className="card-header">
          <div className="card-name-row">
            <span className="card-name">{name}</span>
            <span className="card-ports">:{sam_port} / :{proxy_port}</span>
          </div>
          <div className="card-header-right">
            <button className="btn-expand" onClick={onFocus} title="Open detail view" aria-label="Open detail view">
              <ExpandIcon />
            </button>
            <span className={`status-badge ${status}`}>
              {status === "building" ? "building…" : status}
            </span>
          </div>
        </div>

        {tunnel_url && (
          <>
            <div className="card-divider" />
            <div className="tunnel-row">
              <a href={tunnel_url} target="_blank" rel="noreferrer" className="tunnel-link">
                {tunnel_url}
              </a>
              <button className="btn-copy" onClick={() => navigator.clipboard.writeText(tunnel_url)} title="Copy tunnel URL" aria-label="Copy tunnel URL">
                <CopyIcon />
              </button>
            </div>
          </>
        )}

        <div className="card-divider" />
        <div className="card-actions">
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

        <div ref={logRef} className="log-pane">
          {logs[activeTab].length === 0
            ? <span className="log-empty">— no output —</span>
            : logs[activeTab].map((line, i) => <div key={i} className="log-line">{line}</div>)
          }
        </div>

      </div>
    </div>
  );
}

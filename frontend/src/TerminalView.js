import React, { useState, useEffect, useRef } from 'react';
import './TerminalView.css';

function TerminalView() {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const terminalBodyRef = useRef(null);

  useEffect(() => {
    // Create WebSocket connection.
    const socket = new WebSocket('ws://127.0.0.1:8000/ws/logs');

    socket.onopen = () => {
      setIsConnected(true);
      setLogs(prevLogs => [...prevLogs, '[STATUS] Connected to backend logs.']);
    };

    socket.onmessage = (event) => {
      setLogs(prevLogs => [...prevLogs, event.data]);
    };

    socket.onclose = () => {
      setIsConnected(false);
      setLogs(prevLogs => [...prevLogs, '[STATUS] Disconnected from backend logs.']);
    };

    socket.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setLogs(prevLogs => [...prevLogs, '[ERROR] WebSocket connection failed.']);
    };

    // Cleanup the connection when the component unmounts
    return () => {
      socket.close();
    };
  }, []);

  // Auto-scroll to the bottom when new logs arrive
  useEffect(() => {
    if (terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="terminal-view">
      <div className="terminal-header">
        <div className="terminal-title">Backend Logs</div>
        <div className={`connection-status ${isConnected ? 'connected' : ''}`}>
          {isConnected ? '● LIVE' : '● DISCONNECTED'}
        </div>
      </div>
      <div className="terminal-body" ref={terminalBodyRef}>
        {logs.map((log, index) => (
          <div key={index} className="log-line">
            <span className="log-prefix">&gt;</span>
            <span className="log-content">{log}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TerminalView;

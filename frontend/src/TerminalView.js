import React, { useState, useEffect, useRef } from 'react';
import './TerminalView.css';

const PADDING = 20;

function TerminalView() {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [position, setPosition] = useState({ 
    x: window.innerWidth - 500 - PADDING, 
    y: window.innerHeight - 300 - PADDING 
  });
  const [isDragging, setIsDragging] = useState(false);
  
  const terminalRef = useRef(null);
  const dragOffset = useRef({ x: 0, y: 0 });
  const terminalBodyRef = useRef(null);

  // WebSocket Logic
  useEffect(() => {
    const socket = new WebSocket('ws://127.0.0.1:8000/ws/logs');
    socket.onopen = () => {
      setIsConnected(true);
      setLogs(prev => [...prev, '[STATUS] Connected to backend logs.']);
    };
    socket.onmessage = (event) => setLogs(prev => [...prev, event.data]);
    socket.onclose = () => {
      setIsConnected(false);
      setLogs(prev => [...prev, '[STATUS] Disconnected from backend logs.']);
    };
    return () => socket.close();
  }, []);

  // Auto-scroll Logic
  useEffect(() => {
    if (terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, [logs]);

  // Drag-and-snap Logic
  const onMouseDown = (e) => {
    setIsDragging(true);
    const { left, top } = terminalRef.current.getBoundingClientRect();
    dragOffset.current = { x: e.clientX - left, y: e.clientY - top };
  };

  const onMouseUp = () => {
    if (!isDragging) return;
    setIsDragging(false);
    const { clientWidth, clientHeight } = terminalRef.current;
    const { innerWidth, innerHeight } = window;
    let newPos = { ...position };
    if (position.x + clientWidth / 2 < innerWidth / 2) newPos.x = PADDING;
    else newPos.x = innerWidth - clientWidth - PADDING;
    if (position.y + clientHeight / 2 < innerHeight / 2) newPos.y = PADDING;
    else newPos.y = innerHeight - clientHeight - PADDING;
    setPosition(newPos);
  };

  const onMouseMove = (e) => {
    if (!isDragging) return;
    setPosition({ x: e.clientX - dragOffset.current.x, y: e.clientY - dragOffset.current.y });
  };

  useEffect(() => {
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [isDragging, position]);

  // --- NEW: Helper function to determine CSS class for a log line ---
  const getLogClass = (log) => {
    if (log.startsWith('[INFO]')) return 'log-info';
    if (log.startsWith('[ERROR]')) return 'log-error';
    if (log.startsWith('[STATUS]')) return 'log-status';
    return 'log-default';
  };

  return (
    <div
      ref={terminalRef}
      className={`terminal-view ${isDragging ? 'dragging' : ''}`}
      style={{ top: `${position.y}px`, left: `${position.x}px` }}
    >
      <div className="terminal-header" onMouseDown={onMouseDown}>
        <div className="terminal-title">Backend Logs</div>
        <div className={`connection-status ${isConnected ? 'connected' : ''}`}>
          {isConnected ? '● LIVE' : '● DISCONNECTED'}
        </div>
      </div>
      <div className="terminal-body" ref={terminalBodyRef}>
        {logs.map((log, index) => (
          // --- UPDATED: Apply the dynamic class here ---
          <div key={index} className={`log-line ${getLogClass(log)}`}>
            <span className="log-prefix">&gt;</span>
            <span className="log-content">{log}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TerminalView;

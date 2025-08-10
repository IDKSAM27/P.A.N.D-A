import React, { useState, useEffect, useRef } from 'react';
import './TerminalView.css';

const PADDING = 20;
const MIN_WIDTH = 350;
const MIN_HEIGHT = 200;

function TerminalView() {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  
  // --- STATE FOR SIZE & POSITION ---
  const [size, setSize] = useState({ width: 500, height: 300 });
  const [position, setPosition] = useState({ 
    x: window.innerWidth - 500 - PADDING, 
    y: window.innerHeight - 300 - PADDING 
  });
  
  // --- STATE FOR MODES ---
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  
  const terminalRef = useRef(null);
  const dragStartInfo = useRef(null); // Used for both dragging and resizing

  // WebSocket Logic (no changes)
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

  // Auto-scroll Logic (no changes)
  const terminalBodyRef = useRef(null);
  useEffect(() => {
    if (terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, [logs]);

  // --- DRAG & RESIZE EVENT HANDLERS ---
  const onDragMouseDown = (e) => {
    setIsDragging(true);
    const { left, top } = terminalRef.current.getBoundingClientRect();
    dragStartInfo.current = { x: e.clientX - left, y: e.clientY - top };
  };

  const onResizeMouseDown = (e) => {
    e.stopPropagation(); // Prevent drag from starting on the handle
    setIsResizing(true);
    dragStartInfo.current = {
      startX: e.clientX,
      startY: e.clientY,
      startWidth: size.width,
      startHeight: size.height,
    };
  };

  const onMouseUp = () => {
    if (isDragging) {
      // Snap logic updated to use size from state
      const { innerWidth, innerHeight } = window;
      let newPos = { ...position };
      if (position.x + size.width / 2 < innerWidth / 2) newPos.x = PADDING;
      else newPos.x = innerWidth - size.width - PADDING;
      if (position.y + size.height / 2 < innerHeight / 2) newPos.y = PADDING;
      else newPos.y = innerHeight - size.height - PADDING;
      setPosition(newPos);
    }
    setIsDragging(false);
    setIsResizing(false);
  };

  const onMouseMove = (e) => {
    if (isDragging) {
      setPosition({ x: e.clientX - dragStartInfo.current.x, y: e.clientY - dragStartInfo.current.y });
    }
    if (isResizing) {
      const deltaX = e.clientX - dragStartInfo.current.startX;
      const deltaY = e.clientY - dragStartInfo.current.startY;
      const newWidth = Math.max(MIN_WIDTH, dragStartInfo.current.startWidth + deltaX);
      const newHeight = Math.max(MIN_HEIGHT, dragStartInfo.current.startHeight + deltaY);
      setSize({ width: newWidth, height: newHeight });
    }
  };

  useEffect(() => {
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [isDragging, isResizing, position, size]); // Depend on all relevant states

  const getLogClass = (log) => {
    const upperCaseLog = log.toUpperCase();
    if (upperCaseLog.startsWith('[STATUS]')) return 'log-status';
    if (upperCaseLog.includes('ERROR') || upperCaseLog.includes('CRITICAL')) return 'log-error';
    if (upperCaseLog.includes('WARNING')) return 'log-warning';
    if (upperCaseLog.includes('INFO')) return 'log-info';
    return 'log-default';
  };

  return (
    <div
      ref={terminalRef}
      className={`terminal-view ${isDragging || isResizing ? 'active' : ''}`}
      style={{
        top: `${position.y}px`, left: `${position.x}px`,
        width: `${size.width}px`, height: `${size.height}px`,
      }}
    >
      <div className="terminal-header" onMouseDown={onDragMouseDown}>
        <div className="terminal-title">Backend Logs</div>
        <div className={`connection-status ${isConnected ? 'connected' : ''}`}>
          {isConnected ? '● LIVE' : '● DISCONNECTED'}
        </div>
      </div>
      <div className="terminal-body" ref={terminalBodyRef}>
        {logs.map((log, index) => (
          <div key={index} className={`log-line ${getLogClass(log)}`}>
            <span className="log-prefix">&gt;</span>
            <span className="log-content">{log}</span>
          </div>
        ))}
      </div>
      {/* --- NEW: Resize Handle --- */}
      <div className="resize-handle" onMouseDown={onResizeMouseDown}></div>
    </div>
  );
}

export default TerminalView;

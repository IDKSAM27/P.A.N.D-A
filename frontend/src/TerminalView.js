import React, { useState, useEffect, useRef } from 'react';
import './TerminalView.css';

const PADDING = 20; // The space from the edge of the screen

function TerminalView() {
  const [logs, setLogs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  
  // --- State for Dragging ---
  const [isDragging, setIsDragging] = useState(false);
  // Default to bottom-right corner
  const [position, setPosition] = useState({ 
    x: window.innerWidth - 500 - PADDING, 
    y: window.innerHeight - 300 - PADDING 
  });
  
  const terminalRef = useRef(null);
  const dragOffset = useRef({ x: 0, y: 0 });

  // --- WebSocket Logic (remains the same) ---
  useEffect(() => {
    const socket = new WebSocket('ws://127.0.0.1:8000/ws/logs');
    socket.onopen = () => {
      setIsConnected(true);
      setLogs(prev => [...prev, '[STATUS] Connected to backend logs.']);
    };
    socket.onmessage = (event) => setLogs(prev => [...prev, event.data]);
    socket.onclose = () => {
      setIsConnected(false);
      setLogs(prev => [...prev, '[STATUS] Disconnected.']);
    };
    return () => socket.close();
  }, []);

  // --- Auto-scroll Logic (remains the same) ---
  const terminalBodyRef = useRef(null);
  useEffect(() => {
    if (terminalBodyRef.current) {
      terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
    }
  }, [logs]);


  // --- Event Handlers for Dragging ---
  const onMouseDown = (e) => {
    setIsDragging(true);
    // Calculate the offset from the mouse pointer to the element's top-left corner
    const { left, top } = terminalRef.current.getBoundingClientRect();
    dragOffset.current = { x: e.clientX - left, y: e.clientY - top };
  };

  const onMouseUp = () => {
    if (!isDragging) return;
    setIsDragging(false);

    // --- The "Snap" Logic ---
    const { clientWidth, clientHeight } = terminalRef.current;
    const { innerWidth, innerHeight } = window;
    let newPos = { ...position };

    // Snap horizontally
    if (position.x + clientWidth / 2 < innerWidth / 2) {
      newPos.x = PADDING; // Snap left
    } else {
      newPos.x = innerWidth - clientWidth - PADDING; // Snap right
    }

    // Snap vertically
    if (position.y + clientHeight / 2 < innerHeight / 2) {
      newPos.y = PADDING; // Snap top
    } else {
      newPos.y = innerHeight - clientHeight - PADDING; // Snap bottom
    }
    
    setPosition(newPos);
  };

  const onMouseMove = (e) => {
    if (!isDragging) return;
    // Calculate new position based on mouse movement and initial offset
    const newX = e.clientX - dragOffset.current.x;
    const newY = e.clientY - dragOffset.current.y;
    setPosition({ x: newX, y: newY });
  };

  // --- Effect to add and clean up global event listeners ---
  useEffect(() => {
    // We listen on the window so the drag continues even if the mouse leaves the terminal
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    // Cleanup function to prevent memory leaks
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [isDragging, position]); // Re-attach listeners if state changes


  return (
    <div
      ref={terminalRef}
      className={`terminal-view ${isDragging ? 'dragging' : ''}`}
      style={{
        top: `${position.y}px`,
        left: `${position.x}px`,
      }}
    >
      <div className="terminal-header" onMouseDown={onMouseDown}>
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

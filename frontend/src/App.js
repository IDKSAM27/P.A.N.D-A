import React, { useState } from 'react';
import './App.css';
import CommandInput from './CommandInput';
import TerminalView from './TerminalView';

function App() {
  // The below are called states (for the people who don't understand dog shit)
  const [sessionInfo, setSessionInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [showTerminal, setShowTerminal] = useState(false);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setSessionInfo(null);
    setError('');
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://127.0.0.1:8000/upload_csv', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to upload file.');
      setSessionInfo(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      {/* --- New Terminal Toggle Button --- */}
      <button className="terminal-toggle-btn" onClick={() => setShowTerminal(!showTerminal)}>
        {showTerminal ? 'Hide' : 'Show'} Logs
      </button>

      <header className="App-header">
        <h1>Voice Data Assistant</h1>
        <p>Your personal AI for data analysis.</p>

        <div className="container upload-container">
          <h2>Step 1: Upload Data</h2>
          <input type="file" accept=".csv" onChange={handleFileChange} />
          <button onClick={handleUpload} disabled={isLoading || !selectedFile}>
            {isLoading ? 'Uploading...' : 'Upload File'}
          </button>
        </div>

        {error && <p className="error-message">{error}</p>}
        
        {sessionInfo && (
          <CommandInput 
            sessionId={sessionInfo.session_id} 
            columns={sessionInfo.columns} 
          />
        )}
      </header>

      {/* --- Conditionally render the Terminal --- */}
      {showTerminal && <TerminalView />}

    </div>
  );
}

export default App;

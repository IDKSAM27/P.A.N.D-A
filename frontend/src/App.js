import React, { useState } from 'react';
import './App.css';
import CommandInput from './CommandInput';
import TerminalView from './TerminalView';
import DataPreview from './DataPreview'; // <-- Import new component

function App() {
  const [sessionInfo, setSessionInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(''); // <-- Can be 'upload' or 'sample'
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [showTerminal, setShowTerminal] = useState(false);
  const [showPreview, setShowPreview] = useState(false); // <-- State for preview modal

  const resetState = () => {
    setSessionInfo(null);
    setError('');
    setShowPreview(false);
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      resetState();
    }
  };

  const processApiResponse = (data) => {
    if (!data.session_id) throw new Error("Invalid response from server.");
    setSessionInfo(data);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsLoading('upload');
    resetState();
    const formData = new FormData();
    formData.append('file', selectedFile);
    try {
      const response = await fetch('http://127.0.0.1:8000/upload_csv', { method: 'POST', body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Upload failed.');
      processApiResponse(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading('');
    }
  };
  
  const handleLoadSample = async () => {
    setIsLoading('sample');
    resetState();
    setSelectedFile(null); // Clear file input
    try {
      const response = await fetch('http://127.0.0.1:8000/sample_data', { method: 'POST' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to load sample.');
      processApiResponse(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading('');
    }
  };

  return (
    <div className="App">
      <button className="terminal-toggle-btn" onClick={() => setShowTerminal(!showTerminal)}>
        {showTerminal ? 'Hide' : 'Show'} Logs
      </button>

      <header className="App-header">
        <h1>Voice Data Assistant</h1>
        <p>Your personal AI for data analysis.</p>

        {!sessionInfo && (
          <div className="container upload-container">
            <h2>Step 1: Provide Data</h2>
            <div className="file-input-wrapper">
              <label htmlFor="csv-upload" className="file-input-label">Choose Your File</label>
              <input id="csv-upload" type="file" accept=".csv" onChange={handleFileChange} className="file-input-hidden" />
              <button className="button-secondary" onClick={handleLoadSample} disabled={!!isLoading}>
                {isLoading === 'sample' ? 'Loading...' : 'Use Sample Data'}
              </button>
            </div>
            {selectedFile && <span className="file-name">Selected: {selectedFile.name}</span>}
            <button onClick={handleUpload} disabled={!!isLoading || !selectedFile}>
              {isLoading === 'upload' ? 'Uploading...' : 'Upload & Start'}
            </button>
          </div>
        )}
        
        {error && <p className="error-message">{error}</p>}
        
        {sessionInfo && (
          <>
            <div className="container-header">
              <h3>Data Loaded</h3>
              <button className="button-tertiary" onClick={() => setShowPreview(true)}>Preview Data</button>
            </div>
            <CommandInput sessionId={sessionInfo.session_id} columns={sessionInfo.columns} />
          </>
        )}
      </header>

      {showTerminal && <TerminalView />}
      {showPreview && <DataPreview data={sessionInfo.preview} onClose={() => setShowPreview(false)} />}
    </div>
  );
}

export default App;

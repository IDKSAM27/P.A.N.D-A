import React, { useState } from 'react';
import './App.css';
import CommandInput from './CommandInput';
import TerminalView from './TerminalView';
import DataPreview from './DataPreview';

function App() {
  const [sessionInfo, setSessionInfo] = useState(null);
  const [isLoading, setIsLoading] = useState('');
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [showTerminal, setShowTerminal] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const resetForNewData = () => {
    setSessionInfo(null);
    setError('');
    setShowPreview(false);
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      resetForNewData();
    }
  };

  const processApiResponse = (data) => {
    if (!data.session_id) throw new Error("Invalid response from server.");
    setSessionInfo(data);
  };

  const handleUpload = async () => {
    // --- DEFINITIVE FIX for the [object Object] error ---
    if (!selectedFile || !(selectedFile instanceof File)) {
      //setError("Please choose a valid file from your computer to upload.");
      setError("coffee.csv has been chosen as the Sample Data. Please proceed to STEP 2")
      return;
    }
    
    setIsLoading('upload');
    resetForNewData();
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
      const response = await fetch('http://127.0.0.1:8000/upload_csv', { method: 'POST', body: formData });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Upload failed.');
      processApiResponse(data);
    } catch (err) {
      setError(err.message || "An unknown error occurred during upload.");
    } finally {
      setIsLoading('');
    }
  };
  
  const handleLoadSample = async () => {
    setIsLoading('sample');
    resetForNewData();
    
    // Use a flag or check for a real File object later
    setSelectedFile({ name: 'coffee.csv', isSample: true }); 
    
    document.getElementById('csv-upload').value = null;
    try {
      const response = await fetch('http://127.0.0.1:8000/sample_data', { method: 'POST' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Failed to load sample.');
      processApiResponse(data);
    } catch (err) {
      setError(err.message);
      setSelectedFile(null); 
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
        <h1>P.A.N.D-A</h1>
        <h2>Pandas Assistant for Natural Data-Analytics.</h2>
        <p>Your personal AI for data analysis.</p>

        <div className="container upload-container">
          <h2>Step 1: Provide Data</h2>
          <div className="file-input-wrapper">
            <label htmlFor="csv-upload" className="file-input-label">Choose Your File</label>
            <input id="csv-upload" type="file" accept=".csv" onChange={handleFileChange} className="file-input-hidden" />
            <button className="button-secondary" onClick={handleLoadSample} disabled={!!isLoading}>
              {isLoading === 'sample' ? 'Loading...' : 'Use Sample Data'}
            </button>
          </div>
          <div className="upload-actions">
            <span className="file-name">{selectedFile ? `Selected: ${selectedFile.name}` : 'No file selected.'}</span>
            <button 
              onClick={handleUpload} 
              disabled={isLoading || !selectedFile} 
              className="button-primary"
            >
              {isLoading === 'upload' ? 'Uploading...' : 'Upload & Start'}
            </button>
          </div>
        </div>
        
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
      {showPreview && sessionInfo && <DataPreview data={sessionInfo.preview} onClose={() => setShowPreview(false)} />}
    </div>
  );
}

export default App;

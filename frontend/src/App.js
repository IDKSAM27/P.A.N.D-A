// frontend/src/App.js
import React, { useState } from 'react';
import './App.css';
import CommandInput from './CommandInput'; // <-- Import the new component

function App() {
  const [sessionInfo, setSessionInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setSessionInfo(null);
    setError('');
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a CSV file first.');
      return;
    }

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

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to upload file.');
      }

      setSessionInfo(data);
      console.log('Upload successful:', data);

    } catch (err) {
      setError(err.message);
      console.error('Upload error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Voice Data Assistant</h1>
        
        <div className="upload-container">
          <h2>Step 1: Upload Data</h2>
          <input type="file" accept=".csv" onChange={handleFileChange} />
          <button onClick={handleUpload} disabled={isLoading}>
            {isLoading ? 'Uploading...' : 'Upload File'}
          </button>
        </div>

        {error && <p className="error-message">{error}</p>}
        
        {/* --- UPDATE: Conditionally render the CommandInput component --- */}
        {sessionInfo && (
          <CommandInput sessionId={sessionInfo.session_id} />
        )}

      </header>
    </div>
  );
}

export default App;

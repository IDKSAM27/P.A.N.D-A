import React, { useState } from 'react';

// A helper component to render the results table
const ResultTable = ({ data }) => {
  if (!data || data.length === 0) {
    return null;
  }
  const headers = Object.keys(data[0]);

  return (
    <table className="result-table">
      <thead>
        <tr>
          {headers.map(header => <th key={header}>{header}</th>)}
        </tr>
      </thead>
      <tbody>
        {data.map((row, index) => (
          <tr key={index}>
            {headers.map(header => <td key={header}>{String(row[header])}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

function CommandInput({ sessionId, columns }) {
  const [command, setCommand] = useState('');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (!command) return;
    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, command: command }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Analysis failed.');
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleAnalyze();
    }
  };

  return (
    <div className="container analysis-container">
      <h2>Step 2: Ask a Question</h2>
      
      <div className="columns-display">
        <strong>Available columns:</strong> <span>{columns.join(', ')}</span>
      </div>

      <div className="command-form">
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="e.g., total units sold by day"
          className="command-input" // <-- FIX: Added correct class
        />
        <button 
          onClick={handleAnalyze} 
          disabled={isLoading || !command} 
          className="button-primary" // <-- FIX: Added correct class
        >
          {isLoading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}
      
      {result && (
        <div className="result-container">
          <p className="result-message">{result.message}</p>
          {result.result_type === 'table' && <ResultTable data={result.data} />}
          {result.result_type === 'value' && <p className="result-value">{result.data.toString()}</p>}
        </div>
      )}
    </div>
  );
}

export default CommandInput;

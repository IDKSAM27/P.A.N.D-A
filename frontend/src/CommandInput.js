import React, { useState } from 'react';

// A helper component to render the results table
const ResultTable = ({ data }) => {
  if (!data || data.length === 0) {
    return <p>No data to display.</p>;
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
            {headers.map(header => <td key={header}>{row[header]}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  );
};


function CommandInput({ sessionId }) {
  const [command, setCommand] = useState('');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (!command) {
      setError('Please enter a command.');
      return;
    }

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          command: command,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Analysis failed.');
      }

      setResult(data);
      console.log('Analysis successful:', data);

    } catch (err) {
      setError(err.message);
      console.error('Analysis error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="analysis-container">
      <h2>Step 2: Ask a Question</h2>
      <div className="command-form">
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="e.g., total sales by product"
          className="command-input"
        />
        <button onClick={handleAnalyze} disabled={isLoading}>
          {isLoading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {error && <p className="error-message">{error}</p>}
      
      {result && (
        <div className="result-container">
          <h3>Analysis Result</h3>
          <p><strong>Message:</strong> {result.message}</p>
          {result.result_type === 'table' && <ResultTable data={result.data} />}
          {result.result_type === 'value' && <p className="result-value"><strong>Value:</strong> {result.data.toString()}</p>}
        </div>
      )}
    </div>
  );
}

export default CommandInput;

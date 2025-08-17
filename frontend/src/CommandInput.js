import React, { useState } from 'react';
import ChartView from './ChartView'; // Assuming this exists from previous steps

// A helper component to render the results table
const ResultTable = ({ data }) => {
  if (!data || data.length === 0) {
    return null;
  }
  const headers = Object.keys(data);

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

  // --- NEW: List of example commands ---
  const exampleCommands = [
    { value: '', label: 'Choose an example...' },
    { value: 'total units sold by day', label: 'total units sold by day' },
    { value: 'plot the total units sold by day as a bar chart', label: 'plot the total units sold by day as a bar chart' },
    { value: 'show the top 3 coffee types by sales', label: 'show the top 3 coffee types by sales' },
    { value: 'what are the 2 days with the lowest units sold', label: 'what are the 2 days with the lowest units sold' },
    { value: 'describe the data', label: 'describe the data' },
  ];

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

  // --- NEW: Handle example selection ---
  const handleExampleSelect = (e) => {
    setCommand(e.target.value);
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
          className="command-input"
        />
        <select className="example-dropdown" onChange={handleExampleSelect}>
          {exampleCommands.map((ex, index) => (
            <option key={index} value={ex.value}>
              {ex.label}
            </option>
          ))}
        </select>
        <button 
          onClick={handleAnalyze} 
          disabled={isLoading || !command} 
          className="button-primary"
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
          {result.result_type === 'plot' && <ChartView plotData={result.plot_data} />}
        </div>
      )}
    </div>
  );
}

export default CommandInput;

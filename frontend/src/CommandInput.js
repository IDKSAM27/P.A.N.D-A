import React, { useState } from 'react';
import Select from 'react-select';
import ChartView from './ChartView'; 

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

// Updated example options for react-select
const exampleCommands = [
  { value: '', label: 'Example' },
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
  const handleExampleSelect = (option) => {
      setCommand(option.value);
    };

    return (
      <div className="container analysis-container">
        {/* ...columns-display... */}
        <div className="command-form">
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && handleAnalyze()}
            placeholder="e.g., total units sold by day"
            className="command-input"
          />
          {/* NEW: ReactSelect dropdown styled for dark mode */}
          <Select
            className="example-dropdown"
            classNamePrefix="example"
            options={exampleCommands}
            defaultValue={exampleCommands[0]}
            onChange={handleExampleSelect}
            styles={{
              control: base => ({
                ...base,
                backgroundColor: '#21272b',
                borderColor: '#4caf50',
                minWidth: 100,
                width: 150,
                color: '#e6e6e6',
                boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
              }),
              singleValue: base => ({ ...base, color: '#e6e6e6' }),
              menu: base => ({
                ...base,
                backgroundColor: '#282c34',
                color: '#e6e6e6',
                borderRadius: '8px',
                marginTop: 2,
                boxShadow: '0 8px 24px rgba(0,100,0,0.15)',
              }),
              option: (base, state) => ({
                ...base,
                backgroundColor: state.isFocused
                  ? '#2ecc40'
                  : '#282c34',
                color: state.isFocused ? '#fff' : '#e6e6e6',
                cursor: 'pointer',
              }),
              dropdownIndicator: base => ({
                ...base,
                color: '#4caf50'
              }),
              indicatorSeparator: base => ({
                ...base,
                backgroundColor: '#4caf50'
              }),
            }}
            isSearchable={false}
          />
          <button 
            onClick={handleAnalyze} 
            disabled={isLoading || !command} 
            className="button-primary"
          >
            {isLoading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>
        {/* ... result rendering ... */}
      </div>
    );
  }
  
  export default CommandInput;

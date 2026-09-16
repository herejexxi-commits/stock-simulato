import { useState } from 'react';

export default function MarketsAI() {
  const [symbol, setSymbol] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generateReport = async () => {
    if (!symbol || !apiKey) {
      setError('Por favor ingresa un símbolo y tu API Key de Gemini');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/ai/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, api_key: apiKey })
      });
      
      if (!response.ok) {
        throw new Error('Error al generar el reporte');
      }
      
      const data = await response.json();
      setReport(data.report);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass p-6 animate-fade-in" style={{ padding: '2rem' }}>
      <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>🤖 Mercados e Inteligencia Artificial</h2>
      
      <div className="glass" style={{ padding: '1.5rem', marginBottom: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <p>Utiliza Google Gemini para analizar el sentimiento de noticias recientes sobre una acción específica.</p>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Símbolo (Ej. AAPL, TSLA)</label>
            <input 
              type="text" 
              value={symbol} 
              onChange={e => setSymbol(e.target.value.toUpperCase())}
              placeholder="Símbolo..."
            />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Gemini API Key</label>
            <input 
              type="password" 
              value={apiKey} 
              onChange={e => setApiKey(e.target.value)}
              placeholder="Pega tu clave aquí..."
            />
          </div>
        </div>
        
        <button 
          className="btn-primary" 
          onClick={generateReport}
          disabled={loading}
          style={{ alignSelf: 'flex-start', marginTop: '0.5rem' }}
        >
          {loading ? 'Analizando...' : 'Generar Reporte de IA'}
        </button>
      </div>
      
      {error && <div style={{ color: 'var(--danger-color)', marginBottom: '1rem' }}>{error}</div>}
      
      {report && (
        <div className="glass animate-fade-in" style={{ padding: '1.5rem', borderLeft: '4px solid var(--accent-color)' }}>
          <h3 style={{ marginBottom: '1rem', color: 'var(--accent-color)' }}>Análisis para {symbol}</h3>
          <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{report}</div>
        </div>
      )}
    </div>
  );
}

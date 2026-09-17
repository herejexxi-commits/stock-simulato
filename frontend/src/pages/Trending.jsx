import { useState, useEffect } from 'react';

export default function Trending() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/market/trending')
      .then(res => res.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="glass p-6 animate-fade-in"><h2 className="text-primary">Buscando tendencias del mercado...</h2></div>;

  return (
    <div className="glass p-6 animate-fade-in" style={{ padding: '2rem' }}>
      <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>🚀 En Tendencia Alcista</h2>
      
      {data.length === 0 ? (
        <p>No se encontraron datos de tendencia en este momento.</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {data.map((stock, idx) => (
            <div key={idx} className="glass" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: '1.5rem', margin: 0 }}>{stock.symbol}</h3>
                <span style={{ 
                  background: 'transparent', 
                  border: '1px solid var(--success-color)',
                  color: 'var(--success-color)', 
                  padding: '0.25rem 0.5rem', 
                  borderRadius: '4px',
                  fontWeight: 600
                }}>
                  +{stock.change_pct.toFixed(2)}%
                </span>
              </div>
              <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{stock.name}</p>
              <div style={{ fontSize: '1.25rem', fontWeight: 500, marginTop: '0.5rem' }}>
                ${stock.close.toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

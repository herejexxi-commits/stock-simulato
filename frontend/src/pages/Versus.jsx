import { useState, useEffect } from 'react';

export default function Versus() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/versus')
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

  if (loading) return <div className="glass p-6 animate-fade-in"><h2 className="text-primary">Calculando estado de jugadores...</h2></div>;
  if (!data) return <div className="glass p-6 animate-fade-in"><h2 className="text-danger">Error al cargar datos.</h2></div>;

  const users = Object.keys(data);
  // Simple check to see who is winning
  let leader = null;
  if (users.length >= 2) {
    if (data[users[0]]['Total Value'] > data[users[1]]['Total Value']) leader = users[0];
    else if (data[users[1]]['Total Value'] > data[users[0]]['Total Value']) leader = users[1];
  }

  return (
    <div className="glass p-6 animate-fade-in" style={{ padding: '2rem' }}>
      <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>🏆 Competencia Global</h2>
      
      {leader ? (
        <div style={{ background: 'rgba(16, 185, 129, 0.2)', padding: '1rem', borderRadius: '8px', color: 'var(--success-color)', marginBottom: '2rem', fontWeight: 600 }}>
          👑 ¡{leader} va ganando la competencia!
        </div>
      ) : (
        <div style={{ background: 'rgba(59, 130, 246, 0.2)', padding: '1rem', borderRadius: '8px', color: 'var(--accent-color)', marginBottom: '2rem', fontWeight: 600 }}>
          ⚖️ ¡Están completamente empatados!
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem' }}>
        {users.map(user => {
          const stats = data[user];
          const isPositive = stats['P&L ($)'] >= 0;
          return (
            <div key={user} className="glass" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <h3 style={{ fontSize: '1.5rem', margin: 0 }}>👤 {user}</h3>
              <div>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Valor Total del Portafolio</p>
                <div style={{ fontSize: '2.5rem', fontWeight: 700 }}>${stats['Total Value'].toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
              </div>
              <div>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Rentabilidad (P&L)</p>
                <div style={{ fontSize: '1.25rem', fontWeight: 600, color: isPositive ? 'var(--success-color)' : 'var(--danger-color)' }}>
                  {isPositive ? '+' : ''}{stats['P&L (%)'].toFixed(2)}% (${stats['P&L ($)'].toLocaleString(undefined, {minimumFractionDigits: 2})})
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';

export default function Journal({ user }) {
  const [history, setHistory] = useState([]);
  const [closedTrades, setClosedTrades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    
    // Fetch History & Closed Trades in parallel
    Promise.all([
      fetch(`/api/portfolio/${user}/history`).then(r => r.json()),
      fetch(`/api/portfolio/${user}/closed`).then(r => r.json())
    ]).then(([histData, closedData]) => {
      setHistory(Array.isArray(histData) ? histData : []);
      setClosedTrades(Array.isArray(closedData) ? closedData : []);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [user]);

  if (loading) return <div className="glass p-6 animate-fade-in"><h2 className="text-primary">Cargando bitácora...</h2></div>;

  const totalClosed = closedTrades.length;
  const winningTrades = closedTrades.filter(t => t['P&L ($)'] > 0).length;
  const winRate = totalClosed > 0 ? ((winningTrades / totalClosed) * 100).toFixed(1) : 0.0;
  const totalRealizedPnl = closedTrades.reduce((acc, t) => acc + t['P&L ($)'], 0);

  return (
    <div className="glass p-6 animate-fade-in" style={{ padding: '2rem' }}>
      <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>📖 Bitácora & Analítica de {user}</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="glass" style={{ padding: '1rem' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Operaciones Cerradas</p>
          <h3 style={{ fontSize: '1.5rem' }}>{totalClosed}</h3>
        </div>
        <div className="glass" style={{ padding: '1rem' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>Win Rate</p>
          <h3 style={{ fontSize: '1.5rem' }}>{winRate}%</h3>
        </div>
        <div className="glass" style={{ padding: '1rem' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>P&L Realizado Total</p>
          <h3 style={{ fontSize: '1.5rem', color: totalRealizedPnl >= 0 ? 'var(--success-color)' : 'var(--danger-color)' }}>
            ${totalRealizedPnl.toLocaleString(undefined, {minimumFractionDigits: 2})}
          </h3>
        </div>
      </div>

      <h3 style={{ marginBottom: '1rem' }}>📋 Registro de Operaciones Cerradas</h3>
      {closedTrades.length === 0 ? (
        <p style={{ color: 'var(--text-secondary)' }}>Aún no tienes operaciones cerradas (ventas).</p>
      ) : (
        <div style={{ overflowX: 'auto', marginBottom: '2rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--card-border)' }}>
                <th style={{ padding: '0.75rem' }}>Símbolo</th>
                <th style={{ padding: '0.75rem' }}>Acciones</th>
                <th style={{ padding: '0.75rem' }}>Compra</th>
                <th style={{ padding: '0.75rem' }}>Venta</th>
                <th style={{ padding: '0.75rem' }}>Fecha Salida</th>
                <th style={{ padding: '0.75rem' }}>P&L ($)</th>
                <th style={{ padding: '0.75rem' }}>P&L (%)</th>
              </tr>
            </thead>
            <tbody>
              {closedTrades.map((t, idx) => {
                const isWin = t['P&L ($)'] >= 0;
                return (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--card-border)' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 600 }}>{t.Symbol}</td>
                    <td style={{ padding: '0.75rem' }}>{t.Shares.toFixed(4)}</td>
                    <td style={{ padding: '0.75rem' }}>${t['Buy Price'].toFixed(2)}</td>
                    <td style={{ padding: '0.75rem' }}>${t['Sell Price'].toFixed(2)}</td>
                    <td style={{ padding: '0.75rem' }}>{t['Exit Date'].split(' ')[0]}</td>
                    <td style={{ padding: '0.75rem', color: isWin ? 'var(--success-color)' : 'var(--danger-color)', fontWeight: 600 }}>
                      {isWin ? '+' : ''}${t['P&L ($)'].toFixed(2)}
                    </td>
                    <td style={{ padding: '0.75rem', color: isWin ? 'var(--success-color)' : 'var(--danger-color)' }}>
                      {isWin ? '+' : ''}{t['P&L (%)'].toFixed(2)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

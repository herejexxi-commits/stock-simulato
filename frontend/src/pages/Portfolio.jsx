import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const COLORS = ['#2962FF', '#089981', '#F23645', '#F5A623', '#9C27B0', '#00BCD4'];

export default function Portfolio({ user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/portfolio/${user}`)
      .then(res => {
        if (!res.ok) throw new Error("API Error");
        return res.json();
      })
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setData(null);
        setLoading(false);
      });
  }, [user]);

  if (loading) return <div className="glass p-6 animate-fade-in"><h2 className="text-primary">Cargando portafolio...</h2></div>;
  if (!data) return <div className="glass p-6 animate-fade-in"><h2 className="text-danger">Error al cargar</h2></div>;

  const totalPositionsValue = data.positions.reduce((acc, pos) => acc + pos['Current Value'], 0);
  const totalValue = data.cash + totalPositionsValue;

  // Pie chart data
  const pieData = [
    { name: 'Efectivo', value: data.cash },
    ...data.positions.map(p => ({ name: p.Symbol, value: p['Current Value'] }))
  ];

  // Bar chart data
  const barData = data.positions.map(p => ({
    name: p.Symbol,
    pnl: p['P&L (%)'],
    days: p['Holding Days'] || 0
  }));

  return (
    <div className="glass p-6 animate-fade-in" style={{ padding: '2rem' }}>
      <h2 style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>📊 Resumen de {user}</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="glass" style={{ padding: '1.5rem' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Valor Total</p>
          <h3 style={{ fontSize: '2rem' }}>${totalValue.toLocaleString(undefined, {minimumFractionDigits: 2})}</h3>
        </div>
        <div className="glass" style={{ padding: '1.5rem' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Efectivo Disponible</p>
          <h3 style={{ fontSize: '2rem', color: 'var(--success-color)' }}>${data.cash.toLocaleString(undefined, {minimumFractionDigits: 2})}</h3>
        </div>
        <div className="glass" style={{ padding: '1.5rem' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>Posiciones Abiertas</p>
          <h3 style={{ fontSize: '2rem' }}>{data.positions.length}</h3>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem', marginBottom: '2rem' }}>
        <div className="glass" style={{ padding: '1rem', height: '300px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', textAlign: 'center' }}>Distribución</h3>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `$${value.toLocaleString(undefined, {minimumFractionDigits: 2})}`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="glass" style={{ padding: '1rem', height: '300px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', textAlign: 'center' }}>Rentabilidad por Activo (%)</h3>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="var(--text-secondary)" />
              <YAxis stroke="var(--text-secondary)" />
              <Tooltip cursor={{fill: 'var(--card-border)'}} />
              <Bar dataKey="pnl" fill="var(--accent-color)">
                {barData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? 'var(--success-color)' : 'var(--danger-color)'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <h3 style={{ marginBottom: '1rem' }}>📋 Posiciones Actuales</h3>
      {data.positions.length === 0 ? (
        <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>No tienes posiciones abiertas.</p>
      ) : (
        <div style={{ marginTop: '1.5rem', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--card-border)' }}>
                <th style={{ padding: '1rem' }}>Símbolo</th>
                <th style={{ padding: '1rem' }}>Acciones</th>
                <th style={{ padding: '1rem' }}>Precio Medio</th>
                <th style={{ padding: '1rem' }}>Precio Actual</th>
                <th style={{ padding: '1rem' }}>Valor Actual</th>
                <th style={{ padding: '1rem' }}>P&L ($)</th>
              </tr>
            </thead>
            <tbody>
              {data.positions.map((pos, idx) => {
                const pnl = pos['P&L ($)'];
                return (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--card-border)' }}>
                    <td style={{ padding: '1rem', fontWeight: 600 }}>{pos.Symbol}</td>
                    <td style={{ padding: '1rem' }}>{pos.Shares.toFixed(4)}</td>
                    <td style={{ padding: '1rem' }}>${pos['Average Cost'].toFixed(2)}</td>
                    <td style={{ padding: '1rem' }}>${pos['Current Price'].toFixed(2)}</td>
                    <td style={{ padding: '1rem' }}>${pos['Current Value'].toFixed(2)}</td>
                    <td style={{ padding: '1rem', color: pnl >= 0 ? 'var(--success-color)' : 'var(--danger-color)', fontWeight: 600 }}>
                      {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)} ({pos['P&L (%)'].toFixed(2)}%)
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

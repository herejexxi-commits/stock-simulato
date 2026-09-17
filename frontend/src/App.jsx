import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, TrendingUp, Globe2, BookOpen, Trophy, Settings } from 'lucide-react';
import Portfolio from './pages/Portfolio';
import Trending from './pages/Trending';
import MarketsAI from './pages/MarketsAI';
import Journal from './pages/Journal';
import Versus from './pages/Versus';
import './App.css';

const Admin = () => <div className="glass p-6 animate-fade-in" style={{ padding: '2rem' }}><h2>⚙️ Ajustes en construcción...</h2></div>;

function TradePanel({ activeUser, onTradeSuccess }) {
  const [symbol, setSymbol] = useState('');
  const [tradeMode, setTradeMode] = useState('shares');
  const [inputValue, setInputValue] = useState(1);
  const [modelo, setModelo] = useState('');
  const [plazo, setPlazo] = useState('1 mes');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  const handleTrade = async (action) => {
    if (!symbol) return;
    setLoading(true);
    setMsg(null);
    try {
      let notes = '';
      if (modelo || plazo) {
        notes = `Modelo: ${modelo || 'N/A'} | Plazo: ${plazo || 'N/A'}`;
      }
      
      let payload = { symbol: symbol.toUpperCase(), notes };
      if (tradeMode === 'shares') {
        payload.shares = inputValue;
      } else {
        payload.amount_usd = inputValue;
      }

      const response = await fetch(`/api/portfolio/${activeUser}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Error al operar');
      
      setMsg({ type: 'success', text: `¡${action === 'buy' ? 'Compra' : 'Venta'} exitosa!` });
      if (onTradeSuccess) onTradeSuccess();
    } catch (err) {
      setMsg({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: 'var(--bg-color)', padding: '1rem', borderRadius: '4px', border: '1px solid var(--card-border)', marginBottom: '1rem' }}>
      <h3 style={{ fontSize: '1rem', marginBottom: '1rem' }}>🛒 Panel de Operaciones</h3>
      
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Símbolo</label>
        <input 
          type="text" 
          value={symbol} 
          onChange={e => setSymbol(e.target.value.toUpperCase())}
          placeholder="Ej. AAPL" 
          style={{ padding: '0.5rem', fontSize: '0.9rem' }}
        />
      </div>
      
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Operar por</label>
        <select 
          value={tradeMode} 
          onChange={e => setTradeMode(e.target.value)}
          style={{ padding: '0.5rem', fontSize: '0.9rem', marginBottom: '0.5rem' }}
        >
          <option value="shares">Cantidad de Acciones</option>
          <option value="usd">Monto en Dólares (USD)</option>
        </select>

        <input 
          type="number" 
          min="0.01" step="0.01" 
          value={inputValue} 
          onChange={e => setInputValue(parseFloat(e.target.value))}
          style={{ padding: '0.5rem', fontSize: '0.9rem' }}
          placeholder={tradeMode === 'shares' ? "Ej. 1.5" : "Ej. 100.00"}
        />
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Modelo Predictivo</label>
        <input 
          type="text" 
          value={modelo} 
          onChange={e => setModelo(e.target.value)}
          placeholder="Ej. Random Forest" 
          style={{ padding: '0.5rem', fontSize: '0.9rem' }}
        />
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Plazo de Expiración</label>
        <select 
          value={plazo} 
          onChange={e => setPlazo(e.target.value)}
          style={{ padding: '0.5rem', fontSize: '0.9rem' }}
        >
          <option value="1 mes">1 mes</option>
          <option value="3 meses">3 meses</option>
          <option value="6 meses">6 meses</option>
          <option value="1 año">1 año</option>
          <option value="Sin plazo">Sin plazo</option>
        </select>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button 
          className="btn-primary" 
          style={{ flex: 1, padding: '0.5rem', fontSize: '0.9rem' }}
          onClick={() => handleTrade('buy')}
          disabled={loading}
        >
          Comprar
        </button>
        <button 
          className="btn-secondary" 
          style={{ flex: 1, padding: '0.5rem', fontSize: '0.9rem' }}
          onClick={() => handleTrade('sell')}
          disabled={loading}
        >
          Vender
        </button>
      </div>

      {msg && (
        <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: msg.type === 'error' ? 'var(--danger-color)' : 'var(--success-color)' }}>
          {msg.text}
        </div>
      )}
    </div>
  );
}

function Sidebar({ activeUser, setActiveUser, isMobileOpen, setIsMobileOpen }) {
  const location = useLocation();
  const [cash, setCash] = useState(0);

  const fetchCash = () => {
    fetch(`/api/portfolio/${activeUser}`)
      .then(r => r.json())
      .then(d => setCash(d.cash))
      .catch(() => {});
  };

  useEffect(() => {
    fetchCash();
    // Auto refresh every 5 mins (300000ms), only if the tab is active
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchCash();
      }
    }, 300000);
    return () => clearInterval(interval);
  }, [activeUser, location]); // location to refresh cash on navigation

  const navItems = [
    { path: '/', label: 'Mi Portafolio', icon: <LayoutDashboard size={20} /> },
    { path: '/trending', label: 'En Tendencia', icon: <TrendingUp size={20} /> },
    { path: '/markets', label: 'Mercados e IA', icon: <Globe2 size={20} /> },
    { path: '/journal', label: 'Bitácora', icon: <BookOpen size={20} /> },
    { path: '/versus', label: 'Versus', icon: <Trophy size={20} /> },
    { path: '/admin', label: 'Ajustes', icon: <Settings size={20} /> },
  ];

  return (
    <div className={`glass app-sidebar ${isMobileOpen ? 'open' : ''}`}>
      
      <div>

        
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>👤 Perfil Activo</label>
          <select 
            value={activeUser}
            onChange={(e) => setActiveUser(e.target.value)}
          >
            <option value="Juan David">Juan David</option>
            <option value="Sebastian">Sebastian</option>
          </select>
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link 
              key={item.path} 
              to={item.path}
              onClick={() => { if(window.innerWidth <= 768) setIsMobileOpen(false); }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '0.75rem 1rem',
                borderRadius: '4px',
                textDecoration: 'none',
                color: isActive ? 'white' : 'var(--text-secondary)',
                background: isActive ? 'var(--accent-color)' : 'transparent',
                transition: 'var(--transition)'
              }}
            >
              {item.icon}
              <span style={{ fontWeight: isActive ? 600 : 400 }}>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div style={{ marginTop: 'auto' }}>
        <TradePanel activeUser={activeUser} onTradeSuccess={fetchCash} />
        
        <div style={{ background: 'var(--bg-color)', padding: '1rem', borderRadius: '4px', border: '1px solid var(--card-border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Efectivo Disponible</div>
            <button 
              onClick={() => { fetchCash(); window.location.reload(); }} 
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem' }}
              title="Actualizar datos"
            >
              🔄
            </button>
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--success-color)' }}>
            ${cash.toLocaleString(undefined, {minimumFractionDigits: 2})}
          </div>
        </div>
      </div>

    </div>
  );
}

function App() {
  const [activeUser, setActiveUser] = useState('Juan David');
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <Router>
      <div className="app-container">
        <Sidebar activeUser={activeUser} setActiveUser={setActiveUser} isMobileOpen={isMobileOpen} setIsMobileOpen={setIsMobileOpen} />
        
        <main className="main-content" onClick={() => { if(isMobileOpen) setIsMobileOpen(false); }}>
          <header className="app-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <button className="mobile-toggle" onClick={(e) => { e.stopPropagation(); setIsMobileOpen(!isMobileOpen); }}>
                ☰
              </button>
              <h1 style={{ margin: 0 }}>Simulador de Bolsa</h1>
            </div>
          </header>

          <Routes>
            <Route path="/" element={<Portfolio user={activeUser} />} />
            <Route path="/trending" element={<Trending />} />
            <Route path="/markets" element={<MarketsAI />} />
            <Route path="/journal" element={<Journal user={activeUser} />} />
            <Route path="/versus" element={<Versus />} />
            <Route path="/admin" element={<Admin user={activeUser} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

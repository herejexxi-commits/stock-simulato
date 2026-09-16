from decimal import Decimal
from datetime import datetime
import streamlit as st
import pandas as pd
from database import DBManager
from catalog import get_symbol_sector, get_symbol_info

def parse_date(ts_str):
    if not ts_str:
        return datetime.now()
    if isinstance(ts_str, datetime):
        return ts_str.replace(tzinfo=None)
    try:
        dt = pd.to_datetime(ts_str).to_pydatetime()
        return dt.replace(tzinfo=None)
    except Exception:
        return datetime.now()

class Portfolio:
    def __init__(self, user_name: str):
        self.user_name = user_name
        self.db = DBManager()
        
    @property
    def cash(self) -> Decimal:
        return Decimal(self.db.get_cash(self.user_name))
        
    def buy(self, symbol: str, shares: float | str | Decimal, price: float | str | Decimal, notes: str = "", timestamp: str = None):
        symbol = symbol.upper()
        s = Decimal(str(shares))
        p = Decimal(str(price))
        cost = s * p
        
        current_cash = self.cash
        if cost > current_cash:
            raise ValueError(f"Fondos insuficientes. Costo: ${cost:,.2f}, Disponible: ${current_cash:,.2f}")
            
        pos = self.db.get_position(self.user_name, symbol)
        if pos:
            current_shares = Decimal(pos[0])
            current_total_cost = Decimal(pos[1])
        else:
            current_shares = Decimal('0')
            current_total_cost = Decimal('0')
            
        new_shares = current_shares + s
        new_total_cost = current_total_cost + cost
        
        self.db.upsert_position(self.user_name, symbol, str(new_shares), str(new_total_cost))
        self.db.update_cash(self.user_name, str(current_cash - cost))
        self.db.add_transaction(self.user_name, "BUY", symbol, str(s), str(p), str(cost), notes, timestamp)
        
    def sell(self, symbol: str, shares: float | str | Decimal, price: float | str | Decimal, notes: str = "", timestamp: str = None):
        symbol = symbol.upper()
        s = Decimal(str(shares))
        p = Decimal(str(price))
        revenue = s * p
        
        pos = self.db.get_position(self.user_name, symbol)
        if not pos:
            raise ValueError("No posees este activo en tu portafolio.")
            
        current_shares = Decimal(pos[0])
        current_total_cost = Decimal(pos[1])
        
        if s > current_shares:
            raise ValueError("No hay suficientes acciones para vender.")
            
        avg_cost = current_total_cost / current_shares
        new_shares = current_shares - s
        new_total_cost = current_total_cost - (s * avg_cost)
        
        if new_shares == Decimal('0'):
            self.db.delete_position(self.user_name, symbol)
        else:
            self.db.upsert_position(self.user_name, symbol, str(new_shares), str(new_total_cost))
            
        current_cash = self.cash
        self.db.update_cash(self.user_name, str(current_cash + revenue))
        self.db.add_transaction(self.user_name, "SELL", symbol, str(s), str(p), str(revenue), notes, timestamp)

    def deposit(self, amount: float | str | Decimal, notes: str = "Depósito de capital", timestamp: str = None):
        a = Decimal(str(amount))
        if a <= Decimal('0'):
            raise ValueError("El monto a depositar debe ser mayor a cero.")
            
        current_cash = self.cash
        new_cash = current_cash + a
        self.db.update_cash(self.user_name, str(new_cash))
        # Insertamos como transacción para que sobreviva al motor de REPLAY de la función deshacer
        self.db.add_transaction(self.user_name, "DEPOSIT", "USD", "0", "1", str(a), notes, timestamp)
        
    def reset_account(self):
        self.db.reset_account(self.user_name)
        
    def undo_last(self):
        txs = self.db.get_user_transactions(self.user_name)
        if not txs:
            raise ValueError("No hay operaciones para deshacer.")
            
        # Extraemos todo excepto el primer elemento (que es la operación más reciente)
        transactions_to_replay = txs[1:]
        
        # Volteamos la lista para ejecutarlos en orden cronológico correcto (del más antiguo al más nuevo)
        transactions_to_replay.reverse()
        
        # Reseteamos la cuenta por completo a su estado virgen
        self.reset_account()
        
        # Re-ejecutamos todas las operaciones pasadas inyectando su timestamp original para mantener integridad
        for tx in transactions_to_replay:
            timestamp = tx[0]
            tx_type = tx[1]
            symbol = tx[2]
            shares = Decimal(str(tx[3]))
            price = Decimal(str(tx[4]))
            total = Decimal(str(tx[5]))
            notes = tx[6] if tx[6] else ""
            
            if tx_type == "BUY":
                self.buy(symbol, shares, price, notes, timestamp)
            elif tx_type == "SELL":
                self.sell(symbol, shares, price, notes, timestamp)
            elif tx_type == "DEPOSIT":
                self.deposit(total, notes, timestamp)

    def _get_active_lots(self) -> dict:
        """Calcula los lotes abiertos activos mediante FIFO para determinar fechas de entrada y días de tenencia."""
        txs = self.db.get_user_transactions(self.user_name)
        if not txs:
            return {}
            
        chronological_txs = list(reversed(txs))
        lots = {}
        
        for tx in chronological_txs:
            t_str, tx_type, symbol, shares_str, price_str, _, _ = tx
            symbol = symbol.upper()
            shares = Decimal(str(shares_str))
            price = Decimal(str(price_str))
            tx_dt = parse_date(t_str)
            
            if tx_type == "BUY":
                if symbol not in lots:
                    lots[symbol] = []
                lots[symbol].append({
                    'timestamp': tx_dt,
                    'shares': shares,
                    'price': price
                })
            elif tx_type == "SELL":
                shares_to_sell = shares
                if symbol in lots:
                    while shares_to_sell > Decimal('0') and lots[symbol]:
                        lot = lots[symbol][0]
                        matched_shares = min(shares_to_sell, lot['shares'])
                        lot['shares'] -= matched_shares
                        shares_to_sell -= matched_shares
                        if lot['shares'] <= Decimal('0'):
                            lots[symbol].pop(0)
                            
        return lots

    def get_summary(self) -> list[dict]:
        summary = []
        positions = self.db.get_all_positions(self.user_name)
        active_lots = self._get_active_lots()
        now = datetime.now()
        
        for sym, shares_str, total_cost_str, _ in positions:
            shares = Decimal(shares_str)
            total_cost = Decimal(total_cost_str)
            avg_cost = total_cost / shares if shares > Decimal('0') else Decimal('0')
            sector = get_symbol_sector(sym)
            
            # Calcular días de tenencia desde el lote activo más antiguo
            lots_for_sym = active_lots.get(sym, [])
            if lots_for_sym:
                earliest_lot_time = lots_for_sym[0]['timestamp']
                delta_days = max(0.0, (now - earliest_lot_time).total_seconds() / 86400.0)
                entry_date_str = earliest_lot_time.strftime('%Y-%m-%d %H:%M')
            else:
                delta_days = 0.0
                entry_date_str = "N/A"
                
            summary.append({
                'Symbol': sym,
                'Sector': sector,
                'Shares': float(shares),
                'Average Cost': float(avg_cost),
                'Total Cost': float(total_cost),
                'Holding Days': round(delta_days, 1),
                'Entry Date': entry_date_str
            })
        return summary
        
    def get_transactions(self) -> list[dict]:
        txs = self.db.get_user_transactions(self.user_name)
        result = []
        for t in txs:
            result.append({
                'Fecha': t[0],
                'Tipo': t[1],
                'Acción': t[2],
                'Sector': get_symbol_sector(t[2]),
                'Cantidad': float(t[3]),
                'Precio': float(t[4]),
                'Total': float(t[5]),
                'Notas': t[6] if t[6] else ""
            })
        return result

    def get_closed_trades(self) -> list[dict]:
        """Calcula operaciones cerradas mediante FIFO con días de tenencia, rendimiento y sector."""
        txs = self.db.get_user_transactions(self.user_name)
        if not txs:
            return []
            
        chronological_txs = list(reversed(txs))
        lots = {}
        closed_trades = []
        
        for tx in chronological_txs:
            t_str, tx_type, symbol, shares_str, price_str, total_str, notes = tx
            symbol = symbol.upper()
            shares = Decimal(str(shares_str))
            price = Decimal(str(price_str))
            tx_dt = parse_date(t_str)
            
            if tx_type == "BUY":
                if symbol not in lots:
                    lots[symbol] = []
                lots[symbol].append({
                    'timestamp': tx_dt,
                    'shares': shares,
                    'price': price
                })
            elif tx_type == "SELL":
                shares_to_sell = shares
                if symbol not in lots:
                    lots[symbol] = []
                    
                while shares_to_sell > Decimal('0') and lots[symbol]:
                    lot = lots[symbol][0]
                    matched_shares = min(shares_to_sell, lot['shares'])
                    buy_time = lot['timestamp']
                    buy_price = lot['price']
                    
                    holding_seconds = max(0.0, (tx_dt - buy_time).total_seconds())
                    holding_days = holding_seconds / 86400.0
                    
                    cost = matched_shares * buy_price
                    revenue = matched_shares * price
                    pnl_dollars = revenue - cost
                    pnl_percent = ((price - buy_price) / buy_price) * Decimal('100') if buy_price > Decimal('0') else Decimal('0')
                    
                    closed_trades.append({
                        'Symbol': symbol,
                        'Sector': get_symbol_sector(symbol),
                        'Shares': float(matched_shares),
                        'Buy Price': float(buy_price),
                        'Sell Price': float(price),
                        'Entry Date': buy_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'Exit Date': tx_dt.strftime('%Y-%m-%d %H:%M:%S'),
                        'Holding Days': round(holding_days, 2),
                        'Holding Hours': round(holding_seconds / 3600.0, 1),
                        'P&L ($)': float(pnl_dollars),
                        'P&L (%)': float(pnl_percent),
                        'Notes': notes if notes else ""
                    })
                    
                    lot['shares'] -= matched_shares
                    shares_to_sell -= matched_shares
                    if lot['shares'] <= Decimal('0'):
                        lots[symbol].pop(0)
                        
        return closed_trades

    def get_historical_equity(self, days: int = 30) -> pd.DataFrame:
        """Reconstruye el valor histórico del portafolio durante los últimos X días."""
        from datetime import timedelta
        import yfinance as yf
        
        @st.cache_data(ttl=3600)
        def download_historical_prices(symbols_tuple, start_str, end_str):
            if not symbols_tuple:
                return pd.DataFrame()
            try:
                data = yf.download(list(symbols_tuple), start=start_str, end=end_str, progress=False)
                return data
            except Exception:
                return pd.DataFrame()
        
        now = datetime.now()
        start_date = (now - timedelta(days=days)).date()
        
        db_txs = self.db.get_user_transactions(self.user_name)
        chron_txs = list(reversed(db_txs))
        
        symbols = set(tx[2].upper() for tx in chron_txs if tx[2] != "USD")
        
        prices_df = pd.DataFrame()
        if symbols:
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = (now + timedelta(days=1)).strftime('%Y-%m-%d')
            data = download_historical_prices(tuple(symbols), start_str, end_str)
            if not data.empty:
                if isinstance(data.columns, pd.MultiIndex):
                    prices_df = data['Close']
                else:
                    prices_df = pd.DataFrame({list(symbols)[0]: data['Close']})
            
            if not prices_df.empty:
                prices_df.index = pd.to_datetime(prices_df.index).normalize()
                
        date_range = pd.date_range(start=start_date, end=now.date(), freq='D')
        
        if not prices_df.empty:
            prices_df = prices_df.reindex(date_range)
            prices_df = prices_df.ffill().bfill()
        else:
            prices_df = pd.DataFrame(index=date_range)
            for sym in symbols:
                prices_df[sym] = 0.0
                
        current_cash = 10000.0  # Asumimos que el saldo inicial es $10,000 según database.py
        current_shares = {sym: 0.0 for sym in symbols}
        equity_data = []
        
        tx_idx = 0
        num_txs = len(chron_txs)
        
        for current_date in date_range:
            d = current_date.date()
            
            while tx_idx < num_txs:
                tx = chron_txs[tx_idx]
                t_str, tx_type, symbol, shares_str, price_str, total_str, _ = tx
                tx_date = parse_date(t_str).date()
                
                if tx_date > d:
                    break
                    
                shares = float(shares_str)
                total = float(total_str)
                symbol = symbol.upper()
                
                if tx_type == "DEPOSIT":
                    current_cash += total
                elif tx_type == "BUY":
                    current_cash -= total
                    current_shares[symbol] = current_shares.get(symbol, 0.0) + shares
                elif tx_type == "SELL":
                    current_cash += total
                    current_shares[symbol] = max(0.0, current_shares.get(symbol, 0.0) - shares)
                        
                tx_idx += 1
                
            stock_value = 0.0
            for sym, sh in current_shares.items():
                if sh > 0 and sym in prices_df.columns:
                    price = prices_df.loc[current_date, sym]
                    if not pd.isna(price):
                        stock_value += sh * price
                        
            total_equity = current_cash + stock_value
            equity_data.append({
                'Date': current_date,
                'Equity': total_equity
            })
            
        return pd.DataFrame(equity_data)

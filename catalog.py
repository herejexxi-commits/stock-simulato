"""
Catálogo universal de acciones de Estados Unidos consumiendo la API de la SEC.
"""
import requests
import time
import yfinance as yf

CUSTOM_OPTION = "✍️ Otro (Ingresar ticker manual)"

# Fallback categories para mantener compatibilidad gráfica con los activos anteriores
FALLBACK_SECTORS = {
    # Tecnología
    "META": "Tecnología", "NVDA": "Tecnología", "AAPL": "Tecnología", "MSFT": "Tecnología", "GOOGL": "Tecnología",
    "AVGO": "Tecnología", "AMD": "Tecnología", "DELL": "Tecnología", "CRM": "Tecnología", "QCOM": "Tecnología", "TXN": "Tecnología", 
    "NOW": "Tecnología", "AMAT": "Tecnología", "INTU": "Tecnología", "IBM": "Tecnología", "MU": "Tecnología", 
    "MRVL": "Tecnología", "PANW": "Tecnología", "CSCO": "Tecnología", "ADBE": "Tecnología", "INTC": "Tecnología",
    
    # Salud
    "UNH": "Salud", "JNJ": "Salud", "LLY": "Salud", "MRK": "Salud", "ABBV": "Salud", "TMO": "Salud", 
    "DHR": "Salud", "ABT": "Salud", "PFE": "Salud", "ISRG": "Salud", "SYK": "Salud", "VRTX": "Salud", 
    "REGN": "Salud", "ZTS": "Salud", "BSX": "Salud", "MDT": "Salud", "MCK": "Salud", "COR": "Salud",
    "BMY": "Salud", "CVS": "Salud",
    
    # Financiero
    "JPM": "Financiero", "BAC": "Financiero", "GS": "Financiero", "V": "Financiero", "MA": "Financiero",
    "WFC": "Financiero", "BRK-B": "Financiero", "SPGI": "Financiero", "AXP": "Financiero", "MS": "Financiero",
    "BX": "Financiero", "SCHW": "Financiero", "BLK": "Financiero", "C": "Financiero", "PGR": "Financiero",
    "MMC": "Financiero", "CB": "Financiero", "PYPL": "Financiero", "CME": "Financiero", "ICE": "Financiero",
    
    # Consumo/Cloud
    "AMZN": "Consumo/Cloud", "TSLA": "Consumo/Cloud", "WMT": "Consumo/Cloud", "NFLX": "Consumo/Cloud", 
    "PG": "Consumo/Cloud", "COST": "Consumo/Cloud", "HD": "Consumo/Cloud", "KO": "Consumo/Cloud", 
    "PEP": "Consumo/Cloud", "MCD": "Consumo/Cloud", "NKE": "Consumo/Cloud", "SBUX": "Consumo/Cloud", 
    "DIS": "Consumo/Cloud", "CMCSA": "Consumo/Cloud", "TGT": "Consumo/Cloud", "LOW": "Consumo/Cloud",
    "BKNG": "Consumo/Cloud", "ABNB": "Consumo/Cloud", "MAR": "Consumo/Cloud", "TJX": "Consumo/Cloud"
}

_cache_us_stocks = {"time": 0, "data": []}

def fetch_us_stocks() -> list[dict]:
    """Descarga la lista oficial de la SEC y la cachea por 24 horas."""
    global _cache_us_stocks
    if time.time() - _cache_us_stocks["time"] < 86400 and _cache_us_stocks["data"]:
        return _cache_us_stocks["data"]
    try:
        headers = {'User-Agent': 'StockSimulator admin@stocksimulator.com'}
        res = requests.get('https://www.sec.gov/files/company_tickers.json', headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        stocks = []
        for val in data.values():
            ticker = val["ticker"]
            title = val["title"].title()
            sector = FALLBACK_SECTORS.get(ticker, "General / Mercado")
            
            stocks.append({
                "symbol": ticker,
                "name": title,
                "sector": sector
            })
        
        # Ordenar alfabéticamente
        stocks.sort(key=lambda x: x['symbol'])
        _cache_us_stocks = {"time": time.time(), "data": stocks}
        return stocks
    except Exception as e:
        # Fallback de emergencia si falla la red
        return [
            {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Tecnología"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Tecnología"},
            {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "sector": "General / Mercado"}
        ]

def get_catalog_options() -> list[str]:
    """Retorna la lista de opciones formateadas para el selectbox."""
    stocks = fetch_us_stocks()
    options = [f"{item['symbol']} - {item['name']}" for item in stocks]
    options.append(CUSTOM_OPTION)
    return options

def parse_selected_ticker(selection: str) -> str:
    """Extrae el símbolo del texto formateado o retorna vacío si es opción manual."""
    if not selection or selection == CUSTOM_OPTION:
        return ""
    return selection.split(" - ")[0].strip().upper()

def get_symbol_info(symbol: str) -> dict:
    """Obtiene metadatos (nombre, sector) de un símbolo."""
    symbol = symbol.upper() if symbol else ""
    stocks = fetch_us_stocks()
    
    # Búsqueda en la data cacheada
    for item in stocks:
        if item["symbol"] == symbol:
            return item
            
    # Si no está en la base de datos de la SEC
    return {
        "symbol": symbol,
        "name": symbol,
        "sector": FALLBACK_SECTORS.get(symbol, "Personalizado / Otro")
    }

def get_symbol_sector(symbol: str) -> str:
    """Retorna el sector correspondiente al símbolo."""
    return get_symbol_info(symbol).get("sector", "Personalizado / Otro")

POPULAR_TICKERS = list(FALLBACK_SECTORS.keys())

_cache_top_gainers = {}

def get_top_gainers(limit: int = 10, sector: str = None) -> list[dict]:
    global _cache_top_gainers
    cache_key = f"{limit}_{sector}"
    if cache_key in _cache_top_gainers and time.time() - _cache_top_gainers[cache_key]["time"] < 120:
        return _cache_top_gainers[cache_key]["data"]
    """
    Obtiene las acciones con mayor porcentaje de ganancia en el día actual
    desde una lista curada de acciones populares.
    Opcionalmente filtra por sector.
    """
    try:
        tickers = yf.Tickers(" ".join(POPULAR_TICKERS))
        gainers = []
        for symbol in POPULAR_TICKERS:
            try:
                # Bypassing cache to ensure updated sectors are used immediately
                sym_sector = FALLBACK_SECTORS.get(symbol, "Desconocido")
                if sector and sym_sector != sector:
                    continue
                    
                hist = tickers.tickers[symbol].history(period="1d")
                if not hist.empty:
                    open_price = hist['Open'].iloc[-1]
                    close_price = hist['Close'].iloc[-1]
                    if open_price > 0:
                        change_pct = ((close_price - open_price) / open_price) * 100
                        gainers.append({
                            "symbol": symbol,
                            "name": get_symbol_info(symbol).get("name", symbol),
                            "sector": sym_sector,
                            "open": float(open_price),
                            "close": float(close_price),
                            "change_pct": float(change_pct)
                        })
            except Exception:
                continue
                
        # Ordenar de mayor a menor porcentaje
        gainers.sort(key=lambda x: x["change_pct"], reverse=True)
        res = gainers[:limit]
        _cache_top_gainers[cache_key] = {"time": time.time(), "data": res}
        return res
    except Exception as e:
        return []

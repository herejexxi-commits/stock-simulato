import sys
import os
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from decimal import Decimal
import pandas as pd

# Añadir el directorio padre al sys.path para poder importar los módulos del simulador
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio import Portfolio
import catalog
import ai_agent
from database import DBManager

app = FastAPI(title="Stock Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TradeRequest(BaseModel):
    symbol: str
    amount_usd: float = None
    shares: float = None
    notes: str = ""

class AIReportRequest(BaseModel):
    api_key: str
    symbol: str

@app.get("/api/stock/{ticker}")
async def get_stock_price(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if hist.empty:
            raise HTTPException(status_code=404, detail="Stock data not found")
        current_price = hist['Close'].iloc[-1]
        return {"ticker": ticker.upper(), "price": float(current_price)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/{user}")
async def get_portfolio(user: str):
    try:
        pf = Portfolio(user)
        summary = pf.get_summary()
        
        # Add current prices to calculate current value and P&L
        if summary:
            symbols = [item['Symbol'] for item in summary]
            tickers = yf.Tickers(" ".join(symbols))
            for item in summary:
                try:
                    hist = tickers.tickers[item['Symbol']].history(period="1d")
                    item['Current Price'] = float(hist['Close'].iloc[-1]) if not hist.empty else 0.0
                except:
                    item['Current Price'] = 0.0
                
                item['Current Value'] = item['Shares'] * item['Current Price']
                item['P&L ($)'] = item['Current Value'] - item['Total Cost']
                item['P&L (%)'] = (item['P&L ($)'] / item['Total Cost'] * 100) if item['Total Cost'] > 0 else 0.0

        return {
            "cash": float(pf.cash),
            "positions": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/{user}/buy")
async def buy_stock(user: str, req: TradeRequest):
    try:
        pf = Portfolio(user)
        ticker = yf.Ticker(req.symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            raise HTTPException(status_code=404, detail="No price found for symbol")
        current_price = hist['Close'].iloc[-1]
        
        if req.amount_usd is not None:
            shares_to_trade = Decimal(str(req.amount_usd)) / Decimal(str(current_price))
        else:
            shares_to_trade = Decimal(str(req.shares))
            
        pf.buy(req.symbol, shares_to_trade, current_price, req.notes)
        return {"message": "Buy successful", "shares": float(shares_to_trade), "price": float(current_price)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/{user}/sell")
async def sell_stock(user: str, req: TradeRequest):
    try:
        pf = Portfolio(user)
        ticker = yf.Ticker(req.symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            raise HTTPException(status_code=404, detail="No price found for symbol")
        current_price = hist['Close'].iloc[-1]
        
        if req.amount_usd is not None:
            shares_to_trade = Decimal(str(req.amount_usd)) / Decimal(str(current_price))
        else:
            shares_to_trade = Decimal(str(req.shares))
            
        pf.sell(req.symbol, shares_to_trade, current_price, req.notes)
        return {"message": "Sell successful", "shares": float(shares_to_trade), "price": float(current_price)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/{user}/history")
async def get_history(user: str, days: int = 30):
    try:
        pf = Portfolio(user)
        equity_df = pf.get_historical_equity(days=days)
        if equity_df.empty:
            return []
        
        # Convert to records
        equity_df['Date'] = equity_df['Date'].astype(str)
        return equity_df.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/portfolio/{user}/closed")
async def get_closed_trades(user: str):
    try:
        pf = Portfolio(user)
        return pf.get_closed_trades()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/catalog/search")
async def search_catalog(query: str):
    try:
        info = catalog.get_symbol_info(query)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/catalog/options")
async def get_catalog_options():
    try:
        options = catalog.get_catalog_options()
        return options
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/trending")
async def get_trending(sector: str = None):
    try:
        gainers = catalog.get_top_gainers(limit=10, sector=sector)
        return gainers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/report")
async def get_ai_report(req: AIReportRequest):
    try:
        if not req.api_key:
            raise HTTPException(status_code=400, detail="API Key required")
            
        asset_info = catalog.get_symbol_info(req.symbol)
        
        # Fetch basic news & price
        news_data_ai = []
        try:
            raw_news = yf.Ticker(req.symbol).news
            if raw_news:
                for n in raw_news[:5]:
                    content = n.get('content', n)
                    title = content.get('title', 'Sin título')
                    publisher = content.get('provider', {}).get('displayName', content.get('publisher', 'Desconocida'))
                    news_data_ai.append((title, publisher))
        except:
            pass
            
        current_price = 0.0
        try:
            hist = yf.Ticker(req.symbol).history(period="1d")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
        except:
            pass
            
        report = ai_agent.generate_stock_analysis(
            api_key=req.api_key,
            symbol=req.symbol.upper(),
            company_name=asset_info.get('name', req.symbol.upper()),
            price=round(float(current_price), 2),
            news_headlines=news_data_ai
        )
        return {"report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/versus")
async def get_versus():
    try:
        db = DBManager()
        all_cash = db.get_all_cash()
        all_positions = db.get_all_positions() 
        
        unique_symbols = list(set([row[0] for row in all_positions]))
        live_prices = {}
        if unique_symbols:
            try:
                tickers = yf.Tickers(" ".join(unique_symbols))
                for sym in unique_symbols:
                    hist = tickers.tickers[sym].history(period="1d")
                    if not hist.empty:
                        live_prices[sym] = hist['Close'].iloc[-1]
                    else:
                        live_prices[sym] = 0.0
            except:
                live_prices = {sym: 0.0 for sym in unique_symbols}
                
        user_stats = {}
        users = ["Juan David", "Sebastian"]
        INITIAL_CAPITAL = 10000.0
        
        for u in users:
            cash = float(all_cash.get(u, INITIAL_CAPITAL))
            stock_value = 0.0
            for row in all_positions:
                sym, shares_str, _, user_name = row
                if user_name == u:
                    stock_value += float(Decimal(shares_str)) * live_prices.get(sym, 0.0)
                    
            total_value = cash + stock_value
            pnl_dollars = total_value - INITIAL_CAPITAL
            pnl_percent = (pnl_dollars / INITIAL_CAPITAL) * 100
            
            user_stats[u] = {
                "Total Value": total_value,
                "P&L ($)": pnl_dollars,
                "P&L (%)": pnl_percent
            }
            
        return user_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from portfolio import Portfolio
from database import DBManager
from decimal import Decimal
import catalog
import ai_agent

@st.cache_data(ttl=60)
def get_live_prices(symbols: tuple) -> dict:
    if not symbols:
        return {}
    current_prices = {}
    try:
        tickers = yf.Tickers(" ".join(symbols))
        for sym in symbols:
            hist = tickers.tickers[sym].history(period="1d")
            if not hist.empty:
                current_prices[sym] = hist['Close'].iloc[-1]
            else:
                current_prices[sym] = 0.0
    except Exception as e:
        current_prices = {sym: 0.0 for sym in symbols}
    return current_prices

@st.cache_data(ttl=60)
def get_historical_data(symbol: str, period: str):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.history(period=period)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_news_for_symbols(symbols: tuple) -> dict:
    news_dict = {}
    for sym in symbols:
        try:
            news_dict[sym] = yf.Ticker(sym).news
        except Exception:
            news_dict[sym] = []
    return news_dict

@st.cache_data(ttl=3600)
def get_earnings_calendar(symbols: tuple) -> list:
    earnings_list = []
    try:
        tickers = yf.Tickers(" ".join(symbols))
        for sym in symbols:
            cal = tickers.tickers[sym].calendar
            if cal is not None:
                if isinstance(cal, dict) and 'Earnings Date' in cal:
                    dates = cal['Earnings Date']
                    date_val = dates[0] if isinstance(dates, list) and len(dates) > 0 else dates
                    if date_val:
                        earnings_list.append({"Símbolo": sym, "Fecha": pd.to_datetime(date_val).strftime("%Y-%m-%d")})
                elif hasattr(cal, 'index') and not cal.empty and 'Earnings Date' in cal.index:
                    date_val = cal.loc['Earnings Date'].iloc[0] if isinstance(cal.loc['Earnings Date'], pd.Series) else cal.loc['Earnings Date']
                    if pd.notna(date_val):
                        earnings_list.append({"Símbolo": sym, "Fecha": pd.to_datetime(date_val).strftime("%Y-%m-%d")})
    except Exception:
        pass
    return earnings_list

# Configuración de página
st.set_page_config(
    page_title="Simulador de Bolsa Pro",
    layout="wide",
    page_icon="📈"
)

# Autorefresco automático cada 60 segundos (60,000 ms)
refresh_count = st_autorefresh(interval=60 * 1000, limit=None, key="market_data_autorefresh")

st.markdown("<h1 style='text-align: center;'>Simulador de Bolsa</h1>", unsafe_allow_html=True)

# Selector global de usuario en la barra lateral
st.sidebar.header("👤 Perfil Activo")
active_user = st.sidebar.selectbox("Selecciona usuario:", ["Juan David", "Sebastian"])

pf = Portfolio(user_name=active_user)

st.sidebar.markdown("---")
st.sidebar.header("🛒 Panel de Operaciones")

# Catálogo universal con selector inteligente (búsqueda y autocompletado)
catalog_options = catalog.get_catalog_options()
selected_catalog_item = st.sidebar.selectbox(
    "Busca un Activo (Ticker o Nombre):",
    options=catalog_options,
    index=0,
    help="Escribe el nombre de la empresa o el Ticker para buscar en toda la bolsa de EE.UU."
)

if selected_catalog_item == catalog.CUSTOM_OPTION:
    ticker_input = st.sidebar.text_input("Símbolo personalizado (Ticker)", value="").strip().upper()
else:
    ticker_input = catalog.parse_selected_ticker(selected_catalog_item)

if ticker_input:
    asset_info = catalog.get_symbol_info(ticker_input)
    st.sidebar.caption(f"🏢 **{asset_info['name']}**  \n🏷️ Sector: *{asset_info['sector']}*")

order_type = st.sidebar.radio("Tipo de orden", ["Por cantidad de acciones", "Por monto en USD"])

if order_type == "Por cantidad de acciones":
    shares_input = st.sidebar.number_input("Cantidad de acciones", min_value=0.0001, value=1.0, step=0.01, format="%.4f")
    amount_input = None
else:
    amount_input = st.sidebar.number_input("Monto en USD ($)", min_value=1.0, value=100.0, step=10.0, format="%.2f")
    shares_input = None

notes_input = st.sidebar.text_input("Justificación de entrada (opcional)", placeholder="Ej. Ruptura técnica alcista...")

col1, col2 = st.sidebar.columns(2)
buy_btn = col1.button("Comprar", type="primary", use_container_width=True)
sell_btn = col2.button("Vender", type="secondary", use_container_width=True)

if buy_btn or sell_btn:
    if not ticker_input:
        st.sidebar.error("Por favor selecciona o ingresa un símbolo válido.")
    else:
        with st.spinner("Obteniendo precio de mercado..."):
            ticker = yf.Ticker(ticker_input)
            try:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    st.sidebar.error(f"No se encontró información para el símbolo '{ticker_input}'.")
                    current_price = None
            except Exception as e:
                st.sidebar.error(f"Error consultando precio: {str(e)}")
                current_price = None
                
        if current_price is not None:
            if amount_input is not None:
                shares_to_trade = Decimal(str(amount_input)) / Decimal(str(current_price))
            else:
                shares_to_trade = Decimal(str(shares_input))
                
            action = "buy" if buy_btn else "sell"
            try:
                if action == "buy":
                    pf.buy(ticker_input, shares_to_trade, current_price, notes_input)
                    st.sidebar.success(f"¡Compra exitosa para {active_user}! {shares_to_trade:,.4f} {ticker_input} a ${current_price:,.2f}")
                else:
                    pf.sell(ticker_input, shares_to_trade, current_price, notes_input)
                    st.sidebar.success(f"¡Venta exitosa para {active_user}! {shares_to_trade:,.4f} {ticker_input} a ${current_price:,.2f}")
            except ValueError as e:
                st.sidebar.error(str(e))

st.sidebar.markdown("---")
st.sidebar.metric(f"Efectivo Disponible ({active_user})", f"${float(pf.cash):,.2f}")
st.sidebar.caption("⚡ *Autorefresco en vivo activo (cada 60s)*")

if st.sidebar.button("🔄 Refrescar Cotizaciones Ahora", use_container_width=True):
    if hasattr(st, 'rerun'):
        st.rerun()
    else:
        st.experimental_rerun()

# Pestañas de Interfaz
tab_portfolio, tab_trending, tab_markets, tab_journal, tab_versus, tab_admin = st.tabs([
    "📊 Mi Portafolio", 
    "🚀 En tendencia alcista",
    "🌐 Mercados y Noticias",
    "📖 Bitácora & Analítica", 
    "🏆 Competencia (Versus)", 
    "⚙️ Ajustes de Cuenta"
])

# ==========================================
# PESTAÑA 1: Mi Portafolio
# ==========================================
with tab_portfolio:
    portfolio_data = pf.get_summary()

    if not portfolio_data:
        st.info(f"El portafolio de {active_user} no tiene posiciones abiertas. Utiliza el panel de operaciones a la izquierda para empezar a invertir.")
        st.metric(f"Efectivo Disponible de {active_user}", f"${float(pf.cash):,.2f}")
    else:
        df = pd.DataFrame(portfolio_data)
        symbols = df['Symbol'].tolist()
        
        st.subheader(f"📊 Resumen del Portafolio: {active_user}")
        
        with st.spinner('Actualizando cotizaciones en vivo...'):
            current_prices = get_live_prices(tuple(symbols))
                
        df['Current Price'] = df['Symbol'].map(current_prices)
        df['Current Value'] = df['Shares'] * df['Current Price']
        df['P&L ($)'] = df['Current Value'] - df['Total Cost']
        df['P&L (%)'] = (df['P&L ($)'] / df['Total Cost']) * 100
        
        total_stock_value = df['Current Value'].sum()
        total_portfolio_value = float(pf.cash) + total_stock_value
        total_initial_cost = df['Total Cost'].sum()
        total_pnl_dollars = df['P&L ($)'].sum()
        total_pnl_percent = (total_pnl_dollars / total_initial_cost * 100) if total_initial_cost > 0 else 0.0
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Valor Total Portafolio", f"${total_portfolio_value:,.2f}")
        m2.metric("Valor en Acciones", f"${total_stock_value:,.2f}")
        m3.metric("Efectivo Disponible", f"${float(pf.cash):,.2f}")
        m4.metric("P&L No Realizado Total", f"${total_pnl_dollars:+,.2f}", f"{total_pnl_percent:+.2f}%")
        
        # ==============================================================
        # Requerimiento 1 y 2: Gráfico de Balance y Distribución (Broker Institucional)
        # ==============================================================
        st.markdown("---")
        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            st.subheader(f"📈 Evolución del Balance (Últimos 30 días)")
            with st.spinner("Calculando historial de balance..."):
                equity_df = pf.get_historical_equity(days=30)
                if not equity_df.empty:
                    fig_eq = px.line(
                        equity_df, x='Date', y='Equity',
                        title=f"Patrimonio Total (USD)",
                        labels={'Date': 'Fecha', 'Equity': 'USD'}
                    )
                    fig_eq.update_traces(line_color='#00C851', line_width=2.5, fill='tozeroy', fillcolor='rgba(0, 200, 81, 0.1)')
                    fig_eq.update_layout(xaxis_title='', yaxis_title='', margin=dict(l=0, r=0, t=30, b=0), height=350, hovermode='x unified')
                    st.plotly_chart(fig_eq, use_container_width=True, theme="streamlit")
                else:
                    st.info("No hay suficientes datos históricos para mostrar el balance.")
                    
        with col_chart2:
            st.markdown("<h3 style='text-align: center;'>Distribución del Portafolio</h3>", unsafe_allow_html=True)
            # Build allocation data
            alloc_data = [{'Activo': 'Efectivo (Cash)', 'Valor': float(pf.cash)}]
            for _, row in df.iterrows():
                alloc_data.append({'Activo': row['Symbol'], 'Valor': float(row['Current Value'])})
                
            df_alloc = pd.DataFrame(alloc_data)
            fig_pie = px.pie(
                df_alloc, values='Valor', names='Activo', hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(
                textposition='inside', 
                textinfo='percent+label', 
                hoverinfo='label+percent+value',
                textfont=dict(size=16, family="Arial Black")
            )
            fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=350, showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True, theme="streamlit")
            
        st.markdown("---")
        st.subheader("📋 Posiciones Actuales")
        
        # Tabla Formateada
        display_df = df.copy()
        display_df['Shares'] = display_df['Shares'].map('{:,.4f}'.format)
        display_df['Average Cost'] = display_df['Average Cost'].map('${:,.2f}'.format)
        display_df['Total Cost'] = display_df['Total Cost'].map('${:,.2f}'.format)
        display_df['Current Price'] = display_df['Current Price'].map('${:,.2f}'.format)
        display_df['Current Value'] = display_df['Current Value'].map('${:,.2f}'.format)
        display_df['P&L ($)'] = display_df['P&L ($)'].map('${:,.2f}'.format)
        display_df['P&L (%)'] = display_df['P&L (%)'].map('{:+.2f}%'.format)
        display_df['Días Tenencia'] = display_df['Holding Days'].map(lambda d: f"{d:.1f} d")
        
        def color_pnl(val):
            if isinstance(val, str) and ('$' in val or '%' in val):
                try:
                    num_str = val.replace('$', '').replace('%', '').replace(',', '')
                    num = float(num_str)
                    color = '#00C851' if num >= 0 else '#ff4444'
                    return f'color: {color}; font-weight: bold;'
                except:
                    return ''
            return ''
        
        cols_order = ['Symbol', 'Sector', 'Shares', 'Average Cost', 'Current Price', 'Current Value', 'P&L ($)', 'P&L (%)', 'Días Tenencia', 'Entry Date']
        styled_df = display_df[cols_order].style.map(color_pnl, subset=['P&L ($)', 'P&L (%)'])
        st.dataframe(styled_df, use_container_width=True)
        
        # ==============================================================
        # Requerimiento 3: Visualización de Tenencia y Rentabilidad
        # ==============================================================
        st.markdown("---")
        st.subheader("🎯 Rentabilidad y Tiempo de Tenencia de Posiciones Activas")
        
        bar_colors = ['#00C851' if val >= 0 else '#ff4444' for val in df['P&L (%)']]
        
        fig_tenure = go.Figure()
        
        fig_tenure.add_trace(go.Bar(
            x=df['Symbol'],
            y=df['P&L (%)'],
            marker=dict(
                color=bar_colors,
                line=dict(color='rgba(255, 255, 255, 0.2)', width=1.5)
            ),
            text=[f"{pnl:+.2f}%<br>({d:.1f} d)" for pnl, d in zip(df['P&L (%)'], df['Holding Days'])],
            textposition='outside',
            customdata=list(zip(df['P&L ($)'], df['Holding Days'], df['Sector'], df['Entry Date'], df['Current Value'])),
            hovertemplate=(
                "<b>Activo: %{x}</b> (%{customdata[2]})<br>" +
                "Rentabilidad: <b>%{y:+.2f}%</b><br>" +
                "Ganancia/Pérdida: <b>$%{customdata[0]:+,.2f}</b><br>" +
                "Tiempo en Tenencia: <b>%{customdata[1]:.1f} días</b><br>" +
                "Fecha Entrada: %{customdata[3]}<br>" +
                "Valor Actual: $%{customdata[4]:,.2f}<extra></extra>"
            )
        ))
        
        fig_tenure.update_layout(
            title=f"Desempeño de Posiciones Activas: Rentabilidad (%) y Días Transcurridos ({active_user})",
            xaxis_title="Activo en Portafolio",
            yaxis_title="Rentabilidad P&L (%)",
            yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='rgba(255,255,255,0.4)'),
            margin=dict(l=20, r=20, t=50, b=20),
            height=420
        )
        
        st.plotly_chart(fig_tenure, use_container_width=True, theme="streamlit")
        
        # Gráfico de Velas de Análisis Individual
        st.markdown("---")
        st.subheader(f"📈 Análisis Técnico Histórico")
        
        col_sel1, col_sel2 = st.columns([1, 3])
        with col_sel1:
            selected_symbol = st.selectbox("Selecciona activo a graficar:", symbols)
            period = st.selectbox("Periodo histórico:", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
            
        with col_sel2:
            if selected_symbol:
                with st.spinner(f'Cargando velas para {selected_symbol}...'):
                    hist = get_historical_data(selected_symbol, period)
                    
                    if not hist.empty:
                        fig = go.Figure(data=[go.Candlestick(
                            x=hist.index,
                            open=hist['Open'],
                            high=hist['High'],
                            low=hist['Low'],
                            close=hist['Close'],
                            name=selected_symbol
                        )])
                        
                        fig.update_layout(
                            title=f"Gráfico de Velas - {selected_symbol} ({period})",
                            yaxis_title='Precio (USD)',
                            xaxis_title='Fecha',
                            margin=dict(l=0, r=0, t=40, b=0),
                            height=480
                        )
                        st.plotly_chart(fig, use_container_width=True, theme="streamlit")
                    else:
                        st.warning("No se encontraron datos históricos para este símbolo.")

# ==========================================
# PESTAÑA: En tendencia alcista
# ==========================================
with tab_trending:
    st.subheader("🚀 Acciones en Tendencia Alcista por Sector")
    st.write("Analizando las empresas de mayor capitalización bursátil en tiempo real...")
    
    with st.spinner("Buscando las mejores oportunidades del mercado..."):
        sectores_clave = ["Tecnología", "Salud", "Financiero", "Consumo/Cloud"]
        
        def render_sector_table(sector_name):
            st.markdown(f"### 📊 {sector_name}")
            top_sector = catalog.get_top_gainers(limit=10, sector=sector_name)
            if top_sector:
                df = pd.DataFrame(top_sector)
                display_df = df[['symbol', 'name', 'close', 'change_pct']].copy()
                display_df.columns = ['Símbolo', 'Nombre', 'Precio', 'Ganancia (%)']
                display_df['Precio'] = display_df['Precio'].map('${:,.2f}'.format)
                display_df['Ganancia (%)'] = display_df['Ganancia (%)'].map('+{:.2f}%'.format)
                
                def color_positive(val):
                    return 'color: #00C851; font-weight: bold;' if '+' in str(val) else ''
                    
                styled = display_df.style.map(color_positive, subset=['Ganancia (%)'])
                st.dataframe(styled, use_container_width=True, hide_index=True)
            else:
                st.info(f"No se encontraron datos para {sector_name}.")
                
        # 2x2 Grid
        col1, col2 = st.columns(2)
        with col1:
            render_sector_table(sectores_clave[0])
            st.markdown("---")
            render_sector_table(sectores_clave[2])
        with col2:
            render_sector_table(sectores_clave[1])
            st.markdown("---")
            render_sector_table(sectores_clave[3])

# ==========================================
# PESTAÑA 2: Mercados y Noticias
# ==========================================
with tab_markets:
    st.subheader("🌐 Visión Global del Mercado e Investigación")
    
    # Buscador Universal
    market_search = st.selectbox(
        "🔍 Busca un Activo para ver Noticias e Investigar con IA:",
        options=catalog_options,
        index=0,
        key="market_search"
    )
    
    if market_search == catalog.CUSTOM_OPTION:
        search_ticker = st.text_input("Símbolo personalizado (Ticker) a buscar", value="").strip().upper()
    else:
        search_ticker = catalog.parse_selected_ticker(market_search)
        
    st.markdown("---")
    
    col_news, col_earn = st.columns([2, 1])
    
    with col_news:
        st.markdown("### 📰 Noticias Recientes")
        
        # Si no hay nada buscado o seleccionado, mostramos default
        search_symbols = [search_ticker] if search_ticker else ["SPY", "QQQ", "AAPL"]
        
        if search_ticker:
            st.caption(f"Noticias destacadas para el activo seleccionado: {search_ticker}")
            
            # IA Button
            if st.button("🤖 Generar Reporte de IA con Gemini", type="primary", use_container_width=True):
                api_key = st.session_state.get('gemini_api_key', '')
                if not api_key:
                    st.session_state['ai_report'] = "⚠️ No has configurado tu API Key de Gemini. Ve a la pestaña 'Ajustes de Cuenta' para ingresarla."
                    st.session_state['ai_report_ticker'] = search_ticker
                else:
                    with st.spinner("Analizando información con Inteligencia Artificial..."):
                        asset_info = catalog.get_symbol_info(search_ticker) if search_ticker else {'name': 'Activo'}
                        # Gather news
                        news_data_ai = []
                        news_dict = get_news_for_symbols((search_ticker,))
                        raw_news = news_dict.get(search_ticker, [])
                        if raw_news:
                            for n in raw_news[:5]:
                                content = n.get('content', n)
                                title = content.get('title', 'Sin título')
                                publisher = content.get('provider', {}).get('displayName', content.get('publisher', 'Desconocida'))
                                news_data_ai.append((title, publisher))
                        
                        # Get price
                        current_price = 0.0
                        try:
                            hist = yf.Ticker(search_ticker).history(period="1d")
                            if not hist.empty:
                                current_price = hist['Close'].iloc[-1]
                        except:
                            pass
                            
                        report = ai_agent.generate_stock_analysis(
                            api_key=api_key,
                            symbol=search_ticker,
                            company_name=asset_info.get('name', search_ticker),
                            price=round(float(current_price), 2),
                            news_headlines=news_data_ai
                        )
                        st.session_state['ai_report'] = report
                        st.session_state['ai_report_ticker'] = search_ticker
                        
            # Mostrar el reporte si existe en sesión y corresponde al activo actual
            if st.session_state.get('ai_report') and st.session_state.get('ai_report_ticker') == search_ticker:
                st.info(st.session_state['ai_report'])
        else:
            st.caption(f"Noticias destacadas del mercado global: {', '.join(search_symbols)}")
        
        with st.spinner("Cargando titulares..."):
            news_dict = get_news_for_symbols(tuple(search_symbols))
            for sym in search_symbols:
                news_data = news_dict.get(sym, [])
                if news_data:
                    for n in news_data[:3]:
                        with st.container():
                            content = n.get('content', n)
                            title = content.get('title', 'Sin título')
                            link = content.get('clickThroughUrl', {}).get('url', content.get('link', '#'))
                            publisher = content.get('provider', {}).get('displayName', content.get('publisher', 'Desconocida'))
                            
                            st.markdown(f"**[{title}]({link})**")
                            st.caption(f"_{sym}_ | Fuente: {publisher}")
                            st.write("")
                    
    with col_earn:
        st.markdown("### 📅 Calendario de Resultados (Earnings)")
        if search_ticker:
            key_earnings_symbols = [search_ticker]
            st.caption(f"Próximos reportes para {search_ticker}")
        else:
            key_earnings_symbols = ["AMZN", "MSFT", "UNH", "JPM", "NOW"]
            st.caption("Próximos reportes financieros clave del mercado")
            
        with st.spinner("Consultando fechas..."):
            earnings_list = get_earnings_calendar(tuple(key_earnings_symbols))
            
            if earnings_list:
                df_earn = pd.DataFrame(earnings_list).sort_values("Fecha")
                st.dataframe(df_earn, use_container_width=True, hide_index=True)
            else:
                st.info("No hay fechas de resultados programadas recientemente o falló la consulta.")

# ==========================================
# PESTAÑA 3: Bitácora & Analítica
# ==========================================
with tab_journal:
    st.subheader(f"📖 Bitácora & Analítica de Rendimiento: {active_user}")
    
    closed_trades = pf.get_closed_trades()
    all_txs = pf.get_transactions()
    
    # -------------------------------------------------------------
    # Requerimiento 4: Analítica de Bitácora y Operaciones Cerradas
    # -------------------------------------------------------------
    if closed_trades:
        df_closed = pd.DataFrame(closed_trades)
        
        # Métricas de Resumen
        total_closed = len(df_closed)
        winning_trades = len(df_closed[df_closed['P&L ($)'] > 0])
        win_rate = (winning_trades / total_closed) * 100 if total_closed > 0 else 0.0
        total_realized_pnl = df_closed['P&L ($)'].sum()
        avg_holding_days = df_closed['Holding Days'].mean()
        avg_return_pct = df_closed['P&L (%)'].mean()
        
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric("Operaciones Cerradas", f"{total_closed}")
        kpi2.metric("Tasa de Acierto (Win Rate)", f"{win_rate:.1f}%", f"{winning_trades}/{total_closed} ganadas")
        kpi3.metric("P&L Realizado Total", f"${total_realized_pnl:+,.2f}")
        kpi4.metric("Rentabilidad Media / Trade", f"{avg_return_pct:+.2f}%")
        kpi5.metric("Tenencia Media", f"{avg_holding_days:.1f} días")
        
        st.markdown("---")
        st.markdown("### 📊 Distribución de Rentabilidad y Sectores")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            # Gráfico 1: Rentabilidad vs Tiempo de Tenencia
            fig_dur = px.scatter(
                df_closed,
                x="Holding Days",
                y="P&L (%)",
                color="Sector",
                size="Shares",
                hover_name="Symbol",
                hover_data={
                    "Entry Date": True,
                    "Exit Date": True,
                    "Holding Days": ':.2f',
                    "P&L ($)": ':.2f',
                    "P&L (%)": ':.2f',
                    "Shares": ':.4f'
                },
                title="Rentabilidad (%) vs Días de Tenencia",
                labels={"Holding Days": "Días en Posición (Salida - Entrada)", "P&L (%)": "Rentabilidad Realizada (%)"}
            )
            fig_dur.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.4)")
            fig_dur.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_dur, use_container_width=True, theme="streamlit")
            
        with col_g2:
            # Gráfico 2: Rentabilidad Promedio por Sector
            sector_pnl = df_closed.groupby('Sector').agg({
                'P&L (%)': 'mean',
                'P&L ($)': 'sum',
                'Symbol': 'count'
            }).reset_index().rename(columns={'Symbol': 'Trades', 'P&L (%)': 'Rentabilidad Promedio (%)'})
            
            sector_colors = ['#00C851' if val >= 0 else '#ff4444' for val in sector_pnl['Rentabilidad Promedio (%)']]
            
            fig_sector = go.Figure()
            fig_sector.add_trace(go.Bar(
                x=sector_pnl['Sector'],
                y=sector_pnl['Rentabilidad Promedio (%)'],
                marker=dict(color=sector_colors),
                text=[f"{pnl:+.2f}% ({cnt} ops)" for pnl, cnt in zip(sector_pnl['Rentabilidad Promedio (%)'], sector_pnl['Trades'])],
                textposition='outside',
                customdata=list(zip(sector_pnl['P&L ($)'], sector_pnl['Trades'])),
                hovertemplate=(
                    "<b>Sector: %{x}</b><br>" +
                    "Rentabilidad Media: <b>%{y:+.2f}%</b><br>" +
                    "P&L Acumulado: <b>$%{customdata[0]:+,.2f}</b><br>" +
                    "Trades Cerrados: <b>%{customdata[1]}</b><extra></extra>"
                )
            ))
            fig_sector.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.4)")
            fig_sector.update_layout(
                title="Rentabilidad Promedio Realizada por Sector",
                xaxis_title="Sector",
                yaxis_title="Rentabilidad Media (%)",
                height=400,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_sector, use_container_width=True, theme="streamlit")
            
        st.markdown("### 📋 Registro Detallado de Operaciones Cerradas (FIFO)")
        display_closed = df_closed.copy()
        display_closed['Shares'] = display_closed['Shares'].map('{:,.4f}'.format)
        display_closed['Buy Price'] = display_closed['Buy Price'].map('${:,.2f}'.format)
        display_closed['Sell Price'] = display_closed['Sell Price'].map('${:,.2f}'.format)
        display_closed['P&L ($)'] = display_closed['P&L ($)'].map('${:,.2f}'.format)
        display_closed['P&L (%)'] = display_closed['P&L (%)'].map('{:+.2f}%'.format)
        display_closed['Días Tenencia'] = display_closed['Holding Days'].map(lambda d: f"{d:.2f} d")
        
        def color_pnl_closed(val):
            if isinstance(val, str) and ('$' in val or '%' in val):
                try:
                    num_str = val.replace('$', '').replace('%', '').replace(',', '')
                    num = float(num_str)
                    color = '#00C851' if num >= 0 else '#ff4444'
                    return f'color: {color}; font-weight: bold;'
                except:
                    return ''
            return ''
            
        styled_closed = display_closed[['Symbol', 'Sector', 'Shares', 'Buy Price', 'Sell Price', 'Entry Date', 'Exit Date', 'Días Tenencia', 'P&L ($)', 'P&L (%)', 'Notes']].style.map(color_pnl_closed, subset=['P&L ($)', 'P&L (%)'])
        st.dataframe(styled_closed, use_container_width=True)
        
    else:
        st.info("ℹ️ Aún no tienes operaciones cerradas (ventas). Cuando vendas parte o la totalidad de una posición, aquí se mostrarán los cálculos de días de tenencia (`Fecha Cierre - Fecha Entrada`), rentabilidad realizada y distribución por sectores.")
        
    st.markdown("---")
    st.markdown("### 📜 Historial Completo de Transacciones")
    if not all_txs:
        st.write("No hay transacciones registradas.")
    else:
        df_txs = pd.DataFrame(all_txs)
        df_txs['Fecha'] = pd.to_datetime(df_txs['Fecha']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        display_txs = df_txs.copy()
        display_txs['Cantidad'] = display_txs['Cantidad'].map('{:,.4f}'.format)
        display_txs['Precio'] = display_txs['Precio'].map('${:,.2f}'.format)
        display_txs['Total'] = display_txs['Total'].map('${:,.2f}'.format)
        
        def color_type(val):
            if val == 'BUY':
                return 'color: #00C851; font-weight: bold;'
            elif val == 'SELL':
                return 'color: #ff4444; font-weight: bold;'
            elif val == 'DEPOSIT':
                return 'color: #33b5e5; font-weight: bold;'
            return ''
            
        styled_txs = display_txs[['Fecha', 'Tipo', 'Acción', 'Sector', 'Cantidad', 'Precio', 'Total', 'Notas']].style.map(color_type, subset=['Tipo'])
        st.dataframe(styled_txs, use_container_width=True)

# ==========================================
# PESTAÑA 3: Competencia Global (Versus)
# ==========================================
with tab_versus:
    st.subheader("🏆 Competencia: Juan David vs Sebastian")
    
    with st.spinner("Calculando estado global de todos los jugadores..."):
        db = DBManager()
        all_cash = db.get_all_cash()
        all_positions = db.get_all_positions() 
        
        unique_symbols = list(set([row[0] for row in all_positions]))
        live_prices = get_live_prices(tuple(unique_symbols))
                
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
            
        if user_stats["Juan David"]["Total Value"] > user_stats["Sebastian"]["Total Value"]:
            st.success("👑 ¡Juan David va ganando la competencia!")
        elif user_stats["Sebastian"]["Total Value"] > user_stats["Juan David"]["Total Value"]:
            st.success("👑 ¡Sebastian va ganando la competencia!")
        else:
            st.info("⚖️ ¡Están completamente empatados!")
            
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("### 👤 Juan David")
            val = user_stats["Juan David"]["Total Value"]
            pnl_d = user_stats["Juan David"]["P&L ($)"]
            pnl_p = user_stats["Juan David"]["P&L (%)"]
            st.metric("Valor del Portafolio", f"${val:,.2f}", f"{pnl_p:+.2f}% (${pnl_d:+,.2f})")
            
        with c2:
            st.markdown("### 👤 Sebastian")
            val = user_stats["Sebastian"]["Total Value"]
            pnl_d = user_stats["Sebastian"]["P&L ($)"]
            pnl_p = user_stats["Sebastian"]["P&L (%)"]
            st.metric("Valor del Portafolio", f"${val:,.2f}", f"{pnl_p:+.2f}% (${pnl_d:+,.2f})")

# ==========================================
# PESTAÑA 4: Ajustes de Cuenta
# ==========================================
with tab_admin:
    st.subheader(f"⚙️ Administración de Cuenta: {active_user}")
    
    st.markdown("### 🤖 Configuración de Inteligencia Artificial")
    st.write("Ingresa tu clave de API de Google Gemini para habilitar los reportes de investigación con IA.")
    api_key_input = st.text_input("Gemini API Key", type="password", value=st.session_state.get('gemini_api_key', ''), placeholder="Pega aquí tu clave generada...")
    if st.button("Guardar API Key"):
        st.session_state['gemini_api_key'] = api_key_input
        st.success("✅ API Key guardada exitosamente en la sesión actual.")
        
    st.markdown("---")
    
    st.markdown("### Inyectar Capital")
    st.write("Agrega más fondos a tu cuenta virtual. Esto quedará registrado en tu bitácora.")
    dep_col1, dep_col2 = st.columns([1, 2])
    with dep_col1:
        deposit_amount = st.number_input("Monto a depositar ($)", min_value=1.0, value=5000.0, step=1000.0)
        if st.button("💵 Depositar Fondos"):
            try:
                pf.deposit(deposit_amount, notes="Depósito manual")
                st.success(f"¡Se han depositado ${deposit_amount:,.2f} exitosamente!")
            except Exception as e:
                st.error(f"Error: {e}")
                
    st.markdown("---")
    st.markdown("### Corrección de Errores")
    
    undo_col, reset_col = st.columns(2)
    with undo_col:
        st.write("¿Te equivocaste en tu última operación? El botón mágico borrará la transacción y reconstruirá tu cuenta como estaba.")
        if st.button("⏪ Deshacer última operación", help="Utiliza el motor de Replay para restaurar el saldo de tu cuenta y acciones."):
            try:
                pf.undo_last()
                st.success("✅ La última operación fue deshecha matemáticamente con éxito.")
            except Exception as e:
                st.warning(str(e))
                
    with reset_col:
        st.write("¿Quieres empezar de nuevo? Esto borrará tu portafolio e historial para regresarte a $10,000.")
        if st.button("⚠️ Resetear mi cuenta (Peligro)", type="primary"):
            try:
                pf.reset_account()
                st.success("✅ Cuenta reseteada a $10,000.")
            except Exception as e:
                st.error(f"Error: {e}")

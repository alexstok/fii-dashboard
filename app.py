import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime

# Lista de FIIs
fiis = [
    "AFHI11", "AJFI11", "ALZC11", "ALZM11", "MTOF11", "ALZT11", "ALZR11", "AURB11",
    # ... (inclua todos os tickers fornecidos)
]

# Layout do Dashboard
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.layout = html.Div([
    html.H1("Dashboard de Análise de FIIs", style={'textAlign': 'center'}),
    
    html.Div([
        dcc.Dropdown(
            id='fii-selector',
            options=[{'label': fii, 'value': fii} for fii in fiis],
            value='ALZR11',
            multi=True
        ),
        dcc.DatePickerRange(
            id='date-range',
            min_date_allowed=datetime(2010, 1, 1),
            max_date_allowed=datetime.now(),
            start_date=datetime(2020, 1, 1),
            end_date=datetime.now()
        )
    ], style={'padding': 20}),
    
    dcc.Graph(id='price-chart'),
    dcc.Graph(id='stochastic-oscillator')
])

# Callback para atualizar gráficos
@app.callback(
    [Output('price-chart', 'figure'),
     Output('stochastic-oscillator', 'figure')],
    [Input('fii-selector', 'value'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_charts(selected_fiis, start_date, end_date):
    figures = []
    
    # Gráfico de Preços e Médias Móveis
    price_fig = go.Figure()
    for fii in selected_fiis:
        df = yf.download(f"{fii}.SA", start=start_date, end=end_date)
        if df.empty:
            continue
        
        # Cálculo das Médias Móveis Exponenciais
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        price_fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name=f'{fii} Preço'))
        for ema in [9, 20, 50, 200]:
            price_fig.add_trace(go.Scatter(x=df.index, y=df[f'EMA{ema}'], mode='lines', name=f'EMA{ema}'))
    
    price_fig.update_layout(title='Preço e Médias Móveis', xaxis_title='Data', yaxis_title='Preço (R$)')
    
    # Gráfico do Stochastic Oscillator
    stoch_fig = go.Figure()
    for fii in selected_fiis:
        df = yf.download(f"{fii}.SA", start=start_date, end=end_date)
        if df.empty:
            continue
        
        # Cálculo do Stochastic Oscillator
        low_14 = df['Low'].rolling(window=14).min()
        high_14 = df['High'].rolling(window=14).max()
        df['%K'] = (df['Close'] - low_14) / (high_14 - low_14) * 100
        df['%D'] = df['%K'].rolling(window=3).mean()
        df['%D_EMA'] = df['%D'].ewm(span=9, adjust=False).mean()
        
        stoch_fig.add_trace(go.Scatter(x=df.index, y=df['%K'], mode='lines', name=f'{fii} %K'))
        stoch_fig.add_trace(go.Scatter(x=df.index, y=df['%D'], mode='lines', name=f'{fii} %D'))
        stoch_fig.add_trace(go.Scatter(x=df.index, y=df['%D_EMA'], mode='lines', name=f'{fii} %D EMA(9)'))
    
    stoch_fig.update_layout(title='Stochastic Oscillator', xaxis_title='Data', yaxis_title='Valor')
    
    return price_fig, stoch_fig

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8050)

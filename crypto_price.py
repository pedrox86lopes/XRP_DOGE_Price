import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
import pandas as pd
import time
import feedparser

# Binance API for prices
BINANCE_URL = "https://api.binance.com/api/v3/ticker/price"

# RSS Feeds for crypto news
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://cryptopanic.com/news/all/rss/",
]

# Initialize the app
app = dash.Dash(__name__)
app.title = "Crypto Tracker with Open News"

# Layout
app.layout = html.Div([
    html.H1("Real-Time Crypto Tracker with News", style={'textAlign': 'center'}),
    dcc.Interval(id='interval', interval=5000, n_intervals=0),  # Update every 5 seconds

    # Prices Section
    html.Div([
        html.Div([
            html.H3("DOGE Price (USD)", style={'textAlign': 'center'}),
            html.Div(id='doge-price', style={'textAlign': 'center', 'fontSize': 24})
        ], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([
            html.H3("XRP Price (USD)", style={'textAlign': 'center'}),
            html.Div(id='xrp-price', style={'textAlign': 'center', 'fontSize': 24})
        ], style={'width': '48%', 'display': 'inline-block'})
    ]),

    # Price Chart
    dcc.Graph(id='price-chart', style={'height': '400px'}),

    # News Section
    html.Div([
        html.H2("Latest News", style={'textAlign': 'center'}),
        html.Div(id='news-section', style={'textAlign': 'left', 'padding': '10px'})
    ])
])

# Initialize data storage
price_data = {'Time': [], 'DOGE': [], 'XRP': []}


# Fetch prices from Binance
def fetch_prices():
    try:
        doge_response = requests.get(BINANCE_URL, params={"symbol": "DOGEUSDT"}).json()
        xrp_response = requests.get(BINANCE_URL, params={"symbol": "XRPUSDT"}).json()
        doge_price = float(doge_response.get("price", 0))
        xrp_price = float(xrp_response.get("price", 0))
        return doge_price, xrp_price
    except Exception as e:
        return None, None


# Fetch news from RSS Feeds
def fetch_news():
    news_items = []
    for feed in RSS_FEEDS:
        try:
            parsed_feed = feedparser.parse(feed)
            for entry in parsed_feed.entries[:5]:  # Limit to 5 articles per feed
                news_items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary if hasattr(entry, 'summary') else "",
                    "published": entry.published if hasattr(entry, 'published') else ""
                })
        except Exception as e:
            continue
    return news_items


# Callback to update prices, chart, and news
@app.callback(
    [Output('doge-price', 'children'),
     Output('xrp-price', 'children'),
     Output('price-chart', 'figure'),
     Output('news-section', 'children')],
    [Input('interval', 'n_intervals')]
)
def update_dashboard(n):
    # Fetch prices
    doge_price, xrp_price = fetch_prices()

    # Update price data
    current_time = time.strftime("%H:%M:%S")
    if doge_price and xrp_price:
        price_data['Time'].append(current_time)
        price_data['DOGE'].append(doge_price)
        price_data['XRP'].append(xrp_price)

    # Limit data to last 60 points
    if len(price_data['Time']) > 60:
        for key in price_data.keys():
            price_data[key] = price_data[key][-60:]

    # Create chart
    df = pd.DataFrame(price_data)
    figure = {
        'data': [
            {'x': df['Time'], 'y': df['DOGE'], 'type': 'line', 'name': 'DOGE'},
            {'x': df['Time'], 'y': df['XRP'], 'type': 'line', 'name': 'XRP'}
        ],
        'layout': {'title': 'Price Trend (Last 60 Seconds)'}
    }

    # Fetch news
    articles = fetch_news()
    news_items = []
    for article in articles:
        news_items.append(html.Div([
            html.A(article['title'], href=article['link'], target="_blank", style={'fontSize': '18px'}),
            html.P(article['summary'], style={'fontSize': '14px'}),
            html.P(f"Published: {article['published']}", style={'fontSize': '12px', 'color': 'gray'}),
            html.Hr()
        ]))

    return (
        f"${doge_price:.4f}" if doge_price else "Error fetching price",
        f"${xrp_price:.4f}" if xrp_price else "Error fetching price",
        figure,
        news_items
    )


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

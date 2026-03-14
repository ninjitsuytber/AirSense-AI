import csv
import base64
import pandas as pd
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO

NEWS_API_KEY = "edbbebf8b6d84782b800f68e4706d5cd"

def validate_csv(file_content: bytes, filename: str):

    if not filename.lower().endswith('.csv'):
        return False, "File must be a CSV file", []
    
    try:
        stream = BytesIO(file_content)
        text_stream = stream.read().decode('utf-8').splitlines()
        if not text_stream:
            return False, "CSV file is empty", []
            
        csv_reader = csv.reader(text_stream)
        headers = next(csv_reader)
        if not headers:
            return False, "CSV file has no headers", []
            
        return True, "Valid CSV structure", headers
    except Exception as e:
        return f"Tool Error: Failed to read CSV: {str(e)}"

def fetch_environmental_news(query: str = "air quality pollution"):

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'sortBy': 'relevancy',
            'pageSize': 5
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json().get('articles', [])
        return []
    except Exception as e:
        return f"Tool Error: Failed to fetch environmental news: {str(e)}"

def generate_visualizations(df_json: str):

    try:
        df = pd.read_json(df_json)
        numeric_cols = df.select_dtypes(include=['number']).columns
        exclude = ['id', 'index', 'year', 'month', 'day', 'hour', 'timestamp', 'lat', 'lon']
        filtered_cols = [c for c in numeric_cols if not any(p in c.lower() for p in exclude)]
        
        if not filtered_cols:
            return {}

        charts = {}
        def fig_to_base64(fig):
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches='tight', facecolor='white')
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
            return img_str


        fig1 = plt.figure(figsize=(10, 5))
        plt.style.use('dark_background')
        for col in filtered_cols[:3]:
            plt.plot(df.index, df[col], label=col)
        plt.title('Air Quality Trends')
        plt.legend()
        charts['line_chart'] = fig_to_base64(fig1)


        fig2 = plt.figure(figsize=(10, 5))
        latest = df[filtered_cols].iloc[-1]
        latest.plot(kind='bar', color='skyblue')
        plt.title('Current Metric Comparison')
        charts['bar_chart'] = fig_to_base64(fig2)

        return charts
    except Exception as e:
        return f"Tool Error: Visualization failed: {str(e)}"

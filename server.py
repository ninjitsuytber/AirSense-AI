import os
import csv
import base64
import pandas as pd
import requests
from datetime import datetime, timedelta
from google import genai
from google.genai import types
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

NEWS_API_KEY = "edbbebf8b6d84782b800f68e4706d5cd"

class CSVValidator:
    @staticmethod
    def validate_file(file):
        if not file:
            return False, "No file provided"
        if not file.filename.lower().endswith('.csv'):
            return False, "File must be a CSV file"
        try:

            stream = BytesIO(file.read())
            file.seek(0) 
            
            text_stream = stream.read().decode('utf-8').splitlines()
            if not text_stream:
                return False, "CSV file is empty"
                
            csv_reader = csv.reader(text_stream)
            headers = next(csv_reader)
            if not headers:
                return False, "CSV file has no headers"
                
            row_count = 0
            for row in csv_reader:
                row_count += 1
                if row_count > 0:
                    break
            if row_count == 0:
                return False, "CSV file has no data rows"
                
            return True, f"Valid CSV structure with {len(headers)} columns"
        except Exception as e:
            return False, f"Error reading CSV: {str(e)}"

class DataProcessor:
    def __init__(self, file):
        self.file = file
        self.data = None
        self.headers = None
        
    def load_data(self):
        try:
            self.data = pd.read_csv(self.file)
            self.headers = list(self.data.columns)
            return True, "Data loaded successfully"
        except Exception as e:
            return False, f"Error loading data: {str(e)}"
            
    def get_data_as_text(self):
        if self.data is None:
            return ""
        text_parts = []
        text_parts.append(f"Total Rows: {len(self.data)}")
        text_parts.append(f"Columns: {', '.join(self.headers)}")
        text_parts.append("\nFirst 10 rows:")
        text_parts.append(self.data.head(10).to_string())
        numeric_cols = self.data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            text_parts.append("\nSummary Statistics:")
            text_parts.append(self.data[numeric_cols].describe().to_string())
        return "\n".join(text_parts)

class GeminiAnalyzer:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.generation_config = types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.8,
            top_k=40,
            max_output_tokens=24576,
        )
        
    def verify_air_quality_data(self, data_summary):
        prompt = f"""Analyze the following CSV data and determine if it is related to air quality or pollution monitoring.

Data Summary:
{data_summary}

Respond with ONLY one of these two options:
1. "VALID: This is air quality/pollution data" - if the data contains air quality or pollution metrics
2. "INVALID: This is not air quality data" - if the data is not related to air quality or pollution

Be strict in your assessment. The data must contain clear indicators of air quality measurements such as:
- Air Quality Index (AQI)
- Pollutant measurements (PM2.5, PM10, CO, NO2, SO2, O3, etc.)
- Air pollution levels
- Atmospheric quality metrics

At the beginning of your response, provide your internal reasoning inside a <think> block, then provide the final result.

Provide your response:"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=self.generation_config
            )
            full_text = response.text.strip()
            
            # Extract thinking log
            import re
            think_match = re.search(r'<think>(.*?)</think>', full_text, re.DOTALL)
            thought = think_match.group(1).strip() if think_match else "Analyzing data relevancy..."
            result = re.sub(r'<think>.*?</think>', '', full_text, flags=re.DOTALL).strip()

            if "VALID" in result.upper() and "AIR QUALITY" in result.upper():
                return True, result, thought
            else:
                return False, result, thought
        except Exception as e:
            return False, f"Error during verification: {str(e)}", ""
            
    def analyze_air_quality_data(self, data_text, news_context):
        prompt = f"""You are an expert air quality analyst. Provide ULTRA-CONCISE, TABULATED analysis.

AIR QUALITY DATA:
{data_text}

NEWS CONTEXT:
{news_context}

OUTPUT FORMAT (STRICT):

1. CURRENT STATUS TABLE
CRITICAL: Use EXACT column widths. Each column MUST have these EXACT character counts:
- Index column: 10 characters (pad with spaces)
- Value column: 8 characters (right-align numbers, pad left with spaces)
- Unit column: 7 characters (left-align, pad right with spaces)
- Status column: 31 characters (center-align, pad both sides with spaces)
- Std column: 7 characters (right-align numbers, pad left with spaces)
- Indicator column: 11 characters (center-align, pad both sides with spaces)

MANDATORY TABLE FORMAT (copy this structure EXACTLY):
```
| Index    | Value  | Unit  |             Status            | Std   | Indicator |
|----------|--------|-------|-------------------------------|-------|-----------|
| AQI      |  145   | -     |          Unhealthy            |  100  |     ✗     |
| PM2.5    |  55.2  | μg/m³ |          Moderate             |   25  |     !     |
| PM10     |  89.0  | μg/m³ |          Moderate             |   50  |     !     |
| CO       |   2.1  | ppm   |            Good               |    9  |     ✓     |
| NO2      |  42.0  | μg/m³ |            Good               |   40  |     ✓     |
| SO2      |  15.0  | μg/m³ |            Good               |   20  |     ✓     |
| O3       |  65.0  | μg/m³ |          Moderate             |  100  |     !     |
```

FORMATTING RULES (NON-NEGOTIABLE):
- Each row MUST start and end with | character
- Spaces MUST pad to exact column width
- Numbers MUST be right-aligned within their column
- Text MUST be center-aligned within Status and Indicator columns
- Status values: "Good", "Moderate", "Unhealthy", "Very Unhealthy", "Hazardous"
- Indicator: ✓ (Good), ! (Caution), ✗ (Hazardous)
- Include only pollutants present in dataset
- Std = WHO/EPA standard value

2. TREND COMPARISON TABLE
Format as properly aligned ASCII table with consistent spacing:

| Index    | Previous | Current | Change  |  Trend  |           Assessment          |
|----------|----------|---------|---------|---------|-------------------------------|
| AQI      | [val]    | [val]   | [±val]  | [↑/→/↓] | [Good/Moderate/Bad/Hazardous] |
| PM2.5    | [val]    | [val]   | [±val]  | [↑/→/↓] | [Good/Moderate/Bad/Hazardous] |
| PM10     | [val]    | [val]   | [±val]  | [↑/→/↓] | [Good/Moderate/Bad/Hazardous] |
| CO       | [val]    | [val]   | [±val]  | [↑/→/↓] | [Good/Moderate/Bad/Hazardous] |
| NO2      | [val]    | [val]   | [±val]  | [↑/→/↓] | [Good/Moderate/Bad/Hazardous] |
| SO2      | [val]    | [val]   | [±val]  | [↑/→/↓] | [Good/Moderate/Bad/Hazardous] |
| O3       | [val]    | [val]   | [±val]  | [↑/→/↓] | [Good/Moderate/Bad/Hazardous] |

(Include only pollutants with trend data available)

3. QUICK INSIGHTS (1 line per index)
- [Index]: [Current value] vs [Standard]. [Health impact]. [Trend] ([Good/Bad sign])
[Repeat for each pollutant - MAX 1 sentence each]

4. VERDICT
[2-3 sentences MAX: Overall status, main concerns, action needed]

5. PREDICTIONS
- 24h: [AQI range], [trend direction]
- 7d: [Expected pattern]
- 30d: [Long-term outlook based on news]

CRITICAL FORMATTING RULES:
- Extract ACTUAL numbers from dataset
- Use symbols: ✓ ! ✗ ↑ → ↓
- NO explanations beyond format
- Tables MUST use EXACT column widths as specified above
- ALIGN all pipe characters (|) vertically in EVERY row
- PAD all values with spaces to match column width EXACTLY
- RIGHT-align numeric values, CENTER-align status/assessment text
- Use consistent spacing in EVERY row
- 1 sentence per insight MAX
- Include change calculations (current vs previous)
- Show percentage changes where relevant

At the beginning of your response, provide your internal reasoning trace inside a <think> block, then provide the final analysis.

DO NOT CREATE MISALIGNED TABLES - Every pipe character MUST line up vertically!
"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=self.generation_config
            )
            full_text = response.text
            
            import re
            think_match = re.search(r'<think>(.*?)</think>', full_text, re.DOTALL)
            thought = think_match.group(1).strip() if think_match else "Performing multi-dimensional analysis..."
            result = re.sub(r'<think>.*?</think>', '', full_text, flags=re.DOTALL).strip()
            
            return True, result, thought
        except Exception as e:
            return False, f"Error during analysis: {str(e)}", ""

class NewsFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
        
    def fetch_air_quality_news(self, query="air quality pollution", max_results=5): 
        try:
            params = {
                'q': query,
                'apiKey': self.api_key,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': max_results
            }
            response = requests.get(self.base_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                return True, articles
            else:
                return False, f"API error: {response.status_code}"
        except Exception as e:
            return False, f"Error fetching news: {str(e)}"
            
    def format_news_for_analysis(self, articles):
        if not articles:
            return "No recent news articles found."
        formatted_news = []
        formatted_news.append(f"Recent Air Quality News ({len(articles)} articles):\n")
        for idx, article in enumerate(articles, 1):
            title = article.get('title', 'No title')
            description = article.get('description', 'No description')
            source = article.get('source', {}).get('name', 'Unknown source')
            published_at = article.get('publishedAt', 'Unknown date')
            formatted_news.append(f"{idx}. {title}")
            formatted_news.append(f"   Source: {source} | Published: {published_at}")
            formatted_news.append(f"   Summary: {description}")
            formatted_news.append("")
        return "\n".join(formatted_news)

class DataVisualizer:
    def __init__(self, data_processor):
        self.processor = data_processor
        self.data = None
        self.cleaned_data = None
        self.numeric_columns = []
        
    def _detect_numeric_columns(self):
        if self.data is None:
            return []
        numeric_cols = []
        for col in self.data.columns:
            if pd.api.types.is_numeric_dtype(self.data[col]):
                numeric_cols.append(col)
            else:
                try:
                    pd.to_numeric(self.data[col], errors='raise')
                    numeric_cols.append(col)
                except (ValueError, TypeError):
                    continue
        exclude_patterns = ['id', 'index', 'year', 'month', 'day', 'hour', 'minute', 'second',
                           'timestamp', 'time', 'date', 'latitude', 'longitude', 'lat', 'lon', 'lng']
        filtered_cols = []
        for col in numeric_cols:
            col_lower = col.lower()
            if not any(pattern in col_lower for pattern in exclude_patterns):
                filtered_cols.append(col)
        return filtered_cols

    def clean_data(self):
        if self.processor.data is None:
            return False, "No data loaded"
        try:
            self.data = self.processor.data.copy()
            self.numeric_columns = self._detect_numeric_columns()
            if not self.numeric_columns:
                return False, "No numeric columns found for visualization"
            
            self.cleaned_data = self.data.copy()
            for col in self.numeric_columns:
                self.cleaned_data[col] = pd.to_numeric(self.cleaned_data[col], errors='coerce')
            self.cleaned_data = self.cleaned_data.dropna(subset=self.numeric_columns, how='all')
            
            if len(self.cleaned_data) == 0:
                return False, "No valid data after cleaning"
            return True, "Data cleaned successfully"
        except Exception as e:
            return False, f"Error cleaning data: {str(e)}"
            
    def _fig_to_base64(self, fig):
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches='tight', facecolor='#0c0c0c', edgecolor='none')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return img_str

    def create_line_chart(self):
        if self.cleaned_data is None:
            return False, None

        columns_with_data = [col for col in self.numeric_columns if col in self.cleaned_data.columns and len(self.cleaned_data[col].dropna()) > 0]
        if not columns_with_data:
            return False, None
            
        fig = plt.figure(figsize=(10, 5))

        plt.rcParams['text.color'] = '#00ff41'
        plt.rcParams['axes.labelcolor'] = '#00ff41'
        plt.rcParams['xtick.color'] = '#00ff41'
        plt.rcParams['ytick.color'] = '#00ff41'
        plt.rcParams['axes.edgecolor'] = '#00ff41'
        fig.patch.set_facecolor('#0c0c0c')
        plt.gca().set_facecolor('#0c0c0c')
        
        colors = ['#00ff41', '#58a6ff', '#f1e05a', '#ea4aaa', '#b392f0']
        for idx, col in enumerate(columns_with_data[:5]): 
            data = self.cleaned_data[col].dropna()
            plt.plot(range(len(data)), data, marker='o', linewidth=2, markersize=3,
                    color=colors[idx % len(colors)], label=col, alpha=0.8)
                    
        plt.title('Air Quality Trend Over Time', fontsize=12, fontweight='bold', color='#00ff41')
        plt.xlabel('Time Period', fontsize=10)
        plt.ylabel('Value', fontsize=10)
        legend = plt.legend(loc='best', fontsize=8, facecolor='#0c0c0c', edgecolor='#00ff41')
        plt.grid(True, alpha=0.2, color='#00ff41')
        plt.tight_layout()
        
        return True, self._fig_to_base64(fig)

    def create_bar_chart(self):
        if self.cleaned_data is None:
            return False, None
        try:
            latest_values = {}
            for col in self.numeric_columns:
                if col in self.cleaned_data.columns:
                    valid_data = self.cleaned_data[col].dropna()
                    if len(valid_data) > 0:
                        latest_values[col] = valid_data.iloc[-1]
            if not latest_values:
                return False, None
                
            fig = plt.figure(figsize=(max(12, len(latest_values) * 1.2), 6))
            plt.rcParams['text.color'] = '#00ff41'
            plt.rcParams['axes.labelcolor'] = '#00ff41'
            plt.rcParams['xtick.color'] = '#00ff41'
            plt.rcParams['ytick.color'] = '#00ff41'
            plt.rcParams['axes.edgecolor'] = '#00ff41'
            fig.patch.set_facecolor('#0c0c0c')
            plt.gca().set_facecolor('#0c0c0c')
            
            colors = ['#ea4aaa', '#f1e05a', '#ff5555', '#62b7ec', '#00ff41', '#b392f0']
            bars = plt.bar(latest_values.keys(), latest_values.values(),
                          color=[colors[i % len(colors)] for i in range(len(latest_values))], alpha=0.8)
            plt.title('Current Air Quality Metrics Comparison', fontsize=12, fontweight='bold', color='#00ff41')
            plt.xlabel('Metric', fontsize=10)
            plt.ylabel('Value', fontsize=10)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.2, color='#00ff41', axis='y')
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}',
                        ha='center', va='bottom', fontsize=9, color='#00ff41')
            plt.tight_layout()
            return True, self._fig_to_base64(fig)
        except Exception as e:
            return False, None

    def create_histogram(self):
        if self.cleaned_data is None:
            return False, None
        try:
            columns_with_data = []
            for col in self.numeric_columns:
                if col in self.cleaned_data.columns and len(self.cleaned_data[col].dropna()) > 1:
                    columns_with_data.append(col)
            if not columns_with_data:
                return False, None
                
            num_plots = len(columns_with_data)
            if num_plots == 1:
                fig, axes = plt.subplots(1, 1, figsize=(10, 5))
                axes = [axes]
            elif num_plots == 2:
                fig, axes = plt.subplots(1, 2, figsize=(12, 5))
                axes = axes.flatten()
            elif num_plots <= 4:
                fig, axes = plt.subplots(2, 2, figsize=(12, 8))
                axes = axes.flatten()
            elif num_plots <= 6:
                fig, axes = plt.subplots(2, 3, figsize=(14, 8))
                axes = axes.flatten()
            elif num_plots <= 9:
                fig, axes = plt.subplots(3, 3, figsize=(14, 10))
                axes = axes.flatten()
            else:
                rows = (num_plots + 2) // 3
                fig, axes = plt.subplots(rows, 3, figsize=(14, 4*rows))
                axes = axes.flatten()
                
            plt.rcParams['text.color'] = '#00ff41'
            plt.rcParams['axes.labelcolor'] = '#00ff41'
            plt.rcParams['xtick.color'] = '#00ff41'
            plt.rcParams['ytick.color'] = '#00ff41'
            plt.rcParams['axes.edgecolor'] = '#00ff41'
            fig.patch.set_facecolor('#0c0c0c')
            
            colors = ['#62b7ec', '#00ff41', '#ea4aaa', '#f1e05a', '#ff5555', '#b392f0']
            for idx, col in enumerate(columns_with_data):
                data = self.cleaned_data[col].dropna()
                ax = axes[idx]
                ax.set_facecolor('#0c0c0c')
                ax.hist(data, bins=min(20, max(5, len(data)//3)), color=colors[idx % len(colors)],
                       edgecolor='#0c0c0c', alpha=0.8)
                ax.set_title(f'{col} Distribution', fontsize=10, fontweight='bold', color='#00ff41')
                ax.set_xlabel(f'{col} Value Range', fontsize=8)
                ax.set_ylabel('Frequency', fontsize=8)
                ax.grid(True, alpha=0.2, color='#00ff41', axis='y')
                mean_val = data.mean()
                median_val = data.median()
                ax.axvline(x=mean_val, color='#ff5555', linestyle='--', linewidth=1.5,
                          label=f'Mean: {mean_val:.1f}')
                ax.axvline(x=median_val, color='#58a6ff', linestyle='--', linewidth=1.5,
                          label=f'Median: {median_val:.1f}')
                ax.legend(fontsize=7, facecolor='#0c0c0c', edgecolor='#00ff41')
                
            for idx in range(num_plots, len(axes)):
                fig.delaxes(axes[idx])
                
            plt.suptitle('Air Quality Data Distribution Analysis', fontsize=12, fontweight='bold', y=0.995, color='#00ff41')
            plt.tight_layout()
            return True, self._fig_to_base64(fig)
        except Exception as e:
            return False, None

    def generate_visualizations(self):
        clean_success, msg = self.clean_data()
        if not clean_success:
            return False, {}, msg
            
        charts = {}
        l_success, l_img = self.create_line_chart()
        if l_success: charts['line_chart'] = l_img
            
        b_success, b_img = self.create_bar_chart()
        if b_success: charts['bar_chart'] = b_img
            
        h_success, h_img = self.create_histogram()
        if h_success: charts['histogram'] = h_img
            
        return True, charts, "Visualizations generated"


@app.route('/api/analyze', methods=['POST'])
def analyze():
    api_key = request.form.get('api_key')
    if not api_key:
        return jsonify({'error': 'Gemini API Key is required'}), 400
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400


    is_valid, msg = CSVValidator.validate_file(file)
    if not is_valid:
        return jsonify({'error': msg}), 400
        

    file.seek(0)
    processor = DataProcessor(file)
    success, msg = processor.load_data()
    if not success:
        return jsonify({'error': msg}), 400
        
    data_summary = processor.get_data_as_text()
    

    analyzer = GeminiAnalyzer(api_key)
    is_aq, ai_response, verification_thought = analyzer.verify_air_quality_data(data_summary)
    
    if not is_aq:
        if "Error during verification:" in ai_response:

            status_code = 429 if "429" in ai_response or "exhausted" in ai_response.lower() else 500
            return jsonify({'error': 'AI Verification Failed', 'details': ai_response}), status_code
            
        return jsonify({
            'analysis': f"AI Validation Result:\n{ai_response}\n\nTerminating analysis early since the dataset is not relevant.",
            'charts': {},
            'articles': [],
            'thought': verification_thought
        })

        

    news_fetcher = NewsFetcher(NEWS_API_KEY)
    news_success, news_data = news_fetcher.fetch_air_quality_news()
    if news_success:
        news_context = news_fetcher.format_news_for_analysis(news_data)
    else:
        news_context = "No recent news available for context."
        

    analysis_success, analysis_result, analysis_thought = analyzer.analyze_air_quality_data(data_summary, news_context)
    if not analysis_success:
        status_code = 429 if "429" in analysis_result or "exhausted" in analysis_result.lower() else 500
        return jsonify({'error': 'Gemini Analysis Failed', 'details': analysis_result}), status_code

        

    visualizer = DataVisualizer(processor)
    viz_success, charts, viz_msg = visualizer.generate_visualizations()
    
    return jsonify({
        'analysis': analysis_result,
        'charts': charts,
        'articles': news_data if news_success else [],
        'thought': f"[ DATA RELEVANCY VERIFICATION ]\n{verification_thought}\n\n[ COMPREHENSIVE DATA ANALYSIS ]\n{analysis_thought}"
    })

if __name__ == '__main__':
    print("Starting AirSense API Backend on port 5000...")
    app.run(debug=True, port=5000)

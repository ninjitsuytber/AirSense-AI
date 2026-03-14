import os
import asyncio
import base64
import pandas as pd
import requests
from datetime import datetime, timedelta
from google import genai
from google.genai import types
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from io import BytesIO

# Import modules from new structure
from agents.gemini_agent import GeminiAnalyzer
from tools.news_tool import NewsFetcher
from tools.data_tool import DataProcessor, DataVisualizer, CSVValidator

app = Flask(__name__, static_folder='app')
CORS(app)

NEWS_API_KEY = "edbbebf8b6d84782b800f68e4706d5cd"

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

async def run_airsense_analysis(api_key, file):
    analyzer = GeminiAnalyzer(api_key)
    
    file.seek(0)
    processor = DataProcessor(file)
    processor.load_data()
    data_summary = processor.get_data_as_text()
    
    is_aq, verify_response, verify_thought = analyzer.verify_air_quality_data(data_summary)
    
    if not is_aq:
        if "Error during verification:" in verify_response:
            status_code = 429 if "429" in verify_response or "exhausted" in verify_response.lower() else 500
            return {'error': 'AI Verification Failed', 'details': verify_response}, status_code
            
        return {
            'analysis': f"AI Validation Result:\n{verify_response}\n\nTerminating analysis early since the dataset is not relevant.",
            'charts': {},
            'articles': [],
            'thought': verify_thought
        }, 200

    airsense_agent = Agent(
        name="AirSenseReporter",
        instruction="Evaluate air quality data and provide a comprehensive multidimensional report.",
        model="gemini-2.0-flash" 
    )
    
    news_fetcher = NewsFetcher(NEWS_API_KEY)
    news_success, news_data = news_fetcher.fetch_air_quality_news()
    news_context = news_fetcher.format_news_for_analysis(news_data) if news_success else "No recent news available."
    
    analysis_success, analysis_result, analysis_thought = analyzer.analyze_air_quality_data(data_summary, news_context)
    if not analysis_success:
        status_code = 429 if "429" in analysis_result or "exhausted" in analysis_result.lower() else 500
        return {'error': 'Analysis Error', 'details': analysis_result}, status_code
        
    visualizer = DataVisualizer(processor)
    viz_success, charts, viz_msg = visualizer.generate_visualizations()
    
    return {
        'analysis': analysis_result,
        'charts': charts,
        'articles': news_data if news_success else [],
        'thought': f"[ DATA RELEVANCY VERIFICATION ]\n{verify_thought}\n\n[ AIRSENSE AGENTIC REASONING ]\n{analysis_thought}"
    }, 200

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

    os.environ["GOOGLE_API_KEY"] = api_key

    result, status_code = asyncio.run(run_airsense_analysis(api_key, file))
    return jsonify(result), status_code

if __name__ == '__main__':
    print("Starting AirSense API Backend (Google ADK Integrated) on port 5000...")
    app.run(debug=True, port=5000)

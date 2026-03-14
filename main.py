import os
import re
import pandas as pd
from io import BytesIO
from flask import Flask, request, jsonify
from flask_cors import CORS


from agents.main_agent import create_airsense_agent
from tools.air_tools import fetch_environmental_news, generate_visualizations

app = Flask(__name__, static_folder='app', static_url_path='')
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/analyze', methods=['POST'])
async def analyze():
    user_token = request.form.get('user_token')
    if user_token:
        print(f"Authenticated request received from token: {user_token[:10]}...")
    
    api_key = request.form.get('api_key')
    if not api_key:
        return jsonify({'error': 'Gemini API Key is required'}), 400
        
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    file_bytes = file.read()
    

    agent = create_airsense_agent(api_key)
    

    try:
        df = pd.read_csv(BytesIO(file_bytes))
        data_summary = f"Columns: {list(df.columns)}\nRows: {len(df)}\nSample:\n{df.head(5).to_string()}"
        df_json = df.to_json()
    except Exception as e:
        return jsonify({'error': f"Failed to parse CSV: {str(e)}"}), 400

    user_query = f"Analyze this air quality dataset: {data_summary}. The full data is available for tools."
    
    try:

        response = await agent.run(user_query)
        

        if "INVALID" in response.text.upper():
             return jsonify({
                'analysis': response.text,
                'charts': {},
                'articles': [],
                'thought': "Agent determined data is invalid."
            })


        articles = fetch_environmental_news()
        

        charts = generate_visualizations(df_json)
        

        think_match = re.search(r'<think>(.*?)</think>', response.text, re.DOTALL)
        thought = think_match.group(1).strip() if think_match else "Agent analyzing data..."
        analysis_result = re.sub(r'<think>.*?</think>', '', response.text, flags=re.DOTALL).strip()

        return jsonify({
            'analysis': analysis_result,
            'charts': charts,
            'articles': articles,
            'thought': thought
        })

    except Exception as e:
        return jsonify({'error': f"ADK Agent Error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting AirSense ADK-Powered Backend on port {port}...")
    app.run(debug=True, port=port, host='0.0.0.0')

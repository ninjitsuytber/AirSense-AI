# AirSense AI

   AirSense AI is a next-generation environmental analysis platform powered by the **Google Agent Development Kit (ADK)** and Gemini 2.5 Flash. It utilizes a sophisticated agentic workflow to interpret air quality data, fetch real-time context via modular tools, and provide actionable health insights through an interactive terminal.

## System Architecture

   ```mermaid
   graph TD
      subgraph UserSpace ["User Space"]
         User([User]) <-->|Input/Visuals| App[App Terminal: /app]
      end

      subgraph BackendSpace ["Analysis Agents: /agents"]
         App <-->|POST /api/analyze| Server[Flask Server: server.py]
         
         subgraph AgentCore ["Agentic Reasoning"]
               Server --> Verifier[Relevancy Verifier Agent]
               Server --> Expert[Analysis Expert Agent]
               Server --> Plotter[Visualizer Agent]
         end
      end

      subgraph ToolSpace ["Modular Tools: /tools"]
         Server --> NewsTool[News Fetcher Tool]
      end

      subgraph ExternalProvider ["External APIs / Infrastructure"]
         Verifier & Expert -.->|Google AI Python ADK| Gemini[Gemini 2.5 Flash]
         NewsTool -.->|HTTP requests| NewsAPI[NewsAPI.org]
         Server -.->|Matplotlib / Pandas| Visuals[Data Processing Layer]
      end
   ```

## Google ADK & Agentic Architecture

   This project is built from the ground up to showcase the power of the **Google AI Python ADK**. The core architecture centers on an autonomous agentic loop:

- **Agentic Loop**: Built using the `google-genai` SDK, our agents perform multi-step reasoning (ReAct pattern) to validate, analyze, and predict air quality trends.
- **Thinking Logs**: Every AI response includes a `<think>` block, exposing the internal reasoning trace of the Google ADK agents for full transparency.
- **Modular Tools**: We've implemented a tool-calling pattern compatible with the ADK framework, abstracting external services like NewsAPI into dedicated modules in `/tools`.
- **System Robustness**: Leverages the ADK's safety guardrails and system instructions to ensure professional, accurate environmental reporting.

## Agent Profiles

   AirSense AI utilizes a multi-agentic approach to ensure data accuracy and helpful insights:

   1. **Relevancy Verifier Agent**: Strictly validates uploaded CSV data to ensure it contains air quality metrics. It provides an internal reasoning trace (<think> block) explaining why the data is accepted or rejected.
   2. **Analysis Expert Agent**: Interprets complex pollutant levels (AQI, PM2.5, NO2, etc.) and provides health-focused, tabulated reports. It compares real-time data against WHO/EPA standards and incorporates news context for long-term outlooks.
   3. **Data Visualization Agent**: Automatically detects numeric pollution patterns and generates dynamic trend charts, distribution histograms, and comparison bars using Matplotlib.

### Project Structure

- **/agents**: Core logic and backend server.
- `server.py`: Flask-based analysis engine.
- **/tools**: MCP-style modular tools.
- `news_tool.py`: Real-time environmental news fetcher.
- **/app**: Frontend interactive terminal.
- `index.html`, `style.css`, `script.js`: Terminal interface and UI logic.
- `requirements.txt`: Project dependencies.
- `README.md`: Documentation and setup.

## Prerequisites

### Backend Dependencies

- **python (3.8+)**: Core runtime.
- **flask / flask-cors**: API server and cross-origin support.
- **pandas**: High-performance data manipulation.
- **requests**: Synchronous HTTP library for tool integration.
- **google-genai**: The official Google AI SDK for ADK integration.
- **matplotlib**: Automated visualization generation.
- **gunicorn**: Production-grade WSGI server.

### APIs

- Google Gemini API Key (obtainable from Google AI Studio)
- NewsAPI Key (integrated in server.py)

## Installation and Setup

### 1. Backend Setup

   1. Install the required Python packages:
      pip install -r requirements.txt
   2. Start the Flask server:
      python agents/server.py
      The server will run on <http://localhost:5000> by default.

### 2. Frontend Setup

   1. Simply open app/index.html in any modern web browser.
   2. Ensure the backend server is running to use the analysis features.

## How to Use

   1. Initial Setup: Type 'help' to see available commands or 'airsense' to start the analysis tool.
   2. API Key: If it is your first time using the tool, you will be prompted to enter your Google Gemini API key. This key is saved in your browser's local storage for future sessions.
   3. Upload Data: Select 'Upload CSV file' and choose a valid CSV containing air quality metrics (e.g., AQI, PM2.5, PM10, CO).
   4. Review Results: The AI will validate the data, provide a tabulated analysis, generate trend charts, and list related environmental news.

## Features

- Interactive Terminal: A fully functional command-line interface simulation written in vanilla JavaScript.
- AI Analysis: Uses Gemini 2.5 Flash to interpret complex pollutants and provide health insights.
- Dynamic Visualizations: Automatically generates line charts, bar charts, and histograms based on the uploaded dataset.
- Real-time News: Pulls relevant air quality news to provide context for the analyzed data.
- API Key Persistence: Securely saves the user's API key in local storage and includes error handling for exhausted or invalid keys.
- Mobile Responsive: Optimized for mobile viewing

## Limitations

- **Free Tier Constraints**: Since the backend is currently hosted on the free Render tier, it can only handle lightweight CSV files. Large datasets may cause timeouts or performance issues.

## Deployment Guide

### Frontend Deployment (Netlify)

   1. Connect your GitHub repository to Netlify.
   2. The `netlify.toml` automatically sets the build folder to `/app`.
   3. Set your Production Backend URL in `app/script.js`.

### Backend Deployment (Render / Cloud Run)

   1. Deploy the contents of the project to a platform that supports Python (like Render.com).
   2. Set the Start Command to: `gunicorn agents.server:app`
   3. Ensure all environment variables and dependencies in `requirements.txt` are satisfied.

## Troubleshooting

- Connection Error: Ensure the Flask server (server.py) is running on port 5000 and accessible from your browser.
- Quota Exhausted: If you receive a 429 error, the Gemini API free tier limit may have been reached. Use the 'airsense' command again to enter a new API key.
- Invalid CSV: Ensure your CSV file contains numeric data and clear headers related to air quality or pollutants.

---

**Author**: [Stephen Sii](https://stephensii.netlify.app/) from [Latton Lab](https://lattonlab.netlify.app/)

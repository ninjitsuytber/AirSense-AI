from adk import LlmAgent
from adk.models import GeminiModel
from tools.air_tools import validate_csv, fetch_environmental_news, generate_visualizations

def create_airsense_agent(api_key):

    safety_settings = [
        {"category": "HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    model = GeminiModel(
        model_name="gemini-2.0-flash", 
        api_key=api_key,
        safety_settings=safety_settings
    )
    
    agent = LlmAgent(
        name="AirSenseAgent",
        instructions="""
        You are an expert Air Quality Analyst. 
        Your goal is to process CSV data, verify its relevancy to air quality, and provide a detailed analysis.
        
        WORKFLOW:
        1. Verify if the data is air quality related.
        2. If valid, fetch relevant news context.
        3. Analyze the data metrics against WHO/EPA standards.
        4. Generate a tabulated report.
        5. Request visualizations if numeric data is available.
        
        AGENTIC RECOVERY:
        If a tool fails (returns a "Tool Error" string), note the failure in your <think> block 
        and attempt to proceed with the analysis using the available data, explaining the 
        limitation to the user in your final response.
        
        Respond with your thinking trace in a <think> block first.
        """,
        tools=[validate_csv, fetch_environmental_news, generate_visualizations],
        model=model
    )
    return agent

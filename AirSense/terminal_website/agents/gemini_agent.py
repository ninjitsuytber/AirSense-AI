from google import genai
from google.genai import types

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
                model="gemini-2.0-flash",
                contents=prompt,
                config=self.generation_config
            )
            full_text = response.text.strip()
            
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
                model="gemini-2.0-flash",
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

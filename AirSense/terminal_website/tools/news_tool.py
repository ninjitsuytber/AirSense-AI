import requests

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

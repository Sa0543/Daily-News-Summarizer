# backend/news_scraper.py
import feedparser
from newspaper import Article
from datetime import datetime
import time

class NewsScraper:
    def __init__(self):
        # Keep the category feeds similar to your streamlit version
        self.category_feeds = {
            'General': [
                'http://rss.cnn.com/rss/cnn_topstories.rss',
                'http://feeds.bbci.co.uk/news/rss.xml',
                'https://timesofindia.indiatimes.com/rssfeedstopstories.cms',
            ],
            'Politics': [
                'https://indianexpress.com/section/politics/feed/',
                'https://www.thehindu.com/news/national/feeder/default.rss',
                'http://feeds.reuters.com/Reuters/PoliticsNews',
            ],
            'Sports': [
                'https://timesofindia.indiatimes.com/rssfeeds/4719148.cms',
                'https://indianexpress.com/section/sports/feed/',
                'http://feeds.bbci.co.uk/sport/rss.xml',
            ],
            'Business': [
                'https://economictimes.indiatimes.com/rssfeedstopstories.cms',
                'https://indianexpress.com/section/business/feed/',
                'http://feeds.reuters.com/reuters/businessNews',
            ],
            'Technology': [
                'https://timesofindia.indiatimes.com/rssfeeds/66949542.cms',
                'https://indianexpress.com/section/technology/feed/',
                'http://feeds.reuters.com/reuters/technologyNews',
            ],
            'Education': [
                'https://timesofindia.indiatimes.com/rssfeeds/913168846.cms',
                'https://indianexpress.com/section/education/feed/',
                'https://www.thehindu.com/news/national/feeder/default.rss',
            ],
            'Entertainment': [
                'https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms',
                'https://indianexpress.com/section/entertainment/feed/',
                'http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml',
            ],
            'International': [
                'http://feeds.reuters.com/Reuters/worldNews',
                'https://www.thehindu.com/news/international/feeder/default.rss',
                'http://feeds.bbci.co.uk/news/world/rss.xml',
            ],
            'Health': [
                'https://timesofindia.indiatimes.com/rssfeeds/3908999.cms',
                'https://indianexpress.com/section/lifestyle/health/feed/',
                'http://feeds.reuters.com/reuters/health',
            ]
        }

    def fetch_rss_news(self, max_articles=30, categories=None):
        articles = []
        if categories is None:
            categories = list(self.category_feeds.keys())

        articles_per_category = max(1, max_articles // len(categories))

        for category in categories:
            if category not in self.category_feeds:
                continue
            feeds = self.category_feeds[category]
            category_articles = 0
            for feed_url in feeds:
                if category_articles >= articles_per_category:
                    break
                try:
                    feed = feedparser.parse(feed_url)
                    source_name = feed.feed.get('title', category)
                    for entry in feed.entries[:5]:
                        if category_articles >= articles_per_category:
                            break
                        article_data = {
                            'title': entry.get('title', 'No title'),
                            'url': entry.get('link', ''),
                            'source': source_name,
                            'category': category,
                            'published': entry.get('published', str(datetime.now())),
                            'description': entry.get('summary', '')
                        }
                        # fetch full content with newspaper3k
                        try:
                            article = Article(article_data['url'])
                            article.download()
                            article.parse()
                            article_data['content'] = article.text
                            article_data['image'] = article.top_image
                        except Exception:
                            article_data['content'] = article_data['description']
                            article_data['image'] = None

                        if article_data['content']:
                            articles.append(article_data)
                            category_articles += 1

                        time.sleep(0.2)
                except Exception as e:
                    print(f"Feed read error {feed_url}: {e}")
                    continue

        return articles[:max_articles]

    def get_available_categories(self):
        return list(self.category_feeds.keys())
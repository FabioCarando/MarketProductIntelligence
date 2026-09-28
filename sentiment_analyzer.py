# -*- coding: utf-8 -*-
"""
Sentiment Analysis for Amazon Reviews
Analizza il sentiment delle review estratte
"""

import json
import logging
from pathlib import Path
from textblob import TextBlob
from typing import Dict, List, Any
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment of product reviews"""
    
    def __init__(self, reviews_file: str = "reviews.json", output_file: str = "reviews_with_sentiment.json"):
        self.reviews_file = reviews_file
        self.output_file = output_file
        self.reviews = []
        self.sentiment_results = []
        
    def load_reviews(self) -> bool:
        """Load reviews from JSON file"""
        try:
            with open(self.reviews_file, 'r', encoding='utf-8') as f:
                self.reviews = json.load(f)
            logger.info(f"Loaded {len(self.reviews)} reviews from {self.reviews_file}")
            return True
        except FileNotFoundError:
            logger.error(f"Reviews file not found: {self.reviews_file}")
            return False
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {self.reviews_file}")
            return False
    
    def _get_sentiment_label(self, polarity: float) -> str:
        """Classify sentiment based on polarity score"""
        if polarity > 0.1:
            return "POSITIVE"
        elif polarity < -0.1:
            return "NEGATIVE"
        else:
            return "NEUTRAL"
    
    def _extract_review_text(self, review: Dict[str, Any]) -> str:
        """Extract review text from review dict"""
        # Try to get text from review
        text = review.get('text', '').strip()
        if not text:
            # Fallback to title if text is empty
            text = review.get('title', '').strip()
        
        # If still empty, use helpful_count as proxy (meta-sentiment)
        if not text:
            helpful = review.get('helpful_count', 0)
            if helpful > 10:
                text = "Very helpful review"
            elif helpful > 5:
                text = "Helpful review"
            elif helpful > 0:
                text = "Somewhat helpful review"
            else:
                text = "Review"
        
        return text
    
    def analyze_sentiment(self) -> bool:
        """Analyze sentiment for all reviews"""
        if not self.reviews:
            logger.error("No reviews loaded")
            return False
        
        logger.info(f"Analyzing sentiment for {len(self.reviews)} reviews...")
        
        for idx, review in enumerate(self.reviews):
            try:
                # Extract review text
                review_text = self._extract_review_text(review)
                
                # Perform sentiment analysis using TextBlob
                blob = TextBlob(review_text)
                polarity = blob.sentiment.polarity  # -1 to 1
                subjectivity = blob.sentiment.subjectivity  # 0 to 1
                
                # Classify sentiment
                sentiment_label = self._get_sentiment_label(polarity)
                
                # Create result dict
                result = {
                    **review,
                    'review_text': review_text,
                    'polarity': round(polarity, 3),
                    'subjectivity': round(subjectivity, 3),
                    'sentiment': sentiment_label,
                    'analysis_date': datetime.now().isoformat()
                }
                
                self.sentiment_results.append(result)
                
                if (idx + 1) % 5 == 0:
                    logger.info(f"Analyzed {idx + 1}/{len(self.reviews)} reviews")
                    
            except Exception as e:
                logger.error(f"Error analyzing review {idx}: {str(e)}")
                continue
        
        logger.info(f"Sentiment analysis complete for {len(self.sentiment_results)} reviews")
        return True
    
    def save_results(self) -> bool:
        """Save sentiment analysis results to JSON"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.sentiment_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.sentiment_results)} results to {self.output_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate sentiment analysis report"""
        if not self.sentiment_results:
            logger.error("No results to report")
            return {}
        
        # Count sentiments
        positive = sum(1 for r in self.sentiment_results if r['sentiment'] == 'POSITIVE')
        negative = sum(1 for r in self.sentiment_results if r['sentiment'] == 'NEGATIVE')
        neutral = sum(1 for r in self.sentiment_results if r['sentiment'] == 'NEUTRAL')
        
        # Calculate average scores
        avg_polarity = sum(r['polarity'] for r in self.sentiment_results) / len(self.sentiment_results)
        avg_subjectivity = sum(r['subjectivity'] for r in self.sentiment_results) / len(self.sentiment_results)
        
        # Group by product
        by_product = {}
        for result in self.sentiment_results:
            product = result.get('product_id', 'Unknown')
            if product not in by_product:
                by_product[product] = {'positive': 0, 'negative': 0, 'neutral': 0, 'count': 0, 'avg_polarity': 0}
            by_product[product]['count'] += 1
            by_product[product][result['sentiment'].lower()] += 1
            by_product[product]['avg_polarity'] += result['polarity']
        
        # Calculate avg polarity per product
        for product in by_product:
            by_product[product]['avg_polarity'] = round(by_product[product]['avg_polarity'] / by_product[product]['count'], 3)
        
        report = {
            'total_reviews': len(self.sentiment_results),
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'positive_percentage': round(100 * positive / len(self.sentiment_results), 1),
            'negative_percentage': round(100 * negative / len(self.sentiment_results), 1),
            'neutral_percentage': round(100 * neutral / len(self.sentiment_results), 1),
            'average_polarity': round(avg_polarity, 3),
            'average_subjectivity': round(avg_subjectivity, 3),
            'by_product': by_product,
            'analysis_date': datetime.now().isoformat()
        }
        
        return report
    
    def print_report(self):
        """Print sentiment report to console"""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("SENTIMENT ANALYSIS REPORT")
        print("="*60)
        print(f"Total Reviews: {report['total_reviews']}")
        print(f"\nSentiment Breakdown:")
        print(f"  POSITIVE: {report['positive_count']} ({report['positive_percentage']}%)")
        print(f"  NEGATIVE: {report['negative_count']} ({report['negative_percentage']}%)")
        print(f"  NEUTRAL:  {report['neutral_count']} ({report['neutral_percentage']}%)")
        print(f"\nAverage Scores:")
        print(f"  Polarity: {report['average_polarity']} (-1 to 1, higher = more positive)")
        print(f"  Subjectivity: {report['average_subjectivity']} (0 to 1, higher = more subjective)")
        print(f"\nBy Product:")
        for product, data in report['by_product'].items():
            print(f"\n  {product[:50]}")
            print(f"    Total: {data['count']}")
            print(f"    Avg Polarity: {data['avg_polarity']}")
            print(f"    Positive: {data['positive']}, Negative: {data['negative']}, Neutral: {data['neutral']}")
        print("\n" + "="*60)
    
    def save_report(self, report_file: str = "sentiment_report.json") -> bool:
        """Save report to JSON file"""
        try:
            report = self.generate_report()
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved report to {report_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            return False
    
    def run(self):
        """Run full sentiment analysis pipeline"""
        if not self.load_reviews():
            return False
        
        if not self.analyze_sentiment():
            return False
        
        if not self.save_results():
            return False
        
        if not self.save_report():
            return False
        
        self.print_report()
        return True


if __name__ == "__main__":
    analyzer = SentimentAnalyzer(
        reviews_file="reviews.json",
        output_file="reviews_with_sentiment.json"
    )
    analyzer.run()
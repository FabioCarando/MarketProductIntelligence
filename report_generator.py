# -*- coding: utf-8 -*-
"""
Excel Report Generator for Competitive Analysis
Genera report in 4 sheet con dati di prodotti e sentiment analysis
"""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict, Counter
import re

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("ERROR: openpyxl not installed. Run: pip install openpyxl")
    exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates competitive analysis report in Excel"""
    
    def __init__(self, products_file="products.json", reviews_file="reviews_with_sentiment.json"):
        self.products_file = products_file
        self.reviews_file = reviews_file
        self.products = []
        self.reviews = []
        self.workbook = Workbook()
        self.workbook.remove(self.workbook.active)  # Remove default sheet
        
    def load_data(self) -> bool:
        """Load products and reviews data"""
        try:
            with open(self.products_file, 'r', encoding='utf-8') as f:
                self.products = json.load(f)
            logger.info(f"Loaded {len(self.products)} products")
            
            with open(self.reviews_file, 'r', encoding='utf-8') as f:
                self.reviews = json.load(f)
            logger.info(f"Loaded {len(self.reviews)} reviews")
            
            return True
        except FileNotFoundError as e:
            logger.error(f"File not found: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {str(e)}")
            return False
    
    def _get_style_header(self):
        """Get header style"""
        return {
            'fill': PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid"),
            'font': Font(bold=True, color="FFFFFF", size=11),
            'alignment': Alignment(horizontal="center", vertical="center", wrap_text=True),
            'border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
        }
    
    def _get_style_data(self):
        """Get data cell style"""
        return {
            'alignment': Alignment(horizontal="left", vertical="center", wrap_text=True),
            'border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
        }
    
    def _apply_style(self, cell, style_dict):
        """Apply style to cell"""
        for attr, value in style_dict.items():
            setattr(cell, attr, value)
    
    def generate_sheet1_competitive_analysis(self):
        """Sheet 1: Competitive Analysis - min/max/media per covariate"""
        ws = self.workbook.create_sheet("Analisi Competitiva")
        logger.info("Generating Sheet 1: Competitive Analysis")
        
        # Headers
        headers = ["Covariate", "Min", "Max", "Media", "Prodotti Analizzati"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            self._apply_style(cell, self._get_style_header())
        
        # Extract metrics
        covariates = {
            'potenza_w': [],
            'kg': [],
            'serbatoio_ml': [],
            'cavo_cm': [],
            'price_eur': []
        }
        
        for product in self.products:
            for key in covariates.keys():
                val = product.get(key)
                if val and isinstance(val, (int, float)) and val > 0:
                    covariates[key].append(val)
        
        # Calculate and write stats
        row = 2
        for covariate, values in covariates.items():
            if values:
                min_val = min(values)
                max_val = max(values)
                avg_val = sum(values) / len(values)
                
                ws.cell(row=row, column=1, value=covariate.replace('_', ' ').title())
                ws.cell(row=row, column=2, value=round(min_val, 2))
                ws.cell(row=row, column=3, value=round(max_val, 2))
                ws.cell(row=row, column=4, value=round(avg_val, 2))
                ws.cell(row=row, column=5, value=len(values))
                
                for col in range(1, 6):
                    self._apply_style(ws.cell(row=row, column=col), self._get_style_data())
                
                row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 18
    
    def generate_sheet2_sentiment_summary(self):
        """Sheet 2: Sentiment Summary - ranking prodotti per sentiment"""
        ws = self.workbook.create_sheet("Sentiment Summary")
        logger.info("Generating Sheet 2: Sentiment Summary")
        
        # Headers
        headers = ["Prodotto", "Review Count", "Avg Rating", "Polarity", "Sentiment", "Positive %", "Negative %"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            self._apply_style(cell, self._get_style_header())
        
        # Aggregate reviews by product
        product_reviews = defaultdict(list)
        for review in self.reviews:
            product_id = review.get('product_id', 'Unknown')
            product_reviews[product_id].append(review)
        
        # Calculate stats per product
        row = 2
        for product_id, reviews_list in product_reviews.items():
            if not reviews_list:
                continue
            
            avg_rating = sum([r.get('rating') or 0 for r in reviews_list]) / len(reviews_list) if reviews_list else 0
            avg_polarity = sum([r.get('polarity', 0) for r in reviews_list]) / len(reviews_list)
            positive_count = sum(1 for r in reviews_list if r.get('sentiment') == 'POSITIVE')
            negative_count = sum(1 for r in reviews_list if r.get('sentiment') == 'NEGATIVE')
            
            positive_pct = (positive_count / len(reviews_list) * 100) if reviews_list else 0
            negative_pct = (negative_count / len(reviews_list) * 100) if reviews_list else 0
            
            # Determine overall sentiment
            if avg_polarity > 0.1:
                sentiment = "POSITIVE"
            elif avg_polarity < -0.1:
                sentiment = "NEGATIVE"
            else:
                sentiment = "NEUTRAL"
            
            ws.cell(row=row, column=1, value=str(product_id)[:50])
            ws.cell(row=row, column=2, value=len(reviews_list))
            ws.cell(row=row, column=3, value=round(avg_rating, 2))
            ws.cell(row=row, column=4, value=round(avg_polarity, 3))
            ws.cell(row=row, column=5, value=sentiment)
            ws.cell(row=row, column=6, value=round(positive_pct, 1))
            ws.cell(row=row, column=7, value=round(negative_pct, 1))
            
            for col in range(1, 8):
                self._apply_style(ws.cell(row=row, column=col), self._get_style_data())
            
            row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 12
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 12
    
    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extract keywords from text using simple TF-IDF approach"""
        if not text:
            return []
        
        # Simple stopwords
        stopwords = {'il', 'la', 'di', 'da', 'per', 'non', 'è', 'che', 'si', 'a', 'e', 'o', 'ho', 'sono', 'questo', 'questa'}
        
        # Extract words
        words = re.findall(r'\b[a-zàèéìòù]+\b', text.lower())
        
        # Filter stopwords and short words
        words = [w for w in words if w not in stopwords and len(w) > 3]
        
        # Count and get top
        word_counts = Counter(words)
        return [word for word, count in word_counts.most_common(top_n)]
    
    def generate_sheet3_problems_keywords(self):
        """Sheet 3: Problems & Keywords - top complaints"""
        ws = self.workbook.create_sheet("Problemi & Keywords")
        logger.info("Generating Sheet 3: Problems & Keywords")
        
        # Headers
        headers = ["Prodotto", "Negative Reviews", "Top Keywords", "Common Issues"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            self._apply_style(cell, self._get_style_header())
        
        # Find negative reviews
        negative_reviews = [r for r in self.reviews if r.get('sentiment') == 'NEGATIVE']
        
        # Group by product
        product_negative = defaultdict(list)
        for review in negative_reviews:
            product_id = review.get('product_id', 'Unknown')
            product_negative[product_id].append(review)
        
        # Write data
        row = 2
        for product_id, neg_reviews in product_negative.items():
            if not neg_reviews:
                continue
            
            # Aggregate text
            all_text = ' '.join([r.get('text', '') or r.get('title', '') for r in neg_reviews])
            keywords = self._extract_keywords(all_text, top_n=5)
            
            issues = []
            for review in neg_reviews:
                text = review.get('text', '') or review.get('title', '')
                if text:
                    issues.append(text[:100])
            
            ws.cell(row=row, column=1, value=str(product_id)[:40])
            ws.cell(row=row, column=2, value=len(neg_reviews))
            ws.cell(row=row, column=3, value=", ".join(keywords))
            ws.cell(row=row, column=4, value="\n".join(issues[:2]))
            
            for col in range(1, 5):
                cell = ws.cell(row=row, column=col)
                self._apply_style(cell, self._get_style_data())
                if col == 4:
                    cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            
            row += 1
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 35
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 50
        ws.row_dimensions[1].height = 30
    
    def generate_sheet4_competitor_details(self):
        """Sheet 4: Competitor Details - full product data"""
        ws = self.workbook.create_sheet("Dettagli Competitor")
        logger.info("Generating Sheet 4: Competitor Details")
        
        # Headers
        headers = [
            "Nome Prodotto", "Prezzo €", "Rating", "Review Count",
            "Potenza W", "Kg", "Serbatoio ml", "Cavo cm",
            "Vapore Setting", "Source", "URL"
        ]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            self._apply_style(cell, self._get_style_header())
        
        # Write products
        row = 2
        for product in self.products:
            ws.cell(row=row, column=1, value=product.get('name', 'Unknown')[:60])
            ws.cell(row=row, column=2, value=product.get('price_eur'))
            ws.cell(row=row, column=3, value=product.get('rating'))
            ws.cell(row=row, column=4, value=product.get('review_count', 0))
            ws.cell(row=row, column=5, value=product.get('potenza_w'))
            ws.cell(row=row, column=6, value=product.get('kg'))
            ws.cell(row=row, column=7, value=product.get('serbatoio_ml'))
            ws.cell(row=row, column=8, value=product.get('cavo_cm'))
            ws.cell(row=row, column=9, value=product.get('vapore_setting'))
            ws.cell(row=row, column=10, value=product.get('source', 'Unknown'))
            ws.cell(row=row, column=11, value=product.get('url', '')[:80])
            
            for col in range(1, 12):
                self._apply_style(ws.cell(row=row, column=col), self._get_style_data())
            
            row += 1
        
        # Adjust column widths
        widths = [35, 10, 8, 12, 10, 8, 12, 8, 12, 12, 40]
        for idx, width in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(idx)].width = width
    
    def save(self, output_file: str = "competitive_analysis_report.xlsx") -> bool:
        """Save report to Excel file"""
        try:
            self.workbook.save(output_file)
            logger.info(f"Report saved to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            return False
    
    def generate(self, output_file: str = "competitive_analysis_report.xlsx") -> bool:
        """Generate complete report"""
        if not self.load_data():
            return False
        
        self.generate_sheet1_competitive_analysis()
        self.generate_sheet2_sentiment_summary()
        self.generate_sheet3_problems_keywords()
        self.generate_sheet4_competitor_details()
        
        return self.save(output_file)


if __name__ == "__main__":
    logger.info("Starting Report Generation...")
    
    generator = ReportGenerator(
        products_file="products.json",
        reviews_file="reviews_with_sentiment.json"
    )
    
    if generator.generate("competitive_analysis_report.xlsx"):
        logger.info("✅ Report generated successfully!")
        print("\n✅ Report saved: competitive_analysis_report.xlsx")
    else:
        logger.error("❌ Failed to generate report")
import os
import pandas as pd
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CatalogManager:
    def __init__(self, data_path=None, api_endpoint=None):
        self.product_data = None
        self.data_path = data_path
        self.api_endpoint = api_endpoint
        self.index = None
        
    def load_from_csv(self):
        """Load product catalog from a CSV file"""
        try:
            self.product_data = pd.read_csv(self.data_path)
            print(f"Loaded {len(self.product_data)} products from CSV")
            return True
        except Exception as e:
            logging.error(f"Error loading CSV: {str(e)}")
            return False
    
    def load_from_api(self):
        """Load product catalog from API endpoint"""
        import requests
        try:
            response = requests.get(self.api_endpoint)
            if response.status_code == 200:
                data = response.json()
                self.product_data = pd.DataFrame(data)
                print(f"Loaded {len(self.product_data)} products from API")
                return True
            else:
                logging.error(f"API returned status code {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"Error loading from API: {str(e)}")
            return False
    
    def build_search_index(self):
        """Create a simple search index for products"""
        # In a production system, you would use a more sophisticated 
        # vector database like Pinecone, Weaviate, or FAISS
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        if self.product_data is None:
            return False
        
        # Combine relevant text fields for searching
        self.product_data['search_text'] = self.product_data.apply(
            lambda row: ' '.join([str(val) for val in row.values if isinstance(val, (str, int, float))]),
            axis=1
        )
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.index = self.vectorizer.fit_transform(self.product_data['search_text'])
        return True
    
    def search_products(self, query, top_k=5):
        """Search for products matching the query"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        if self.index is None:
            logging.error("Search index not built. Call build_search_index() first.")
            return []
        
        # Vectorize the query
        query_vec = self.vectorizer.transform([query])
        
        # Calculate similarity to all products
        similarities = cosine_similarity(query_vec, self.index).flatten()
        
        # Get indices of top matches
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        # Return the top matching products
        results = [
            self.product_data.iloc[idx].to_dict() 
            for idx in top_indices 
            if similarities[idx] > 0.1  # Similarity threshold
        ]
        
        return results
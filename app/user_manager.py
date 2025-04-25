import os
import json
import pandas as pd
import logging

class UserManager:
    def __init__(self, db_path="user_profiles.json"):
        self.db_path = db_path
        self.users = self._load_users()

    def _load_users(self):
        """Load user profiles from database"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading user profiles: {str(e)}")
                return {}
        return {}

    def _save_users(self):
        """Save user profiles to database"""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.users, f)
            return True
        except Exception as e:
            logging.error(f"Error saving user profiles: {str(e)}")
            return False

    def get_user(self, user_id):
        """Get a user profile by ID"""
        if user_id not in self.users:
            self.users[user_id] = {
                "interactions": [],
                "viewed_products": [],
                "purchased_products": [],
                "preferences": {}
            }
            self._save_users()
        return self.users[user_id]

    def update_interaction(self, user_id, query, products_shown, selected_product=None):
        """Record a user interaction with the system"""
        user = self.get_user(user_id)

        # Add interaction to history
        interaction = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "query": query,
            "products_shown": [p.get('id', '') for p in products_shown],
            "selected_product": selected_product
        }
        user["interactions"].append(interaction)

        # Update viewed products
        for product in products_shown:
            if product.get('id') not in user["viewed_products"]:
                user["viewed_products"].append(product.get('id'))

        # Update purchased products if one was selected
        if selected_product:
            if selected_product not in user["purchased_products"]:
                user["purchased_products"].append(selected_product)

        # Update preferences (simple implementation)
        # In a real system, you'd use more sophisticated methods
        for product in products_shown:
            for key, value in product.items():
                if key in ['category', 'brand', 'color', 'material']:
                    if key not in user["preferences"]:
                        user["preferences"][key] = {}
                    if value not in user["preferences"][key]:
                        user["preferences"][key][value] = 0
                    user["preferences"][key][value] += 1

        # Save changes
        self._save_users()
        return True

    def get_user_history_summary(self, user_id):
        """Get a summary of the user's history for LLM context"""
        user = self.get_user(user_id)
        summary = []

        # Add top categories if they exist
        if user["preferences"].get("category"):
            top_categories = sorted(
                user["preferences"]["category"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            if top_categories:
                cats = ", ".join([cat for cat, _ in top_categories])
                summary.append(f"Interested in categories: {cats}")

        # Add top brands if they exist
        if user["preferences"].get("brand"):
            top_brands = sorted(
                user["preferences"]["brand"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            if top_brands:
                brands = ", ".join([brand for brand, _ in top_brands])
                summary.append(f"Previously viewed brands: {brands}")

        # Add recent searches
        recent_queries = [i["query"] for i in user["interactions"][-5:]]
        if recent_queries:
            summary.append(f"Recent searches: {', '.join(recent_queries)}")

        return summary
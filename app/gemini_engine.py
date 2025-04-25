# Improved Gemini API Integration for E-commerce Chatbot
# With more concise, personalized responses

import os
import json
import logging
import requests
from typing import List, Dict, Any

class GeminiLLMEngine:
    """LLM Engine that uses Google's Gemini API for inference with improved response style"""

    def __init__(self, api_key=None, model_name="gemini-2.0-flash"):
        """
        Initialize the Gemini LLM Engine

        Args:
            api_key: Gemini API key (if not provided, will look for GEMINI_API_KEY env variable)
            model_name: Name of the Gemini model to use
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass to constructor.")

        self.model_name = model_name
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"

        # Verify API key and connectivity
        self._check_api_connectivity()

    def _check_api_connectivity(self):
        """Verify Gemini API is accessible with the provided API key"""
        try:
            # Simple test request
            test_prompt = "Hello"
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts":[{"text": test_prompt}]}]
                }
            )

            if response.status_code == 200:
                logging.info(f"Successfully connected to Gemini API with model: {self.model_name}")
            elif response.status_code == 400:
                error_data = response.json()
                logging.warning(f"API request format issue: {error_data.get('error', {}).get('message')}")
                # Still return as this could just be an issue with the test prompt
            elif response.status_code == 403:
                raise ValueError("Invalid API key or insufficient permissions for Gemini API")
            else:
                logging.warning(f"Unexpected status code from Gemini API: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Error connecting to Gemini API: {str(e)}")
            raise ConnectionError(f"Could not connect to Gemini API: {str(e)}")

    def generate_response(self, user_input, product_results, user_history=None):
        """
        Generate LLM response using Gemini API

        Args:
            user_input: User's query
            product_results: List of relevant products
            user_history: User's interaction history summary

        Returns:
            Generated text response
        """
        # Prepare context with product information
        product_info = "\n".join([
            f"Product {i+1}: {p.get('name', 'Unknown')} - {p.get('description', 'No description')} - ${p.get('price', 0)}"
            for i, p in enumerate(product_results[:5])  # Limit to top 5 for context size
        ])

        # Build prompt with user history if available
        history_context = ""
        if user_history and len(user_history) > 0:
            history_items = "\n".join([f"- {item}" for item in user_history[-5:]])  # Last 5 interactions
            history_context = f"\nUser's previous interests:\n{history_items}\n"

        # Create the full prompt for Gemini with style guidance
        prompt = f"""You are a concise, friendly store assistant who helps customers find the perfect products.

Available products matching the user's query:
{product_info}
{history_context}

User: {user_input}

IMPORTANT RESPONSE STYLE GUIDELINES:
1. Keep your response brief and conversational - under 3-4 sentences for product recommendations
2. Don't use bullet points or asterisks unless absolutely necessary
3. Speak naturally like a helpful assistant would in person
4. Ask at most ONE focused follow-up question to better understand their needs
5. Be warm but direct - no need for excessive greetings or verbosity
6. Mention 2-3 specific products maximum with their key benefits and prices
7. Sound like a real person having a casual conversation

Example of good response style:
"We have some great options for running shoes. The Sprint Pro X has extra cushioning for $89.99, and the AirGlide offers better breathability for $75.50. Do you prefer more cushioning or breathability?"

Remember to stay natural, brief, and conversational in your response.
"""

        try:
            # Make request to Gemini API
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.7,
                        "topP": 0.9,
                        "maxOutputTokens": 250,  # Limiting token count to encourage brevity
                    }
                }
            )

            if response.status_code != 200:
                logging.error(f"Gemini API error: {response.status_code}, {response.text}")
                return "I'm having trouble connecting right now. Can we try again in a moment?"

            # Extract the generated text from response
            response_data = response.json()

            # Handle potential response structure variations
            try:
                if 'candidates' in response_data:
                    generated_text = response_data['candidates'][0]['content']['parts'][0]['text']
                elif 'text' in response_data:
                    generated_text = response_data['text']
                else:
                    logging.error(f"Unexpected response structure: {response_data}")
                    return "Sorry, I couldn't process that request. Let me know what kind of shoes you're looking for."
            except (KeyError, IndexError) as e:
                logging.error(f"Error parsing Gemini response: {str(e)}")
                logging.error(f"Response data: {response_data}")
                return "I'm having a bit of trouble right now. Can you tell me more about what you're looking for?"

            return generated_text.strip()

        except requests.exceptions.RequestException as e:
            logging.error(f"Error calling Gemini API: {str(e)}")
            return "Sorry, I'm having trouble connecting right now. Can we try again in a moment?"
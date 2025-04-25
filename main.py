from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import json
import os
from typing import List, Dict, Any

# Import components
from app.catalog import CatalogManager
from app.gemini_engine import GeminiLLMEngine  # Updated to use Gemini
from app.user_manager import UserManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="E-commerce Chatbot with Google Gemini")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ChatMessage(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    products: List[Dict[str, Any]]

# Configuration
GEMINI_MODEL = "gemini-2.0-flash"  # You can also use "gemini-1.5-pro" or other variants
CATALOG_PATH = "data/products.csv"
USER_DB_PATH = "data/user_profiles.json"

# Initialize components
catalog = CatalogManager(data_path=CATALOG_PATH)

# Get Gemini API key from environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY not found in environment variables. Please set this before running the app.")

llm = GeminiLLMEngine(
    api_key=GEMINI_API_KEY,
    model_name=GEMINI_MODEL
)

user_mgr = UserManager(db_path=USER_DB_PATH)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Startup event
@app.on_event("startup")
async def startup_event():
    if not catalog.load_from_csv():
        logging.error("Failed to load product catalog")
    catalog.build_search_index()
    logging.info(f"Using Google Gemini API with model: {GEMINI_MODEL}")

# API endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(message: ChatMessage):
    # Get user profile
    user_id = message.user_id
    user_history = user_mgr.get_user_history_summary(user_id)

    # Search for relevant products
    products = catalog.search_products(message.message)

    # Generate response using Gemini
    response = llm.generate_response(message.message, products, user_history)

    # Update user interaction history
    user_mgr.update_interaction(user_id, message.message, products)

    return ChatResponse(
        response=response,
        products=products
    )

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logging.info(f"WebSocket connection established for user {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logging.info(f"WebSocket connection closed for user {user_id}")

    async def send_response(self, user_id: str, response: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(response)

manager = ConnectionManager()

# WebSocket for real-time chat
@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")

            # Get user profile
            user_history = user_mgr.get_user_history_summary(user_id)

            # Search for relevant products
            products = catalog.search_products(user_message)

            # Generate response using Gemini
            response = llm.generate_response(user_message, products, user_history)

            # Update user interaction history
            user_mgr.update_interaction(user_id, user_message, products)

            # Send response back to client
            await websocket.send_json({
                "response": response,
                "products": products
            })
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
    finally:
        manager.disconnect(user_id)

# Root endpoint redirects to the chat interface
@app.get("/")
async def root():
    return {"message": "Welcome to E-commerce Chatbot with Google Gemini", "docs": "/docs"}

# Test endpoint for Gemini API integration
@app.post("/test_gemini")
async def test_gemini(message: str = "Hello, can you recommend a good laptop?"):
    """Test endpoint to verify Gemini API integration"""
    try:
        # Sample product results for testing
        sample_products = [
            {
                "id": "laptop1",
                "name": "UltraBook Pro X1",
                "description": "Powerful laptop with 16GB RAM and 512GB SSD",
                "price": 1299.99
            },
            {
                "id": "laptop2",
                "name": "LightBook Air",
                "description": "Thin and light laptop with excellent battery life",
                "price": 999.99
            }
        ]

        # Generate response using Gemini
        response = llm.generate_response(message, sample_products)

        return {
            "status": "success",
            "gemini_model": GEMINI_MODEL,
            "query": message,
            "response": response
        }
    except Exception as e:
        logging.error(f"Error testing Gemini API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gemini API test failed: {str(e)}")

# Main execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
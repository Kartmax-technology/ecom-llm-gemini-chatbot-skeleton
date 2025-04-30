# Project Setup and Execution Guide

This guide explains how to set up and run the application.

## Prerequisites

- Python 3.x
- pip (Python package installer)
- A Gemini API key (obtain from [Google AI Studio](https://ai.google.dev/))

## Installation and Setup

1. **Install dependencies**

   ```
   pip install -r requirements.txt
   ```

2. **Create a virtual environment**

   ```
   python3 -m venv venv
   ```

3. **Activate the virtual environment**

   On Linux/macOS:
   ```
   source venv/bin/activate
   ```

   On Windows:
   ```
   venv\Scripts\activate
   ```

4. **Set up your Gemini API key**

   ```
   export GEMINI_API_KEY=your_api_key_here
   ```

   On Windows:
   ```
   set GEMINI_API_KEY=your_api_key_here
   ```

## Running the Application

1. **Start the backend server**

   ```
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   This will start the backend service at `http://localhost:8000`

2. **Access the frontend**

   Open `public/index.html` in your web browser. You can do this by:
   - Navigating to the file in your file explorer and double-clicking it
   - Using a local development server
   - Entering the file path in your browser (e.g., `file:///path/to/your/project/public/index.html`)

## Verifying WebSocket Connection

To ensure the WebSocket connection is working properly:

1. Open the browser's developer tools (F12 or right-click > Inspect)
2. Navigate to the Console tab
3. Look for messages indicating a successful WebSocket connection
4. If no errors appear and you can interact with the application, the WebSocket connection is working correctly

## Troubleshooting

If you encounter issues with the WebSocket connection:

- Ensure the backend server is running
- Check that you're using the correct port (8000)
- Verify there are no firewall or network restrictions blocking WebSocket connections
- Check the browser console for specific error messages

## Project Structure

- `main.py`: The FastAPI backend application
- `requirements.txt`: List of Python dependencies
- `public/index.html`: Frontend HTML interface
- `venv/`: Virtual environment directory (created during setup)

## Notes

- The application uses port 8000 by default, ensure this port is available
- The Gemini API key must be valid for the application to function properly

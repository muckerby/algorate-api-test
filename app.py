#!/usr/bin/env python3
"""
Algorate API Connectivity Test Service
Tests Punting Form API access from Railway Singapore region
"""

import os
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template_string
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Test configuration
PUNTING_FORM_API_BASE = "https://api.puntingform.com.au/v2"
TEST_DATE = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Algorate API Test - Railway Singapore</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { padding: 20px; margin: 20px 0; border-radius: 8px; }
        .success { background: #2d5a2d; border: 2px solid #4caf50; }
        .error { background: #5a2d2d; border: 2px solid #f44336; }
        .info { background: #2d4a5a; border: 2px solid #2196f3; }
        pre { background: #333; padding: 15px; border-radius: 4px; overflow-x: auto; }
        h1 { color: #4caf50; }
        .timestamp { color: #888; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Algorate API Connectivity Test</h1>
        <div class="info">
            <h3>Test Environment</h3>
            <p><strong>Platform:</strong> Railway</p>
            <p><strong>Region:</strong> Singapore (asia-southeast1)</p>
            <p><strong>Target API:</strong> Punting Form API</p>
            <p><strong>Test Date:</strong> {{ test_date }}</p>
            <p class="timestamp">Last tested: {{ timestamp }}</p>
        </div>
        
        <div class="status {{ status_class }}">
            <h3>{{ status_title }}</h3>
            <p>{{ status_message }}</p>
        </div>
        
        {% if api_response %}
        <div class="info">
            <h3>API Response Details</h3>
            <pre>{{ api_response }}</pre>
        </div>
        {% endif %}
        
        {% if error_details %}
        <div class="error">
            <h3>Error Details</h3>
            <pre>{{ error_details }}</pre>
        </div>
        {% endif %}
        
        <div class="info">
            <h3>Test Results Interpretation</h3>
            <ul>
                <li><strong>✅ Success:</strong> Railway Singapore can access Punting Form API</li>
                <li><strong>🚫 Geo-blocked:</strong> Need to migrate to Azure Australia</li>
                <li><strong>⚠️ Other Error:</strong> API key or endpoint issue</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

def test_api_connectivity():
    """Test Punting Form API connectivity from current location"""
    try:
        # Test endpoint - meetings list
        url = f"{PUNTING_FORM_API_BASE}/form/meetingslist"
        
        # Get API key from environment
        api_key = os.getenv("PUNTING_FORM_API_KEY", "test-key")
        
        # Correct authentication method - apiKey as URL parameter
        params = {
            "meetingDate": TEST_DATE,
            "apiKey": api_key
        }
        
        headers = {
            "User-Agent": "Algorate-Test/1.0"
        }
        
        logger.info(f"Testing API connectivity to {url}")
        logger.info(f"Test date: {TEST_DATE}")
        logger.info(f"Using API key: {api_key[:8]}...")
        
        # Make request with timeout
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        result = {
            "success": True,
            "status_code": response.status_code,
            "url": response.url,
            "headers": dict(response.headers),
            "response_size": len(response.content)
        }
        
        # Try to parse JSON response
        try:
            json_data = response.json()
            result["json_response"] = json_data
            
            # Check if we got actual meeting data
            if response.status_code == 200 and json_data.get("payLoad"):
                result["meetings_count"] = len(json_data["payLoad"]) if isinstance(json_data["payLoad"], list) else 1
                result["sample_meeting"] = json_data["payLoad"][0] if isinstance(json_data["payLoad"], list) and len(json_data["payLoad"]) > 0 else None
            else:
                result["meetings_count"] = "N/A"
        except:
            result["response_text"] = response.text[:500] + "..." if len(response.text) > 500 else response.text
        
        logger.info(f"API test result: {response.status_code}")
        return result
        
    except requests.exceptions.Timeout:
        logger.error("API request timeout")
        return {
            "success": False,
            "error": "Request timeout",
            "details": "API request timed out after 10 seconds"
        }
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return {
            "success": False,
            "error": "Connection error",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            "success": False,
            "error": "Unexpected error",
            "details": str(e)
        }

@app.route("/")
def index():
    """Main test page"""
    result = test_api_connectivity()
    
    if result["success"]:
        if result["status_code"] == 200:
            status_class = "success"
            status_title = "✅ API Connectivity SUCCESS"
            status_message = f"Successfully connected to Punting Form API from Railway Singapore! Status: {result['status_code']}"
        elif result["status_code"] == 403:
            status_class = "error"
            status_title = "🚫 GEO-BLOCKED"
            status_message = "API returned 403 Forbidden - likely geo-blocked. Need to migrate to Azure Australia."
        elif result["status_code"] == 401:
            status_class = "error"
            status_title = "🔑 AUTHENTICATION ERROR"
            status_message = "API returned 401 Unauthorized - API key issue, but connectivity works!"
        else:
            status_class = "error"
            status_title = f"⚠️ API ERROR ({result['status_code']})"
            status_message = f"API returned status {result['status_code']} - connectivity works but API issue"
    else:
        status_class = "error"
        status_title = "❌ CONNECTION FAILED"
        status_message = f"Failed to connect to API: {result['error']}"
    
    return render_template_string(HTML_TEMPLATE,
        test_date=TEST_DATE,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        status_class=status_class,
        status_title=status_title,
        status_message=status_message,
        api_response=json.dumps(result, indent=2) if result.get("success") else None,
        error_details=result.get("details") if not result.get("success") else None
    )

@app.route("/api/test")
def api_test():
    """JSON API endpoint for test results"""
    result = test_api_connectivity()
    result["timestamp"] = datetime.now().isoformat()
    result["test_location"] = "Railway Singapore"
    result["test_date"] = TEST_DATE
    return jsonify(result)

@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "algorate-api-test",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)


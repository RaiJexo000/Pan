from flask import Flask, request, jsonify
import requests
import time
import logging
from datetime import datetime
import os
import json
from functools import wraps

# ============================================
# 📋 FLASK APP INITIALIZATION
# ============================================
app = Flask(__name__)

# ============================================
# 🏷️ BRANDING CONFIGURATION
# ============================================
APP_NAME = "PAN Lookup API"
VERSION = "2.0"
DEVELOPER = "@RaiJexo"
CHANNEL = "https://t.me/NAXupdate"
STUDIO = "RJ Studio"
COPYRIGHT = "© 2026 RJ Studio. All Rights Reserved."
DEPLOYMENT = "Vercel Serverless"

# ============================================
# 🔐 TOKEN MANAGEMENT (Vercel Optimized)
# ============================================
TOKEN_FILE = '/tmp/token_cache.json'
DEFAULT_TOKEN = "1843d97b04a6d2f4059d689cee445aa52809b09e9d41945b6db4e8a80e988433af3b0a7b48e825dccdeb00e6bf6393be"

def get_token():
    """Get token from cache or use default"""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                # Check if token is still valid (15 min)
                if time.time() - data.get('timestamp', 0) < 900:
                    return data.get('token', DEFAULT_TOKEN)
    except:
        pass
    return DEFAULT_TOKEN

def update_token(new_token):
    """Update token in cache"""
    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump({
                'token': new_token,
                'timestamp': time.time()
            }, f)
        return True
    except:
        return False

# ============================================
# 📊 STATISTICS (In-Memory)
# ============================================
REQUEST_COUNTER = 0
SUCCESS_COUNTER = 0
ERROR_COUNTER = 0
START_TIME = time.time()

# ============================================
# 🔧 LOGGING SETUP
# ============================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# 🛡️ RATE LIMITING
# ============================================
RATE_LIMIT = {}

def rate_limit_check(ip):
    """Simple rate limiting: 100 requests per minute"""
    current_time = time.time()
    if ip not in RATE_LIMIT:
        RATE_LIMIT[ip] = []
    
    # Clean old requests
    RATE_LIMIT[ip] = [t for t in RATE_LIMIT[ip] if current_time - t < 60]
    
    if len(RATE_LIMIT[ip]) >= 100:
        return False
    
    RATE_LIMIT[ip].append(current_time)
    return True

# ============================================
# 📦 RESPONSE HELPER WITH BRANDING
# ============================================
def add_branding(data, show_branding=True):
    """Add branding to response"""
    if show_branding:
        data["branding"] = {
            "studio": STUDIO,
            "developer": DEVELOPER,
            "channel": CHANNEL,
            "version": VERSION,
            "copyright": COPYRIGHT,
            "powered_by": "RJ Studio"
        }
        data["timestamp"] = datetime.now().isoformat()
        data["deployment"] = DEPLOYMENT
    return data

# ============================================
# 🏠 ROOT ENDPOINT
# ============================================
@app.route('/', methods=['GET'])
def home():
    return jsonify(add_branding({
        "app": APP_NAME,
        "version": VERSION,
        "status": "Active",
        "server_time": datetime.now().isoformat(),
        "endpoints": {
            "/": "🏠 Home page with info",
            "/lookup_pan": "🔍 Check PAN details (GET)",
            "/bulk_lookup": "📦 Check multiple PANs (POST)",
            "/stats": "📊 API usage statistics",
            "/health": "💚 Health check",
            "/refresh_token": "🔄 Manually refresh token (POST)",
            "/about": "ℹ️ About this API"
        }
    }))

# ============================================
# ℹ️ ABOUT ENDPOINT
# ============================================
@app.route('/about', methods=['GET'])
def about():
    return jsonify(add_branding({
        "app": APP_NAME,
        "version": VERSION,
        "developer": DEVELOPER,
        "studio": STUDIO,
        "channel": CHANNEL,
        "copyright": COPYRIGHT,
        "description": "Turtlemint PAN Lookup API - Check existing leads by PAN number",
        "features": [
            "🔍 Single PAN lookup",
            "📦 Bulk PAN lookup (up to 20 PANs)",
            "🔄 Auto token management",
            "🛡️ Rate limiting (100 req/min)",
            "📊 Usage statistics",
            "💚 Health monitoring",
            "🏷️ Branding included"
        ],
        "deployment": DEPLOYMENT,
        "support": "https://t.me/NAXupdate"
    }))

# ============================================
# 📊 STATS ENDPOINT
# ============================================
@app.route('/stats', methods=['GET'])
def get_stats():
    uptime_seconds = int(time.time() - START_TIME)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    
    return jsonify(add_branding({
        "app": APP_NAME,
        "version": VERSION,
        "statistics": {
            "total_requests": REQUEST_COUNTER,
            "successful_requests": SUCCESS_COUNTER,
            "failed_requests": ERROR_COUNTER,
            "success_rate": f"{(SUCCESS_COUNTER/REQUEST_COUNTER*100):.2f}%" if REQUEST_COUNTER > 0 else "0%",
            "token_status": "Valid" if get_token() else "Missing",
            "token_length": len(get_token()) if get_token() else 0
        },
        "uptime": {
            "seconds": uptime_seconds,
            "minutes": uptime_minutes,
            "hours": uptime_hours,
            "formatted": f"{uptime_hours}h {uptime_minutes}m"
        }
    }))

# ============================================
# 💚 HEALTH CHECK
# ============================================
@app.route('/health', methods=['GET'])
def health_check():
    token = get_token()
    return jsonify({
        "status": "healthy",
        "app": APP_NAME,
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "token_available": bool(token),
        "token_length": len(token) if token else 0,
        "studio": STUDIO,
        "environment": "Vercel",
        "uptime": f"{int(time.time() - START_TIME)}s"
    })

# ============================================
# 🔄 REFRESH TOKEN ENDPOINT
# ============================================
@app.route('/refresh_token', methods=['POST'])
def refresh_token():
    """Manually refresh token"""
    try:
        # Try to get token from Turtlemint
        test_headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "application/json"
        }
        
        response = requests.get(
            "https://turtlemintloans.com/products/personal-loan/customer/MULTI/apply",
            headers=test_headers,
            timeout=10
        )
        
        # Try to extract token from response
        if response.headers.get('authorization'):
            new_token = response.headers.get('authorization').replace('Bearer ', '')
            update_token(new_token)
            return jsonify({
                "status": "success",
                "message": "Token refreshed successfully",
                "token": new_token[:20] + "...",
                "developer": DEVELOPER
            })
        
        return jsonify({
            "status": "warning",
            "message": "Could not fetch new token. Using existing token.",
            "current_token": get_token()[:20] + "...",
            "developer": DEVELOPER,
            "note": "Auto-refresh requires Selenium which is not available on Vercel"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Token refresh failed: {str(e)}",
            "developer": DEVELOPER
        }), 500

# ============================================
# 🔍 SINGLE PAN LOOKUP
# ============================================
@app.route('/lookup_pan', methods=['GET'])
def lookup_pan():
    global REQUEST_COUNTER, SUCCESS_COUNTER, ERROR_COUNTER
    REQUEST_COUNTER += 1

    # Rate limiting
    client_ip = request.remote_addr
    if not rate_limit_check(client_ip):
        ERROR_COUNTER += 1
        return jsonify({
            "status": "error",
            "message": "Rate limit exceeded. Max 100 requests per minute.",
            "developer": DEVELOPER,
            "channel": CHANNEL
        }), 429

    pan_number = request.args.get('pan')
    show_branding = request.args.get('branding', 'true').lower() == 'true'

    # Validate PAN
    if not pan_number:
        ERROR_COUNTER += 1
        return jsonify({
            "status": "error",
            "message": "Usage: /lookup_pan?pan=MQTPS3756A",
            "example": "/lookup_pan?pan=ABCDE1234F",
            "developer": DEVELOPER,
            "channel": CHANNEL
        }), 400

    if not pan_number.isalnum() or len(pan_number) != 10:
        ERROR_COUNTER += 1
        return jsonify({
            "status": "error",
            "message": "Invalid PAN format. PAN must be 10 characters alphanumeric.",
            "example": "ABCDE1234F",
            "developer": DEVELOPER
        }), 400

    # Prepare request
    headers = {
        "host": "turtlemintloans.com",
        "authorization": f"Bearer {get_token()}",
        "x-broker": "turtlemint",
        "x-provider": "signzy",
        "x-tenant": "turtlemint",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "content-type": "application/json"
    }

    params = {"pan": pan_number.upper().strip()}

    try:
        logger.info(f"[REQUEST] PAN Lookup: {pan_number.upper()}")
        response = requests.get(
            "https://turtlemintloans.com/api/minterprise/v1/products/personal-loan/leads/existing-lead-by-pan",
            headers=headers,
            params=params,
            timeout=10
        )
        SUCCESS_COUNTER += 1
        
        response_data = response.json()
        
        # Add branding
        if show_branding:
            response_data = add_branding(response_data)
        
        logger.info(f"[SUCCESS] PAN: {pan_number.upper()} | Status: {response.status_code}")
        return jsonify(response_data), response.status_code
        
    except requests.exceptions.Timeout:
        ERROR_COUNTER += 1
        return jsonify({
            "status": "error",
            "error": "Request timeout",
            "message": "Server took too long to respond. Please try again.",
            "developer": DEVELOPER,
            "channel": CHANNEL
        }), 504
        
    except requests.exceptions.ConnectionError:
        ERROR_COUNTER += 1
        return jsonify({
            "status": "error",
            "error": "Connection failed",
            "message": "Unable to connect to Turtlemint servers. Please try again later.",
            "developer": DEVELOPER,
            "channel": CHANNEL
        }), 503
        
    except Exception as e:
        ERROR_COUNTER += 1
        logger.error(f"[EXCEPTION] PAN: {pan_number.upper()} | Error: {str(e)}")
        return jsonify({
            "status": "error",
            "exception": str(e),
            "message": "Something went wrong. Please contact developer.",
            "developer": DEVELOPER,
            "channel": CHANNEL,
            "support": "https://t.me/NAXupdate"
        }), 500

# ============================================
# 📦 BULK PAN LOOKUP
# ============================================
@app.route('/bulk_lookup', methods=['POST'])
def bulk_lookup():
    global REQUEST_COUNTER, SUCCESS_COUNTER, ERROR_COUNTER
    REQUEST_COUNTER += 1

    try:
        data = request.get_json()
        if not data or 'pans' not in data:
            ERROR_COUNTER += 1
            return jsonify({
                "status": "error",
                "message": "Please provide JSON with 'pans' array",
                "example": {"pans": ["MQTPS3756A", "ABCDE1234F"]},
                "developer": DEVELOPER,
                "channel": CHANNEL
            }), 400

        pans = data.get('pans', [])
        if not isinstance(pans, list):
            ERROR_COUNTER += 1
            return jsonify({
                "status": "error",
                "message": "'pans' must be an array",
                "developer": DEVELOPER
            }), 400

        if len(pans) > 20:
            return jsonify({
                "status": "error",
                "message": "Maximum 20 PANs allowed per request",
                "developer": DEVELOPER
            }), 400

        results = {}
        headers = {
            "authorization": f"Bearer {get_token()}",
            "x-broker": "turtlemint",
            "x-provider": "signzy",
            "x-tenant": "turtlemint",
            "content-type": "application/json"
        }

        for pan in pans:
            pan = pan.upper().strip()
            try:
                params = {"pan": pan}
                response = requests.get(
                    "https://turtlemintloans.com/api/minterprise/v1/products/personal-loan/leads/existing-lead-by-pan",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                results[pan] = response.json()
                SUCCESS_COUNTER += 1
                logger.info(f"[BULK SUCCESS] PAN: {pan}")
            except Exception as e:
                results[pan] = {"error": str(e)}
                ERROR_COUNTER += 1
                logger.error(f"[BULK ERROR] PAN: {pan} | {str(e)}")

        response_data = {
            "status": "success",
            "total": len(pans),
            "results": results
        }
        
        return jsonify(add_branding(response_data)), 200

    except Exception as e:
        ERROR_COUNTER += 1
        return jsonify({
            "status": "error",
            "message": str(e),
            "developer": DEVELOPER
        }), 500

# ============================================
# 🔥 ERROR HANDLERS
# ============================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "available_endpoints": [
            "/",
            "/lookup_pan",
            "/bulk_lookup",
            "/stats",
            "/health",
            "/refresh_token",
            "/about"
        ],
        "developer": DEVELOPER,
        "channel": CHANNEL
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "status": "error",
        "message": "Method not allowed",
        "developer": DEVELOPER,
        "channel": CHANNEL
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "developer": DEVELOPER,
        "support": "https://t.me/NAXupdate"
    }), 500

# ============================================
# 🚀 VERCEL SERVERLESS HANDLER
# ============================================
# This is the entry point for Vercel
def handler(request, context):
    """Vercel serverless function handler"""
    return app

# ============================================
# 🏃 LOCAL DEVELOPMENT
# ============================================
if __name__ == '__main__':
    print("="*60)
    print(f"🚀 {APP_NAME} v{VERSION}")
    print(f"🏷️  Studio: {STUDIO}")
    print(f"👨‍💻 Developer: {DEVELOPER}")
    print(f"📢 Channel: {CHANNEL}")
    print("="*60)
    print("[+] Starting API on Vercel Serverless...")
    print("[+] Token: Using cached or default token")
    print("[+] Server listening on http://0.0.0.0:5000")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)

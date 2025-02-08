import boto3
from botocore.exceptions import ClientError
import json
import logging
import os
from flask import Flask, request, jsonify
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Fetch environment variables for profile and org
PROFILE = os.getenv('profile', 'default')  # Default to 'default' if not set
ORG = os.getenv('service', 'default_service')     # Default to 'default_org' if not set

# Health endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    log_request_details(request)
    return jsonify({"status": "healthy"}), 200

# Endpoint to fetch AWS Secret
@app.route('/fetch-secret', methods=['GET'])
def fetch_secret():
    """Fetch the AWS Secret."""
    tenant = request.args.get('tenant')  # Get tenant from query parameter
    if not tenant:
        return jsonify({"error": "Tenant parameter is missing"}), 400
    
    # Construct the secret name dynamically using profile, org, and tenant
    secret_name = f"{PROFILE}/{ORG}/{tenant}"
    region_name = "es-east-1"
    
    try:
        secret = get_secret(secret_name, region_name)
        logger.info(f"Fetched secret for tenant {tenant}: {secret}")
        return jsonify(secret), 200
    except Exception as e:
        logger.error(f"Error fetching secret for tenant {tenant}: {e}")
        return jsonify({"error": str(e)}), 500

# Helper to fetch AWS secret
def get_secret(secret_name, region_name):
    """Fetch a secret from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(f"Error fetching secret: {e}")
        raise e
    
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

# Generic method to log requests
def log_request_details(req):
    """Logs the details of the HTTP request."""
    request_time = datetime.datetime.now()
    content_length = len(req.data)  # Get the size of data
    logger.info(f"--- Request Info ---\nTime: {request_time}\nMethod: {req.method}\nPath: {req.path}\nHeaders: {dict(req.headers)}\nBody: {req.data.decode('utf-8') if content_length else 'No Body'}\n-------------------")

# Catch-all route for other HTTP methods
@app.route('/', methods=['POST', 'PUT', 'DELETE'])
def handle_other_methods():
    """Handles POST, PUT, DELETE requests."""
    log_request_details(request)
    return jsonify({"message": f"{request.method} method handled."}), 200

if __name__ == '__main__':
    # Run the Flask app
    port = 5000  # Change this as needed
    logger.info(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port)

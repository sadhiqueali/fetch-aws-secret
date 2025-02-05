import boto3
from botocore.exceptions import ClientError
import json
import http.server
import socketserver
import datetime
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Start a simple HTTP server')
parser.add_argument('-p', '--port', type=int, default=5000, help='The port to listen on')
args = parser.parse_args()

PORT = args.port

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.get_path() == "health":
            self.send_200_response("healthy")
        self.log_request_details()
        secret_name = "dev/awssecretfetch/tenant"
        region_name = "eu-north-1"
        secret = self.get_secret(secret_name, region_name)
        logger.info(f"Fetched secret: {secret}")
        self.send_response(200)
        self.end_headers()

    def get_secret(self, secret_name, region_name):
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            # For a list of exceptions thrown, see
            # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
            logger.error(f"Error fetching secret: {e}")
            raise e

        secret = get_secret_value_response['SecretString']
        return json.loads(secret)

    def send_200_response(self, message, send_body=True):
        self.log_request_details()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        if send_body:
            self.wfile.write(message.encode('utf-8'))
            
    def do_POST(self):
        self.log_request_details()
        self.send_response(200)
        self.end_headers()

    def do_PUT(self):
        self.log_request_details()
        self.send_response(200)
        self.end_headers()

    def do_DELETE(self):
        self.log_request_details()
        self.send_response(200)
        self.end_headers()

    def log_request_details(self):
        request_time = datetime.datetime.now()
        content_length = int(self.headers.get('Content-Length', 0)) # Gets the size of data
        post_data = self.rfile.read(content_length) # Gets the data itself
        logger.info(f"---------------------------------------------------START---------------------------------------------------\n###################    Time: {request_time}\n###################  Method: {self.command}\n###################    Path: {self.path}\n################### Headers:\n{self.headers}\n###################    Body:\n{post_data.decode('utf-8')}\n---------------------------------------------------END---------------------------------------------------")

#os.chdir(RESOURCE_DIRECTORY)

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    logger.info(f"serving at port {PORT}")
    httpd.serve_forever()
import http.server
import json
import os
import threading
from urllib.parse import urlparse, parse_qs

# Import your teammates' modules
from dsa.parser import parse_sms_xml
from api.auth import is_authorized

# Global thread-safe database storage in memory
db_lock = threading.Lock()
transactions_db = {}

def load_initial_data():
    """Loads records from XML into a dictionary keyed by ID on startup."""
    global transactions_db
    xml_path = os.path.join(os.path.dirname(__file__), '..', 'modified_sms_v2.xml')
    if not os.path.exists(xml_path):
        # Fallback path if XML is in root
        xml_path = 'modified_sms_v2.xml'
    
    if os.path.exists(xml_path):
        records = parse_sms_xml(xml_path)
        with db_lock:
            for rec in records:
                transactions_db[rec['id']] = rec
        print(f"Loaded {len(transactions_db)} records successfully.")
    else:
        print("Warning: modified_sms_v2.xml not found!")

class MoMoRequestHandler(http.server.BaseHTTPRequestHandler):
    
    def send_json(self, status_code, data):
        """Helper method to send JSON responses cleanly."""
        response_body = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def authenticate_request(self):
        """Checks Basic Authentication header. Returns True if authorized, False otherwise."""
        auth_header = self.headers.get('Authorization')
        return is_authorized(auth_header)

    def check_auth_or_reject(self):
        """Gatekeeper: If unauthorized, sends 401 response and returns False."""
        if not self.authenticate_request():
            self.send_header('WWW-Authenticate', 'Basic realm="MoMo API"')
            self.send_json(401, {"error": "Unauthorized: Invalid or missing credentials"})
            return False
        return True

    def do_GET(self):
        if not self.check_auth_or_reject():
            return
        
        parsed_url = urlparse(self.path)
        path_parts = parsed_url.path.strip('/').split('/')

        # Route: GET /transactions
        if len(path_parts) == 1 and path_parts[0] == 'transactions':
            with db_lock:
                all_records = list(transactions_db.values())
            self.send_json(200, all_records)
            return

        # Route: GET /transactions/{id}
        elif len(path_parts) == 2 and path_parts[0] == 'transactions':
            try:
                txn_id = int(path_parts[1])
            except ValueError:
                self.send_json(400, {"error": "Invalid transaction ID format"})
                return

            with db_lock:
                record = transactions_db.get(txn_id)
            
            if record:
                self.send_json(200, record)
            else:
                self.send_json(404, {"error": "Transaction not found"})
            return

        # Catch-all for unmatched routes
        self.send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        if not self.check_auth_or_reject():
            return

        parsed_url = urlparse(self.path)
        path_parts = parsed_url.path.strip('/').split('/')

        # Route: POST /transactions
        if len(path_parts) == 1 and path_parts[0] == 'transactions':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json(400, {"error": "Missing request body"})
                return

            try:
                body_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            except json.JSONDecodeError:
                self.send_json(400, {"error": "Malformed JSON data"})
                return

            # Validate required fields
            required_fields = ['transaction_type', 'amount', 'sender', 'receiver', 'timestamp']
            for field in required_fields:
                if field not in body_data:
                    self.send_json(400, {"error": f"Missing required field: {field}"})
                    return

            with db_lock:
                # Generate new sequential ID
                new_id = max(transactions_db.keys()) + 1 if transactions_db else 1
                body_data['id'] = new_id
                transactions_db[new_id] = body_data

            self.send_json(201, body_data)
            return

        self.send_json(404, {"error": "Endpoint not found"})

    def do_PUT(self):
        if not self.check_auth_or_reject():
            return

        parsed_url = urlparse(self.path)
        path_parts = parsed_url.path.strip('/').split('/')

        # Route: PUT /transactions/{id}
        if len(path_parts) == 2 and path_parts[0] == 'transactions':
            try:
                txn_id = int(path_parts[1])
            except ValueError:
                self.send_json(400, {"error": "Invalid transaction ID format"})
                return

            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_json(400, {"error": "Missing request body"})
                return

            try:
                body_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            except json.JSONDecodeError:
                self.send_json(400, {"error": "Malformed JSON data"})
                return

            with db_lock:
                if txn_id not in transactions_db:
                    self.send_json(404, {"error": "Transaction not found"})
                    return
                
                # Prevent ID manipulation via PUT
                body_data['id'] = txn_id
                transactions_db[txn_id] = body_data

            self.send_json(200, body_data)
            return

        self.send_json(404, {"error": "Endpoint not found"})

    def do_DELETE(self):
        if not self.check_auth_or_reject():
            return

        parsed_url = urlparse(self.path)
        path_parts = parsed_url.path.strip('/').split('/')

        # Route: DELETE /transactions/{id}
        if len(path_parts) == 2 and path_parts[0] == 'transactions':
            try:
                txn_id = int(path_parts[1])
            except ValueError:
                self.send_json(400, {"error": "Invalid transaction ID format"})
                return

With db_lock:
                if txn_id in transactions_db:
                    del transactions_db[txn_id]
                    self.send_response(204)
                    self.end_headers()
                else:
                    self.send_json(404, {"error": "Transaction not found"})
            return

        self.send_json(404, {"error": "Endpoint not found"})

def run_server(port=8000):
    load_initial_data()
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, MoMoRequestHandler)
    print(f"Server running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    run_server(port)
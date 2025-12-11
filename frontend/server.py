"""
Simple web server to serve the frontend files for the OAuth2 system dashboard.
"""
from flask import Flask, send_from_directory, render_template
import os

app = Flask(__name__, static_folder='.')

# Serve static files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/omar_auth_server.html')
def omar_auth():
    return send_from_directory('.', 'omar_auth_server.html')

@app.route('/resource_server.html')
def resource_server():
    return send_from_directory('.', 'resource_server.html')

@app.route('/badr_client_app.html')
def badr_client():
    return send_from_directory('.', 'badr_client_app.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    print("Frontend server starting...")
    print("Visit http://localhost:8080 to access the OAuth2 System Dashboard")
    app.run(host='0.0.0.0', port=8080, debug=True)
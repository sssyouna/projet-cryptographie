"""
Database module for OAuth2 Authorization Server
Provides persistence for clients, users, and auth requests
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta
import bcrypt


class Database:
    def __init__(self, db_path='oauth2.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create clients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                client_id TEXT PRIMARY KEY,
                client_secret TEXT NOT NULL,
                client_name TEXT NOT NULL,
                client_uri TEXT,
                redirect_uris TEXT NOT NULL,  -- JSON encoded list
                grant_types TEXT NOT NULL,    -- JSON encoded list
                response_types TEXT NOT NULL, -- JSON encoded list
                token_endpoint_auth_method TEXT NOT NULL,
                scopes TEXT NOT NULL,         -- JSON encoded list
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                email TEXT NOT NULL,
                name TEXT NOT NULL,
                roles TEXT NOT NULL,          -- JSON encoded list
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create authorization requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth_requests (
                code TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                user_info TEXT NOT NULL,      -- JSON encoded dict
                scopes TEXT NOT NULL,         -- JSON encoded list
                redirect_uri TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create refresh tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                token TEXT PRIMARY KEY,
                user_info TEXT NOT NULL,      -- JSON encoded dict
                scopes TEXT NOT NULL,         -- JSON encoded list
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insert default client if it doesn't exist
        self.create_default_client()
        
        # Insert default users if they don't exist
        self.create_default_users()
    
    def create_default_client(self):
        """Create the default client if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM clients WHERE client_id = ?', ('badr_app',))
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute('''
                INSERT INTO clients (
                    client_id, client_secret, client_name, client_uri,
                    redirect_uris, grant_types, response_types,
                    token_endpoint_auth_method, scopes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'badr_app',
                os.getenv('CLIENT_SECRET', 'e2a8d3f7c9d5b1a4e6f8c2d7a9b3e5f1'),  # More secure secret
                'Badr Client Application',
                'http://localhost:8080',
                json.dumps([os.getenv('CLIENT_REDIRECT_URI', 'http://localhost:8080/badr_client_app.html')]),
                json.dumps(['authorization_code']),
                json.dumps(['code']),
                'client_secret_basic',
                json.dumps(['profile', 'read:orders', 'write:orders'])
            ))
        
        conn.commit()
        conn.close()
    
    def create_default_users(self):
        """Create default users if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Default users with bcrypt hashed passwords
        default_users = [
            ('alice', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S', 
             'alice@example.com', 'Alice Johnson', ['user']),
            ('bob', '$2b$12$hR0cc5Kx9o20/9nWpUFZO.F7.CL3MAo0BqHnTYGwWs/S9sH78pB9O',
             'bob@example.com', 'Bob Smith', ['user']),
            ('admin', '$2b$12$k.4cJJ96/D8x7fHIC9i9JeQ.QpB2QD2V8H85Syq5aKK7Al7mlEFOa',
             'admin@example.com', 'Admin User', ['user', 'admin'])
        ]
        
        for username, password_hash, email, name, roles in default_users:
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, name, roles)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, password_hash, email, name, json.dumps(roles)))
        
        conn.commit()
        conn.close()
    
    def get_client(self, client_id):
        """Retrieve a client by client_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM clients WHERE client_id = ?', (client_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            client = dict(zip(columns, row))
            
            # Decode JSON fields
            client['redirect_uris'] = json.loads(client['redirect_uris'])
            client['grant_types'] = json.loads(client['grant_types'])
            client['response_types'] = json.loads(client['response_types'])
            client['scopes'] = json.loads(client['scopes'])
            
            return client
        
        conn.close()
        return None
    
    def create_client(self, client_data):
        """Create a new client"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO clients (
                client_id, client_secret, client_name, client_uri,
                redirect_uris, grant_types, response_types,
                token_endpoint_auth_method, scopes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            client_data['client_id'],
            client_data['client_secret'],
            client_data['client_name'],
            client_data['client_uri'],
            json.dumps(client_data['redirect_uris']),
            json.dumps(client_data['grant_types']),
            json.dumps(client_data['response_types']),
            client_data['token_endpoint_auth_method'],
            json.dumps(client_data['scopes'])
        ))
        
        conn.commit()
        conn.close()
        
        return client_data
    
    def get_user(self, username):
        """Retrieve a user by username"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            user = dict(zip(columns, row))
            
            # Decode JSON fields
            user['roles'] = json.loads(user['roles'])
            
            return user
        
        conn.close()
        return None
    
    def create_auth_request(self, code, client_id, user_info, scopes, redirect_uri, expires_in=300):
        """Create a new authorization request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        cursor.execute('''
            INSERT INTO auth_requests (code, client_id, user_info, scopes, redirect_uri, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            code,
            client_id,
            json.dumps(user_info),
            json.dumps(scopes),
            redirect_uri,
            expires_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_auth_request(self, code):
        """Retrieve an authorization request by code"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM auth_requests WHERE code = ?', (code,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            auth_request = dict(zip(columns, row))
            
            # Decode JSON fields
            auth_request['user_info'] = json.loads(auth_request['user_info'])
            auth_request['scopes'] = json.loads(auth_request['scopes'])
            
            # Convert expires_at to datetime
            auth_request['expires_at'] = datetime.fromisoformat(auth_request['expires_at'])
            
            return auth_request
        
        conn.close()
        return None
    
    def delete_auth_request(self, code):
        """Delete an authorization request by code"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM auth_requests WHERE code = ?', (code,))
        
        conn.commit()
        conn.close()
    
    def create_refresh_token(self, token, user_info, scopes, expires_in=86400):  # 24 hours
        """Create a new refresh token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(seconds=expires_in)
        
        cursor.execute('''
            INSERT INTO refresh_tokens (token, user_info, scopes, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            token,
            json.dumps(user_info),
            json.dumps(scopes),
            created_at.isoformat(),
            expires_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_refresh_token(self, token):
        """Retrieve a refresh token by token value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM refresh_tokens WHERE token = ?', (token,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            refresh_token = dict(zip(columns, row))
            
            # Decode JSON fields
            refresh_token['user_info'] = json.loads(refresh_token['user_info'])
            refresh_token['scopes'] = json.loads(refresh_token['scopes'])
            
            # Convert timestamps to datetime
            refresh_token['created_at'] = datetime.fromisoformat(refresh_token['created_at'])
            refresh_token['expires_at'] = datetime.fromisoformat(refresh_token['expires_at'])
            
            return refresh_token
        
        conn.close()
        return None
    
    def delete_refresh_token(self, token):
        """Delete a refresh token by token value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM refresh_tokens WHERE token = ?', (token,))
        
        conn.commit()
        conn.close()
    
    def cleanup_expired_auth_requests(self):
        """Remove expired authorization requests"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM auth_requests WHERE expires_at < ?', (datetime.utcnow().isoformat(),))
        
        conn.commit()
        conn.close()
    
    def cleanup_expired_refresh_tokens(self):
        """Remove expired refresh tokens"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM refresh_tokens WHERE expires_at < ?', (datetime.utcnow().isoformat(),))
        
        conn.commit()
        conn.close()


# Global database instance
db = Database()
"""
User management module for OAuth2 Authorization Server
Provides secure password hashing and user management functions
"""
import bcrypt
import sqlite3
from db import db


class UserManager:
    def __init__(self):
        pass
    
    def hash_password(self, password):
        """
        Hash a password using bcrypt
        
        Args:
            password (str): Plain text password
            
        Returns:
            str: Hashed password
        """
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password, hashed_password):
        """
        Verify a password against its hash
        
        Args:
            password (str): Plain text password
            hashed_password (str): Hashed password
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def create_user(self, username, password, email, name, roles=None):
        """
        Create a new user with secure password hashing
        
        Args:
            username (str): Unique username
            password (str): Plain text password
            email (str): User's email
            name (str): User's full name
            roles (list): List of user roles
            
        Returns:
            dict: User data
        """
        if roles is None:
            roles = ['user']
            
        # Hash the password
        password_hash = self.hash_password(password)
        
        # Prepare user data
        user_data = {
            'username': username,
            'password_hash': password_hash,
            'email': email,
            'name': name,
            'roles': roles
        }
        
        # Store user in database (this would be implemented in db.py)
        # For now, we'll just return the user data
        return user_data
    
    def update_user_password(self, username, new_password):
        """
        Update a user's password
        
        Args:
            username (str): Username
            new_password (str): New plain text password
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Hash the new password
        new_password_hash = self.hash_password(new_password)
        
        # Update in database
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET password_hash = ? 
                WHERE username = ?
            ''', (new_password_hash, username))
            
            conn.commit()
            success = cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating password: {e}")
            success = False
        finally:
            conn.close()
        
        return success
    
    def get_user(self, username):
        """
        Retrieve a user by username
        
        Args:
            username (str): Username
            
        Returns:
            dict: User data or None if not found
        """
        return db.get_user(username)


# Global user manager instance
user_manager = UserManager()
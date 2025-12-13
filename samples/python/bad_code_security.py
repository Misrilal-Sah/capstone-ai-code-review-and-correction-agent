"""
Sample Bad Python Code #1: Security Issues

This file contains intentionally bad code for testing the AI Code Review Agent.
Issues: SQL injection, hardcoded secrets, bare except, missing docstrings
"""

import os
import sys
import json  # Unused import
import requests  # Unused import

# SECURITY ISSUE: Hardcoded credentials
DATABASE_PASSWORD = "admin123"
API_KEY = "sk-abcdefghijklmnopqrstuvwxyz123456"
SECRET_TOKEN = "super_secret_token_here"

def get_user(user_id):
    # SECURITY ISSUE: SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    # SECURITY ISSUE: Another SQL injection
    name = input("Enter name: ")
    query2 = "SELECT * FROM users WHERE name = '%s'" % name
    cursor.execute(query2)
    
    return cursor.fetchone()

def authenticate(username, password):
    # Missing docstring
    # SECURITY ISSUE: Comparing password in plain text
    if password == "admin123":
        return True
    
    # ISSUE: Bare except clause
    try:
        result = database.check_credentials(username, password)
    except:
        pass
    
    return result

def process_data(items=[]):  # ISSUE: Mutable default argument
    global counter  # ISSUE: Using global
    counter = 0
    
    for item in items:
        print(item)  # ISSUE: Using print instead of logging
    
    return counter

class UserManager:
    def delete_user(self, user_id):
        # SECURITY ISSUE: No authorization check
        # SECURITY ISSUE: SQL Injection
        query = f"DELETE FROM users WHERE id = {user_id}"
        cursor.execute(query)
        print(f"User {user_id} deleted")  # Logging sensitive info

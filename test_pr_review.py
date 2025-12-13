"""
Test File for PR Review Testing
This file contains intentional code issues for testing the AI Code Review Agent.
"""

import os
import sys

# Hardcoded credentials (SECURITY ISSUE)
DATABASE_PASSWORD = "admin123"
API_SECRET_KEY = "sk-12345-secret-key"

def process_user_data(user_id, data=[]):  # Mutable default argument (BUG)
    """Process user data from database."""
    
    # SQL Injection vulnerability (SECURITY)
    query = f"SELECT * FROM users WHERE id = {user_id}"
    
    # Bare except (BAD PRACTICE)
    try:
        result = execute_query(query)
        data.append(result)
    except:
        pass  # Silent failure
    
    return data


def calculate_total(items):
    # Missing docstring
    # Deeply nested code (CODE SMELL)
    total = 0
    for item in items:
        if item:
            if 'price' in item:
                if item['price'] > 0:
                    if 'quantity' in item:
                        if item['quantity'] > 0:
                            total += item['price'] * item['quantity']
    return total


class UserManager:
    # Missing class docstring
    
    def __init__(self):
        self.users = []
        self.password = "hardcoded123"  # Hardcoded secret
    
    def get_user(self, id):
        # Using built-in name 'id' as parameter
        for u in self.users:
            if u.id == id:
                return u
        return None
    
    def delete_all_users(self):
        # Dangerous operation without confirmation
        self.users = []
        os.system("rm -rf /tmp/user_data")  # Shell injection risk


# Global variable (BAD PRACTICE)
GLOBAL_COUNTER = 0

def increment():
    global GLOBAL_COUNTER
    GLOBAL_COUNTER += 1

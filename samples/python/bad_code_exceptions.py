"""
Sample Bad Python Code #3: Exception Handling

This file contains intentionally bad code for testing the AI Code Review Agent.
Issues: Bare except, silent failures, poor exception handling
"""

import json
import os

def read_config(path):
    # Missing docstring
    try:
        with open(path) as f:
            return json.load(f)
    except:  # ISSUE: Bare except
        pass  # ISSUE: Silent failure

def process_file(filename):
    try:
        data = open(filename).read()  # ISSUE: File not closed properly
        result = json.loads(data)
    except Exception as e:  # Too broad exception
        print(f"Error: {e}")  # ISSUE: Using print, not logging
        return None
    except:  # ISSUE: Bare except after specific exception
        pass
    return result

def divide(a, b):
    try:
        return a / b
    except:
        return 0  # ISSUE: Hiding the error, returning wrong value

def connect_database():
    # Multiple issues with exception handling
    try:
        connection = database.connect(
            host="localhost",
            password="hardcoded123"  # SECURITY: Hardcoded password
        )
    except Exception:
        pass  # Silent failure - connection errors ignored
    except:
        pass  # Another bare except
    
    return connection  # May reference undefined variable

class DataLoader:
    def load(self, source):
        # No docstring
        try:
            if source.startswith("http"):
                data = requests.get(source).json()
            else:
                with open(source) as f:
                    data = json.load(f)
        except:
            data = {}  # Silent failure, returning empty dict
        
        return data
    
    def save(self, data, path):
        try:
            with open(path, "w") as f:
                json.dump(data, f)
        except PermissionError:
            pass  # Ignoring permission errors
        except IOError:
            pass  # Ignoring IO errors
        except:
            pass  # Catching everything else

def risky_operation():
    # FIXME: This function swallows all exceptions
    try:
        result = external_service.call()
        processed = process(result)
        saved = save_to_database(processed)
        return saved
    except:
        # This hides ALL errors - network, processing, database, everything
        return None

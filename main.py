# main.py
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Now import the WSGI application
from core.wsgi import application

# App Engine uses the variable named 'app'
app = application

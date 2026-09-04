"""Configuration for Personal PaaS Controller"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Server
    PORT = int(os.environ.get('PORT', 10000))
    HOST = '0.0.0.0'
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'personal-paas-secret-key')
    
    # Render API
    RENDER_API_KEY = os.environ.get('RENDER_API_KEY', '')
    RENDER_API_BASE = 'https://api.render.com/v1'
    
    # GitHub API
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
    GITHUB_API_BASE = 'https://api.github.com'
    
    # Storage
    PROJECTS_FILE = 'data/projects.json'
    LOGS_FILE = 'data/logs.json'
    
    # Default deploy settings
    DEFAULT_RUNTIME = 'python'
    DEFAULT_BUILD_COMMAND = 'pip install -r requirements.txt'
    DEFAULT_START_COMMAND = 'gunicorn app:app --bind 0.0.0.0:$PORT'
    
    # Self-ping (keep controller alive)
    PING_INTERVAL = 600  # 10 minutes
    RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:10000')

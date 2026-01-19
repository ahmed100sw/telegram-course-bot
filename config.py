import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Web App Configuration
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:5000')
WEBAPP_HOST = os.getenv('WEBAPP_HOST', '0.0.0.0')
WEBAPP_PORT = int(os.getenv('WEBAPP_PORT', 5000))

# Token Configuration
TOKEN_EXPIRY_HOURS = int(os.getenv('TOKEN_EXPIRY_HOURS', 24))

# Database Configuration
DATABASE_PATH = 'data/bot.db'

# Directories
VIDEOS_DIR = 'videos'
DATA_DIR = 'data'

# Ensure directories exist
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

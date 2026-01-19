import asyncio
import threading
import os
import sys

def run_bot():
    """Run the Telegram bot"""
    print("Starting Telegram bot...")
    os.system('python bot.py')

def run_webapp():
    """Run the Flask web app"""
    print("Starting Web App...")
    os.system('python webapp/server.py')

if __name__ == '__main__':
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Run webapp in main thread
    run_webapp()

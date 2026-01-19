from flask import Flask, render_template, jsonify, send_file, request, Response
import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path to import database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from database import db

app = Flask(__name__, 
            template_folder='.',
            static_folder='static')


def get_event_loop():
    """Get or create event loop"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


@app.route('/')
def index():
    """Serve the Web App"""
    return render_template('index.html')


@app.route('/watch')
def watch():
    """Watch page (same as index)"""
    return render_template('index.html')


@app.route('/api/video/<token>')
def validate_video_token(token):
    """Validate token and return video info"""
    loop = get_event_loop()
    
    # Validate token
    video_info = loop.run_until_complete(db.validate_token(token))
    
    if not video_info:
        return jsonify({'error': 'رمز الوصول غير صحيح أو منتهي الصلاحية'}), 404
    
    return jsonify({
        'title': video_info['title'],
        'episode_id': video_info['episode_id']
    })


@app.route('/api/stream/<token>')
def stream_video(token):
    """Stream video file with token validation"""
    loop = get_event_loop()
    
    # Validate token
    video_info = loop.run_until_complete(db.validate_token(token))
    
    if not video_info:
        return jsonify({'error': 'رمز الوصول غير صحيح أو منتهي الصلاحية'}), 404
    
    # Additional device check (server-side)
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Check if request is from mobile
    is_mobile = any(device in user_agent for device in ['android', 'iphone', 'ipad', 'mobile'])
    
    # Block desktop browsers (additional server-side check)
    if not is_mobile and 'telegram' not in user_agent:
        return jsonify({'error': 'يمكن المشاهدة فقط من الهاتف المحمول'}), 403
    
    video_path = video_info['video_path']
    
    # Check if video_path is a file_id (Telegram file)
    # In this case, we need to download from Telegram
    # For now, we'll assume videos are stored locally
    # You can extend this to download from Telegram Bot API
    
    # For demonstration, return a placeholder response
    # In production, you would:
    # 1. Download video from Telegram using file_id
    # 2. Stream it to the user
    # 3. Or store videos locally and stream from disk
    
    return jsonify({
        'error': 'تنفيذ البث قيد التطوير. يرجى تحميل الفيديوهات محلياً.',
        'note': 'في الإنتاج، سيتم تحميل الفيديو من تلغرام أو من التخزين المحلي'
    }), 501


@app.route('/api/stream/local/<token>')
def stream_local_video(token):
    """Stream locally stored video file"""
    loop = get_event_loop()
    
    # Validate token
    video_info = loop.run_until_complete(db.validate_token(token))
    
    if not video_info:
        return jsonify({'error': 'رمز الوصول غير صحيح أو منتهي الصلاحية'}), 404
    
    # Get video file path (assuming it's stored in videos directory)
    # This is for locally stored videos, not Telegram file_ids
    video_filename = video_info.get('video_path')
    video_file_path = os.path.join(config.VIDEOS_DIR, video_filename)
    
    if not os.path.exists(video_file_path):
        return jsonify({'error': 'الفيديو غير موجود'}), 404
    
    # Get file size
    file_size = os.path.getsize(video_file_path)
    
    # Handle range requests for video streaming
    range_header = request.headers.get('Range', None)
    
    if range_header:
        # Parse range header
        byte_range = range_header.replace('bytes=', '').split('-')
        start = int(byte_range[0]) if byte_range[0] else 0
        end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
        length = end - start + 1
        
        # Read file chunk
        with open(video_file_path, 'rb') as f:
            f.seek(start)
            data = f.read(length)
        
        # Return partial content
        response = Response(
            data,
            206,
            mimetype='video/mp4',
            direct_passthrough=True
        )
        response.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
        response.headers.add('Accept-Ranges', 'bytes')
        response.headers.add('Content-Length', str(length))
        return response
    else:
        # Return full file
        return send_file(
            video_file_path,
            mimetype='video/mp4',
            as_attachment=False
        )


async def init_database():
    """Initialize database"""
    await db.init_db()
    print("Database initialized!")


if __name__ == '__main__':
    # Initialize database
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_database())
    
    # Run Flask app
    print(f"Starting Web App server on {config.WEBAPP_HOST}:{config.WEBAPP_PORT}")
    print(f"Web App URL: {config.WEBAPP_URL}")
    app.run(
        host=config.WEBAPP_HOST,
        port=config.WEBAPP_PORT,
        debug=True
    )

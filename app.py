# =================================================================
# Production-Ready Real-Time YOLOv10 Object Detection Web App
#
# Features:
# - Secure HTTPS with self-signed SSL
# - Real-time camera detection on any device
# - Feedback-based learning with dataset management
# - Optimized YOLOv10 inference with FP16
# - Modular, maintainable code structure
# =================================================================

from flask import Flask, render_template, request, jsonify, send_from_directory
import base64
import cv2
import os
import logging
from datetime import datetime
from detection import load_model, process_frame, get_detections, class_names
from utils import generate_self_signed_cert, get_local_ip
from feedback import save_frame_for_training, get_training_data, delete_sample
from data.database import get_database, LeaderboardDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Initialize Flask App ---
app = Flask(__name__)

# --- Initialize Database with fallback ---
try:
    db = get_database()
    logger.info("Database initialized successfully with connection pool")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    # Fallback to basic database if pool initialization fails
    db = LeaderboardDB()
    logger.warning("Using fallback database instance")

# --- Load Model ---
load_model()
logger.info("YOLO model loaded successfully")

# --- Leaderboard API Routes ---
@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top players from leaderboard"""
    try:
        limit = request.args.get('limit', 20, type=int)
        players = db.get_top_players(limit)
        return jsonify({
            'success': True,
            'players': players,
            'total_players': db.get_total_players()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'players': []
        }), 500

@app.route('/api/leaderboard', methods=['POST'])
def update_leaderboard():
    """Update player score in leaderboard"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        score = data.get('score', 0)
        games_played = data.get('games_played', 1)
        objects_discovered = data.get('objects_discovered', 1)
        
        if not name or not isinstance(score, int) or score < 0:
            return jsonify({
                'success': False,
                'error': 'Invalid name or score'
            }), 400
        
        success = db.add_or_update_player(name, score, games_played, objects_discovered)
        if success:
            player_rank = db.get_player_rank(name)
            return jsonify({
                'success': True,
                'message': 'Player updated successfully',
                'player': player_rank
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update player'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leaderboard/player/<name>', methods=['GET'])
def get_player_rank(name):
    """Get specific player's rank and stats"""
    try:
        if not name:
            return jsonify({
                'success': False,
                'error': 'Player name required'
            }), 400
        
        player = db.get_player_rank(name)
        if player:
            return jsonify({
                'success': True,
                'player': player
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Player not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leaderboard/stats', methods=['GET'])
def get_leaderboard_stats():
    """Get leaderboard statistics"""
    try:
        stats = db.get_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leaderboard/recent', methods=['GET'])
def get_recent_activity():
    """Get recently active players"""
    try:
        limit = request.args.get('limit', 10, type=int)
        activity = db.get_recent_activity(limit)
        return jsonify({
            'success': True,
            'activity': activity
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leaderboard/clear', methods=['DELETE'])
def clear_leaderboard():
    """Clear all leaderboard data (admin only)"""
    try:
        # In production, you'd want to add proper authentication
        # For now, we'll add a simple token check
        auth_token = request.headers.get('Authorization', '')
        expected_token = os.environ.get('LEADERBOARD_CLEAR_TOKEN', 'objectquest-admin-2025')
        
        if auth_token != f'Bearer {expected_token}':
            return jsonify({
                'success': False,
                'error': 'Unauthorized: Invalid or missing token'
            }), 401
        
        success = db.clear_leaderboard()
        if success:
            return jsonify({
                'success': True,
                'message': 'Leaderboard cleared successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to clear leaderboard'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leaderboard/export', methods=['GET'])
def export_leaderboard():
    """Export complete leaderboard data as JSON for frontend"""
    try:
        include_stats = request.args.get('include_stats', 'true').lower() == 'true'
        export_data = db.export_to_json(include_stats=include_stats)
        
        return jsonify({
            'success': True,
            'data': export_data
        })
        
    except Exception as e:
        logger.error(f"Leaderboard export failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/leaderboard/optimize', methods=['POST'])
def optimize_database():
    """Optimize database performance (admin operation)"""
    try:
        # Simple token check for optimization endpoint
        auth_token = request.headers.get('Authorization', '')
        expected_token = os.environ.get('LEADERBOARD_CLEAR_TOKEN', 'objectquest-admin-2025')
        
        if auth_token != f'Bearer {expected_token}':
            return jsonify({
                'success': False,
                'error': 'Unauthorized: Invalid or missing token'
            }), 401
        
        success = db.optimize_database()
        if success:
            return jsonify({
                'success': True,
                'message': 'Database optimization completed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Database optimization failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Database and system health check"""
    try:
        # Check database health
        db_health = db.health_check()
        
        # Check disk space
        disk_usage = os.statvfs('.')
        free_space = disk_usage.f_bavail * disk_usage.f_frsize
        total_space = disk_usage.f_blocks * disk_usage.f_frsize
        disk_usage_percent = (free_space / total_space) * 100
        
        health_data = {
            'status': 'healthy' if db_health.get('status') == 'healthy' else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'database': db_health,
            'system': {
                'disk_usage_percent': round(disk_usage_percent, 2),
                'free_space_gb': round(free_space / (1024**3), 2),
                'total_space_gb': round(total_space / (1024**3), 2)
            }
        }
        
        status_code = 200 if health_data['status'] == 'healthy' else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dataset')
def dataset():
    data = get_training_data()
    return render_template('dataset.html', data=data)

@app.route('/process_frame', methods=['POST'])
def process_frame_route():
    data = request.json
    image_data = base64.b64decode(data['image'].split(',')[1])
    detections = get_detections(image_data)
    if detections is None:
        return jsonify({'error': 'Model not loaded'}), 500
    custom_names = list(class_names.values()) if isinstance(class_names, dict) else list(class_names)
    # Custom name changes
    if len(custom_names) > 67:
        custom_names[67] = 'mobile phone'
    return jsonify({
        'detections': detections,
        'class_names': custom_names
    })

@app.route('/save_frame', methods=['POST'])
def save_frame():
    data = request.json
    image_data = base64.b64decode(data['image'].split(',')[1])
    label_data = [list(map(float, line.split())) for line in data['label'].strip().split('\n') if line.strip()]
    save_frame_for_training(image_data, label_data)
    return jsonify({'status': 'success'})

@app.route('/delete_sample/<timestamp>', methods=['DELETE'])
def delete_sample_route(timestamp):
    delete_sample(timestamp)
    return jsonify({'status': 'success'})

@app.route('/export_dataset')
def export_dataset():
    # Create a zip file of the training_data directory
    import zipfile
    from io import BytesIO
    from flask import send_file

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk('training_data'):
            for file in files:
                zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), 'training_data'))
    memory_file.seek(0)
    return send_file(memory_file, download_name='training_data.zip', as_attachment=True)

@app.route('/training_data/<path:filename>')
def training_data_files(filename):
    return send_from_directory('training_data', filename)

if __name__ == '__main__':
    cert_file, key_file = generate_self_signed_cert()
    ssl_context = (cert_file, key_file)
    local_ip = get_local_ip()
    print("\n🚀 Secure HTTPS server is running! Access it from your browser:")
    print(f"   - On this PC: https://127.0.0.1:5000")
    print(f"   - On your Network (Phone/Other PC): https://{local_ip}:5000")
    print("\n⚠️ Your browser will show a security warning. This is NORMAL.")
    print("   Click 'Advanced', then 'Proceed to...' to continue.")
    app.run(host='0.0.0.0', port=5000, debug=False, ssl_context=ssl_context)
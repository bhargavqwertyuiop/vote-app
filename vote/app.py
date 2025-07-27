from flask import Flask, request, render_template, make_response, g, jsonify
from redis import Redis
import os
import socket
import random
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_connect_timeout=10, socket_timeout=10, retry_on_timeout=True)
    return g.redis

@app.route("/", methods=['POST','GET'])
def hello():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None

    if request.method == 'POST':
        try:
            redis = get_redis()
            vote = request.form['vote']
            
            # Validate vote
            if vote not in ['a', 'b']:
                logger.warning(f"Invalid vote received: {vote}")
                return make_response(render_template('index.html', 
                                                   option_a=option_a, 
                                                   option_b=option_b, 
                                                   hostname=hostname, 
                                                   vote=None,
                                                   error="Invalid vote option")), 400
            
            # Create vote data with timestamp
            vote_data = {
                'voter_id': voter_id,
                'vote': vote,
                'timestamp': datetime.now().isoformat(),
                'hostname': hostname
            }
            
            redis.lpush('votes', json.dumps(vote_data))
            logger.info(f"Vote recorded: {vote} from {voter_id}")
            
        except Exception as e:
            logger.error(f"Error recording vote: {e}")
            return make_response(render_template('index.html', 
                                               option_a=option_a, 
                                               option_b=option_b, 
                                               hostname=hostname, 
                                               vote=None,
                                               error="Failed to record vote")), 500

    resp = make_response(render_template('index.html',
                                        option_a=option_a, 
                                        option_b=option_b, 
                                        hostname=hostname, 
                                        vote=vote))
    resp.set_cookie('voter_id', voter_id)
    return resp

@app.route('/api/health')
def health():
    """Health check endpoint"""
    try:
        redis = get_redis()
        redis.ping()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'hostname': hostname,
            'redis': 'connected'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'hostname': hostname,
            'redis': 'disconnected',
            'error': str(e)
        }), 500

@app.route('/api/stats')
def stats():
    """Get voting statistics"""
    try:
        redis = get_redis()
        vote_count = redis.llen('votes')
        
        return jsonify({
            'total_votes': vote_count,
            'timestamp': datetime.now().isoformat(),
            'hostname': hostname
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@app.route('/api/vote', methods=['POST'])
def api_vote():
    """API endpoint for voting"""
    try:
        data = request.get_json()
        if not data or 'vote' not in data:
            return jsonify({'error': 'Vote option required'}), 400
            
        vote = data['vote']
        if vote not in ['a', 'b']:
            return jsonify({'error': 'Invalid vote option'}), 400
            
        voter_id = request.cookies.get('voter_id')
        if not voter_id:
            voter_id = hex(random.getrandbits(64))[2:-1]
            
        redis = get_redis()
        vote_data = {
            'voter_id': voter_id,
            'vote': vote,
            'timestamp': datetime.now().isoformat(),
            'hostname': hostname
        }
        
        redis.lpush('votes', json.dumps(vote_data))
        logger.info(f"API Vote recorded: {vote} from {voter_id}")
        
        resp = make_response(jsonify({
            'success': True,
            'vote': vote,
            'timestamp': datetime.now().isoformat()
        }))
        resp.set_cookie('voter_id', voter_id)
        return resp
        
    except Exception as e:
        logger.error(f"Error in API vote: {e}")
        return jsonify({'error': 'Failed to record vote'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)

# agent_bridge.py
import logging
from flask import Flask, request, send_from_directory, jsonify
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import traceback
import os
from agent_orchestrator import run_outlook_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('agent_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='/')

# Executor for running tasks with timeout
executor = ThreadPoolExecutor(max_workers=1)

@app.route('/')
def home():
    logger.info("Home endpoint accessed")
    return send_from_directory('.', 'index.html')  # Serve index.html

@app.route('/<path:path>')
def static_files(path):
    logger.info(f"Serving static file: {path}")
    return send_from_directory('.', path)  # Serve other static files

@app.route('/fallback/outlook', methods=['POST'])
def outlook_fallback():
    logger.info("Outlook fallback endpoint triggered")
    try:
        future = executor.submit(run_outlook_agent_wrapper)
        result = future.result(timeout=30)
        logger.info("Diagnostics completed successfully")
        return jsonify({"status": "success", "message": "Diagnostics completed"}), 200
    except TimeoutError:
        logger.error("Diagnostics timed out after 30 seconds")
        return jsonify({"status": "error", "message": "Operation timed out"}), 503
    except Exception as e:
        logger.error(f"Error in diagnostics: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500

@app.route('/fallback/outlook/logs', methods=['GET'])
def outlook_logs():
    logger.info("Outlook logs endpoint triggered")
    # Placeholder: Return dummy logs (replace with actual file reading logic)
    return jsonify({"status": "success", "data": "No logs available yet"}), 200

@app.route('/fallback/outlook/registry', methods=['GET'])
def outlook_registry():
    logger.info("Outlook registry endpoint triggered")
    # Placeholder: Return dummy registry data (replace with actual file reading logic)
    return jsonify({"status": "success", "data": "No registry data available yet"}), 200

def run_outlook_agent_wrapper():
    """Wrapper to handle import and execution of run_outlook_agent"""
    try:
        run_outlook_agent()
    except ImportError as e:
        raise ImportError(f"Failed to import agent_orchestrator: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to run outlook agent: {str(e)}")

@app.route('/favicon.ico')
def favicon():
    logger.debug("Favicon requested")
    return '', 404

if __name__ == "__main__":
    logger.info("Starting Flask server on http://127.0.0.1:5000")
    app.run(port=5000, debug=True, threaded=True)
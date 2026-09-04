"""Personal PaaS Controller - Main Server"""

import threading
import time
import json
import logging
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from config import Config
from storage.project_store import ProjectStore
from github.client import GitHubClient
from render_api.client import RenderClient
from deploy.manager import DeployManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/*": {"origins": "*"}})

config = Config()
project_store = ProjectStore(config)
github_client = GitHubClient(config)
render_client = RenderClient(config)
deploy_manager = DeployManager(config, project_store, github_client, render_client)

active_clients = {}
clients_lock = threading.Lock()


@app.before_request
def before_request():
    client_id = request.headers.get('X-Client-ID')
    if client_id:
        with clients_lock:
            active_clients[client_id] = time.time()


# ==================== HEALTH ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'activeClients': len(active_clients),
        'timestamp': datetime.now().isoformat(),
        'projectsCount': len(project_store.get_all_projects()),
        'renderApiConfigured': bool(config.RENDER_API_KEY),
        'githubConfigured': bool(config.GITHUB_TOKEN)
    })


# ==================== PROJECTS ====================

@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all deployed projects"""
    projects = project_store.get_all_projects()
    return jsonify({'projects': projects, 'count': len(projects)})


@app.route('/api/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project"""
    project = project_store.get_project(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify(project)


@app.route('/api/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project"""
    project = project_store.get_project(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Delete from Render if it has a service ID
    if project.get('render_service_id'):
        render_client.delete_service(project['render_service_id'])
    
    project_store.delete_project(project_id)
    return jsonify({'status': 'deleted', 'projectId': project_id})


# ==================== GITHUB ====================

@app.route('/api/github/repos', methods=['GET'])
def list_github_repos():
    """List user's GitHub repositories"""
    if not config.GITHUB_TOKEN:
        return jsonify({'error': 'GitHub token not configured'}), 400
    
    repos = github_client.list_repositories()
    return jsonify({'repos': repos, 'count': len(repos)})


@app.route('/api/github/repos/<repo_name>', methods=['GET'])
def get_github_repo(repo_name):
    """Get details of a specific GitHub repo"""
    if not config.GITHUB_TOKEN:
        return jsonify({'error': 'GitHub token not configured'}), 400
    
    repo = github_client.get_repository(repo_name)
    if not repo:
        return jsonify({'error': 'Repository not found'}), 404
    return jsonify(repo)


@app.route('/api/github/branches/<repo_name>', methods=['GET'])
def list_branches(repo_name):
    """List branches for a repository"""
    if not config.GITHUB_TOKEN:
        return jsonify({'error': 'GitHub token not configured'}), 400
    
    branches = github_client.list_branches(repo_name)
    return jsonify({'branches': branches})


# ==================== DEPLOY ====================

@app.route('/api/deploy', methods=['POST'])
def deploy_project():
    """Deploy a GitHub repo to Render"""
    data = request.json or {}
    
    required_fields = ['name', 'repo_url']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    result = deploy_manager.deploy(data)
    
    if result.get('status') == 'success':
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@app.route('/api/deploy/<deploy_id>/status', methods=['GET'])
def deploy_status(deploy_id):
    """Get deploy status"""
    status = deploy_manager.get_deploy_status(deploy_id)
    if not status:
        return jsonify({'error': 'Deploy not found'}), 404
    return jsonify(status)


# ==================== LOGS ====================

@app.route('/api/projects/<project_id>/logs', methods=['GET'])
def get_project_logs(project_id):
    """Get logs for a project"""
    project = project_store.get_project(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    logs = project_store.get_logs(project_id)
    return jsonify({'projectId': project_id, 'logs': logs})


@app.route('/api/projects/<project_id>/logs/render', methods=['GET'])
def get_render_logs(project_id):
    """Get live logs from Render"""
    project = project_store.get_project(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if not project.get('render_service_id'):
        return jsonify({'error': 'No Render service ID'}), 400
    
    logs = render_client.get_service_logs(project['render_service_id'])
    return jsonify({'projectId': project_id, 'renderLogs': logs})


# ==================== SERVICE CONTROL ====================

@app.route('/api/projects/<project_id>/stop', methods=['POST'])
def stop_project(project_id):
    """Stop/suspend a project"""
    project = project_store.get_project(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if project.get('render_service_id'):
        render_client.suspend_service(project['render_service_id'])
    
    project_store.update_project_status(project_id, 'stopped')
    return jsonify({'status': 'stopped', 'projectId': project_id})


@app.route('/api/projects/<project_id>/start', methods=['POST'])
def start_project(project_id):
    """Start/resume a project"""
    project = project_store.get_project(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if project.get('render_service_id'):
        render_client.resume_service(project['render_service_id'])
    
    project_store.update_project_status(project_id, 'started')
    return jsonify({'status': 'started', 'projectId': project_id})


@app.route('/api/projects/<project_id>/restart', methods=['POST'])
def restart_project(project_id):
    """Restart/redeploy a project"""
    project = project_store.get_project(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if project.get('render_service_id'):
        render_client.trigger_deploy(project['render_service_id'])
    
    project_store.update_project_status(project_id, 'deploying')
    return jsonify({'status': 'redeploying', 'projectId': project_id})


# ==================== RENDER STATUS ====================

@app.route('/api/render/services', methods=['GET'])
def list_render_services():
    """List all services on Render"""
    if not config.RENDER_API_KEY:
        return jsonify({'error': 'Render API key not configured'}), 400
    
    services = render_client.list_services()
    return jsonify({'services': services})


@app.route('/api/render/services/<service_id>', methods=['GET'])
def get_render_service(service_id):
    """Get a specific Render service"""
    if not config.RENDER_API_KEY:
        return jsonify({'error': 'Render API key not configured'}), 400
    
    service = render_client.get_service(service_id)
    return jsonify(service)


# ==================== SETTINGS ====================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings"""
    return jsonify({
        'renderApiConfigured': bool(config.RENDER_API_KEY),
        'githubConfigured': bool(config.GITHUB_TOKEN),
        'defaultRuntime': config.DEFAULT_RUNTIME,
        'defaultBuildCommand': config.DEFAULT_BUILD_COMMAND,
        'defaultStartCommand': config.DEFAULT_START_COMMAND
    })


@app.route('/api/settings/validate', methods=['POST'])
def validate_settings():
    """Validate API keys"""
    data = request.json or {}
    results = {}
    
    if data.get('render_api_key'):
        results['render'] = render_client.validate_key(data['render_api_key'])
    
    if data.get('github_token'):
        results['github'] = github_client.validate_token(data['github_token'])
    
    return jsonify(results)


# ==================== REGISTER/HEARTBEAT ====================

@app.route('/api/register', methods=['POST'])
def register_client():
    data = request.json or {}
    client_id = data.get('clientId', f"client-{int(time.time())}")
    with clients_lock:
        active_clients[client_id] = time.time()
    return jsonify({'status': 'registered', 'clientId': client_id})


@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json or {}
    client_id = data.get('clientId')
    if client_id:
        with clients_lock:
            active_clients[client_id] = time.time()
    return jsonify({'status': 'alive', 'activeClients': len(active_clients)})


# ==================== WEB UI ====================

@app.route('/', methods=['GET'])
def web_ui():
    return send_from_directory('data/web_ui', 'index.html')


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal error: {e}")
    return jsonify({'error': 'Internal server error'}), 500


# ==================== SELF-PING ====================

def self_ping_loop():
    """Keep the controller alive"""
    while True:
        try:
            import requests
            requests.get(f"{config.RENDER_URL}/api/health", timeout=10)
        except:
            pass
        time.sleep(config.PING_INTERVAL)


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/web_ui', exist_ok=True)
    
    # Start self-ping thread
    ping_thread = threading.Thread(target=self_ping_loop, daemon=True)
    ping_thread.start()
    
    logger.info(f"Personal PaaS Controller starting on port {config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, threaded=True)

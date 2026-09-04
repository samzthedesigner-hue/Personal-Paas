"""Deploy Manager - Handles project deployment"""

import logging
import uuid
import threading
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class DeployManager:
    def __init__(self, config, project_store, github_client, render_client):
        self.config = config
        self.project_store = project_store
        self.github_client = github_client
        self.render_client = render_client
        self.deploys = {}
        self.deploy_lock = threading.Lock()
    
    def deploy(self, data: Dict) -> Dict:
        """Deploy a GitHub repo to Render"""
        deploy_id = str(uuid.uuid4())[:16]
        
        # Create project record
        project = {
            'id': deploy_id,
            'name': data['name'],
            'repo_url': data['repo_url'],
            'branch': data.get('branch', 'main'),
            'runtime': data.get('runtime', self.config.DEFAULT_RUNTIME),
            'build_command': data.get('build_command', self.config.DEFAULT_BUILD_COMMAND),
            'start_command': data.get('start_command', self.config.DEFAULT_START_COMMAND),
            'status': 'deploying',
            'created_at': datetime.now().isoformat(),
            'deploy_id': deploy_id,
            'render_service_id': None,
            'url': None
        }
        
        # Save to store
        self.project_store.save_project(project)
        self.project_store.add_log(deploy_id, f"Starting deployment for {data['name']}")
        
        # Create service on Render
        if self.config.RENDER_API_KEY:
            service_data = {
                'type': 'web_service',
                'name': data['name'],
                'repo': data['repo_url'],
                'branch': data.get('branch', 'main'),
                'runtime': data.get('runtime', self.config.DEFAULT_RUNTIME),
                'buildCommand': data.get('build_command', self.config.DEFAULT_BUILD_COMMAND),
                'startCommand': data.get('start_command', self.config.DEFAULT_START_COMMAND)
            }
            
            service = self.render_client.create_service(service_data)
            
            if service:
                project['render_service_id'] = service.get('id')
                project['url'] = service.get('serviceDetails', {}).get('url', '')
                project['status'] = 'live'
                self.project_store.save_project(project)
                self.project_store.add_log(deploy_id, f"Render service created: {project['url']}")
            else:
                project['status'] = 'failed'
                self.project_store.save_project(project)
                self.project_store.add_log(deploy_id, "Failed to create Render service", 'error')
        else:
            # Simulated deploy (no Render API key)
            project['status'] = 'deployed_simulated'
            project['url'] = f"https://{data['name']}.onrender.com"
            self.project_store.save_project(project)
            self.project_store.add_log(deploy_id, f"Simulated deploy (no Render API key). URL would be: {project['url']}")
        
        with self.deploy_lock:
            self.deploys[deploy_id] = project
        
        return {
            'status': 'success',
            'projectId': deploy_id,
            'name': data['name'],
            'url': project.get('url'),
            'renderServiceId': project.get('render_service_id')
        }
    
    def get_deploy_status(self, deploy_id: str) -> Optional[Dict]:
        """Get deploy status"""
        with self.deploy_lock:
            deploy = self.deploys.get(deploy_id)
        
        if not deploy:
            # Check project store
            deploy = self.project_store.get_project(deploy_id)
        
        return deploy

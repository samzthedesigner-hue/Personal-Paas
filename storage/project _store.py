"""Local storage for projects and logs"""

import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional

class ProjectStore:
    def __init__(self, config):
        self.config = config
        self.projects_file = config.PROJECTS_FILE
        self.logs_file = config.LOGS_FILE
        self.lock = threading.Lock()
        
        # Initialize storage
        os.makedirs(os.path.dirname(self.projects_file), exist_ok=True)
        
        if not os.path.exists(self.projects_file):
            with open(self.projects_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.logs_file):
            with open(self.logs_file, 'w') as f:
                json.dump({}, f)
    
    def get_all_projects(self) -> List[Dict]:
        with self.lock:
            with open(self.projects_file, 'r') as f:
                projects = json.load(f)
            return list(projects.values())
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        with self.lock:
            with open(self.projects_file, 'r') as f:
                projects = json.load(f)
            return projects.get(project_id)
    
    def save_project(self, project: Dict) -> bool:
        with self.lock:
            with open(self.projects_file, 'r') as f:
                projects = json.load(f)
            projects[project['id']] = project
            with open(self.projects_file, 'w') as f:
                json.dump(projects, f, indent=2)
        return True
    
    def delete_project(self, project_id: str) -> bool:
        with self.lock:
            with open(self.projects_file, 'r') as f:
                projects = json.load(f)
            if project_id in projects:
                del projects[project_id]
                with open(self.projects_file, 'w') as f:
                    json.dump(projects, f, indent=2)
                return True
        return False
    
    def update_project_status(self, project_id: str, status: str) -> bool:
        with self.lock:
            with open(self.projects_file, 'r') as f:
                projects = json.load(f)
            if project_id in projects:
                projects[project_id]['status'] = status
                projects[project_id]['last_updated'] = datetime.now().isoformat()
                with open(self.projects_file, 'w') as f:
                    json.dump(projects, f, indent=2)
                return True
        return False
    
    def add_log(self, project_id: str, message: str, level: str = 'info') -> bool:
        with self.lock:
            with open(self.logs_file, 'r') as f:
                logs = json.load(f)
            if project_id not in logs:
                logs[project_id] = []
            logs[project_id].append({
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message
            })
            # Keep only last 100 logs
            logs[project_id] = logs[project_id][-100:]
            with open(self.logs_file, 'w') as f:
                json.dump(logs, f, indent=2)
        return True
    
    def get_logs(self, project_id: str) -> List[Dict]:
        with self.lock:
            with open(self.logs_file, 'r') as f:
                logs = json.load(f)
            return logs.get(project_id, [])
    
    def clear_logs(self, project_id: str) -> bool:
        with self.lock:
            with open(self.logs_file, 'r') as f:
                logs = json.load(f)
            if project_id in logs:
                logs[project_id] = []
                with open(self.logs_file, 'w') as f:
                    json.dump(logs, f, indent=2)
                return True
        return False

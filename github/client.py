"""GitHub API Client"""

import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class GitHubClient:
    def __init__(self, config):
        self.config = config
        self.token = config.GITHUB_TOKEN
        self.api_base = config.GITHUB_API_BASE
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        } if self.token else {}
    
    def list_repositories(self) -> List[Dict]:
        """List user's repositories"""
        if not self.token:
            return []
        
        try:
            response = requests.get(
                f"{self.api_base}/user/repos",
                headers=self.headers,
                params={'per_page': 100, 'sort': 'updated'}
            )
            response.raise_for_status()
            repos = response.json()
            
            return [
                {
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'clone_url': repo['clone_url'],
                    'html_url': repo['html_url'],
                    'description': repo.get('description', ''),
                    'language': repo.get('language', ''),
                    'default_branch': repo['default_branch'],
                    'private': repo['private'],
                    'updated_at': repo['updated_at']
                }
                for repo in repos
            ]
        except Exception as e:
            logger.error(f"Failed to list repos: {e}")
            return []
    
    def get_repository(self, repo_name: str) -> Optional[Dict]:
        """Get a specific repository"""
        if not self.token:
            return None
        
        try:
            # Try to get username first
            user_response = requests.get(
                f"{self.api_base}/user",
                headers=self.headers
            )
            user_response.raise_for_status()
            username = user_response.json()['login']
            
            response = requests.get(
                f"{self.api_base}/repos/{username}/{repo_name}",
                headers=self.headers
            )
            response.raise_for_status()
            repo = response.json()
            
            return {
                'name': repo['name'],
                'full_name': repo['full_name'],
                'clone_url': repo['clone_url'],
                'html_url': repo['html_url'],
                'description': repo.get('description', ''),
                'language': repo.get('language', ''),
                'default_branch': repo['default_branch'],
                'private': repo['private']
            }
        except Exception as e:
            logger.error(f"Failed to get repo {repo_name}: {e}")
            return None
    
    def list_branches(self, repo_name: str) -> List[str]:
        """List branches for a repository"""
        if not self.token:
            return []
        
        try:
            user_response = requests.get(
                f"{self.api_base}/user",
                headers=self.headers
            )
            username = user_response.json()['login']
            
            response = requests.get(
                f"{self.api_base}/repos/{username}/{repo_name}/branches",
                headers=self.headers
            )
            response.raise_for_status()
            branches = response.json()
            
            return [branch['name'] for branch in branches]
        except Exception as e:
            logger.error(f"Failed to list branches: {e}")
            return []
    
    def validate_token(self, token: str) -> bool:
        """Validate a GitHub token"""
        try:
            response = requests.get(
                f"{self.api_base}/user",
                headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
            )
            return response.status_code == 200
        except:
            return False

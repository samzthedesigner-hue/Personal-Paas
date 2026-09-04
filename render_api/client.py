"""Render API Client"""

import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class RenderClient:
    def __init__(self, config):
        self.config = config
        self.api_key = config.RENDER_API_KEY
        self.api_base = config.RENDER_API_BASE
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        } if self.api_key else {}
    
    def list_services(self) -> List[Dict]:
        """List all services on Render"""
        if not self.api_key:
            return []
        
        try:
            response = requests.get(
                f"{self.api_base}/services",
                headers=self.headers
            )
            response.raise_for_status()
            services = response.json()
            
            return [
                {
                    'id': service.get('id'),
                    'name': service.get('name'),
                    'type': service.get('type'),
                    'url': service.get('serviceDetails', {}).get('url', ''),
                    'status': service.get('suspended', 'unknown')
                }
                for service in services
            ]
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return []
    
    def get_service(self, service_id: str) -> Optional[Dict]:
        """Get a specific service"""
        if not self.api_key:
            return None
        
        try:
            response = requests.get(
                f"{self.api_base}/services/{service_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get service {service_id}: {e}")
            return None
    
    def create_service(self, service_data: Dict) -> Optional[Dict]:
        """Create a new service on Render"""
        if not self.api_key:
            return None
        
        try:
            response = requests.post(
                f"{self.api_base}/services",
                headers=self.headers,
                json=service_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create service: {e}")
            return None
    
    def delete_service(self, service_id: str) -> bool:
        """Delete a service"""
        if not self.api_key:
            return False
        
        try:
            response = requests.delete(
                f"{self.api_base}/services/{service_id}",
                headers=self.headers
            )
            return response.status_code == 204 or response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to delete service {service_id}: {e}")
            return False
    
    def suspend_service(self, service_id: str) -> bool:
        """Suspend a service"""
        if not self.api_key:
            return False
        
        try:
            response = requests.post(
                f"{self.api_base}/services/{service_id}/suspend",
                headers=self.headers
            )
            return response.status_code in [200, 202, 204]
        except Exception as e:
            logger.error(f"Failed to suspend service: {e}")
            return False
    
    def resume_service(self, service_id: str) -> bool:
        """Resume a service"""
        if not self.api_key:
            return False
        
        try:
            response = requests.post(
                f"{self.api_base}/services/{service_id}/resume",
                headers=self.headers
            )
            return response.status_code in [200, 202, 204]
        except Exception as e:
            logger.error(f"Failed to resume service: {e}")
            return False
    
    def trigger_deploy(self, service_id: str) -> bool:
        """Trigger a new deploy"""
        if not self.api_key:
            return False
        
        try:
            response = requests.post(
                f"{self.api_base}/services/{service_id}/deploys",
                headers=self.headers
            )
            return response.status_code in [200, 201, 202]
        except Exception as e:
            logger.error(f"Failed to trigger deploy: {e}")
            return False
    
    def get_service_logs(self, service_id: str) -> List[Dict]:
        """Get logs for a service"""
        if not self.api_key:
            return []
        
        try:
            response = requests.get(
                f"{self.api_base}/services/{service_id}/deploys",
                headers=self.headers
            )
            response.raise_for_status()
            deploys = response.json()
            
            if deploys:
                latest = deploys[0]
                logs_response = requests.get(
                    f"{self.api_base}/services/{service_id}/deploys/{latest['id']}",
                    headers=self.headers
                )
                logs_response.raise_for_status()
                return logs_response.json()
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
        
        return []
    
    def validate_key(self, api_key: str) -> bool:
        """Validate a Render API key"""
        try:
            response = requests.get(
                f"{self.api_base}/services",
                headers={'Authorization': f'Bearer {api_key}'}
            )
            return response.status_code == 200
        except:
            return False

from typing import Dict, List
import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class NotionClient:
    def __init__(self):
        self.api_key = os.getenv('NOTION_API_KEY')
        self.subprojects_db_id = os.getenv('NOTION_SUBPROJECTS_DB_ID')
        self.steps_db_id = os.getenv('NOTION_STEPS_DB_ID')
        self.projects_db_id = os.getenv('NOTION_PROJECTS_DB_ID')
        self.people_db_id = os.getenv('NOTION_PEOPLE_DB_ID')
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.base_url = "https://api.notion.com/v1"
        
        # Add this to debug the database structure
        self._debug_database_structure()

    def _debug_database_structure(self):
        """Debug helper to print out the actual database structure from Notion."""
        try:
            url = f"{self.base_url}/databases/{self.subprojects_db_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # properties = response.json().get('properties', {})
            # logger.info("Database properties:")
            # for prop_name, prop_details in properties.items():
                # logger.info(f"Property '{prop_name}' of type '{prop_details.get('type')}'")
            
        except Exception as e:
            logger.error(f"Error fetching database structure: {e}")
            if isinstance(e, requests.exceptions.HTTPError):
                logger.error(f"Response content: {e.response.content}")

    def _get_page_id_by_title(self, database_id: str, title: str) -> str:
        """Get Notion page ID by searching for its title in a database."""
        try:
            url = f"{self.base_url}/databases/{database_id}/query"
            data = {
                "filter": {
                    "property": "Name",
                    "title": {
                        "equals": title
                    }
                }
            }
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            results = response.json().get('results', [])
            if results:
                return results[0]['id']
            return None
        except Exception as e:
            logger.error(f"Error getting page ID for {title}: {e}")
            return None

    def create_subproject(self, mapped_task: Dict) -> bool:
        """Create a subproject in Notion with status 'potential'."""
        try:
            # Get related page IDs
            project_id = self._get_page_id_by_title(self.projects_db_id, mapped_task["project_display_name"])
            step_id = self._get_page_id_by_title(self.steps_db_id, mapped_task["step"])
            person_id = self._get_page_id_by_title(self.people_db_id, "Miles Porter")  # Hardcoded for now

            if not all([project_id, step_id, person_id]):
                logger.error("Failed to get all required page IDs")
                logger.error(f"Project ID: {project_id}, Step ID: {step_id}, Person ID: {person_id}")
                return False

            url = f"{self.base_url}/pages"
            data = {
                "parent": {"database_id": self.subprojects_db_id},
                "properties": {
                    "Sub-project": {
                        "title": [
                            {
                                "text": {
                                    "content": mapped_task["subproject"]
                                }
                            }
                        ]
                    },
                    "Status": {
                        "status": {
                            "name": "Potential"
                        }
                    },
                    "Project": {
                        "relation": [
                            {
                                "id": project_id
                            }
                        ]
                    },
                    "Step": {
                        "relation": [
                            {
                                "id": step_id
                            }
                        ]
                    },
                    "Team Comp": {
                        "relation": [
                            {
                                "id": person_id
                            }
                        ]
                    }
                }
            }

            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            logger.info(f"Created Notion subproject: {mapped_task['subproject']}")
            return True

        except Exception as e:
            logger.error(f"Error creating Notion subproject: {e}")
            if isinstance(e, requests.exceptions.HTTPError):
                logger.error(f"Response content: {e.response.content}")
            return False

    def create_subprojects(self, mapped_tasks: List[Dict]) -> List[Dict]:
        """Create multiple subprojects in Notion."""
        results = []
        for task in mapped_tasks:
            success = self.create_subproject(task)
            results.append({
                **task,
                "notion_created": success
            })
        return results 

    def create_webhook(self, url: str):
        """Create a new webhook in Notion."""
        try:
            webhook_url = f"{self.base_url}/webhooks"
            data = {
                "url": url,
                "events": ["page_properties_changed"]  # This will trigger when button properties change
            }
            
            response = requests.post(webhook_url, headers=self.headers, json=data)
            response.raise_for_status()
            
            logger.info(f"Created webhook: {response.json()}")
            return response.json()
            
        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            if isinstance(e, requests.exceptions.HTTPError):
                logger.error(f"Response content: {e.response.content}")
            return None

    def create_button_property(self, database_id: str):
        """Add a button property to a database."""
        try:
            url = f"{self.base_url}/databases/{database_id}"
            
            data = {
                "properties": {
                    "Test Button": {  # Name of the button property
                        "type": "button",
                        "button": {}
                    }
                }
            }
            
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            logger.info("Created button property in database")
            return True
            
        except Exception as e:
            logger.error(f"Error creating button property: {e}")
            return False

    def setup_webhook_integration(self):
        """Set up the webhook integration for the button clicks."""
        try:
            webhook_url = "https://whole-mastodon-top.ngrok-free.app/webhook"
            
            # Create the webhook
            webhook_data = {
                "parent": {
                    "database_id": self.subprojects_db_id
                },
                "properties": {
                    "Test Button": {
                        "button": {}
                    }
                },
                "url": webhook_url,
                "events": ["page_properties_changed"]
            }
            
            response = self.create_webhook(webhook_url)
            if response:
                logger.info("Successfully set up webhook integration")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error setting up webhook integration: {e}")
            return False
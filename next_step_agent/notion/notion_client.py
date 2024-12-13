from typing import Dict, List
import requests
import logging
import os
from dotenv import load_dotenv
import json
from config import (
    NOTION_API_KEY,
    NOTION_STEPS_DATABASE_ID,
    NOTION_PROJECTS_DATABASE_ID,
    NOTION_SUBPROJECTS_DATABASE_ID,
)

load_dotenv()

logger = logging.getLogger(__name__)


class NotionClient:
    def __init__(self):
        self.api_key = NOTION_API_KEY
        self.subprojects_db_id = NOTION_SUBPROJECTS_DATABASE_ID
        self.steps_db_id = NOTION_STEPS_DATABASE_ID
        self.projects_db_id = NOTION_PROJECTS_DATABASE_ID

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        self.base_url = "https://api.notion.com/v1"

        # Add this to debug the database structure
        self._debug_database_structure()

        # Add value mappings for Notion properties
        self.priority_map = {"High": 3, "Low": 1}

        # Project Priority is 1-5 with 1 being highest, so we'll invert it
        self.project_priority_map = {
            1: 5,  # 1 (highest) -> 5 points
            2: 4,
            3: 3,
            4: 2,
            5: 1,  # 5 (lowest) -> 1 point
        }

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
            data = {"filter": {"property": "Name", "title": {"equals": title}}}
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            results = response.json().get("results", [])
            if results:
                return results[0]["id"]
            return None
        except Exception as e:
            logger.error(f"Error getting page ID for {title}: {e}")
            return None

    def create_subproject(self, mapped_task: Dict) -> bool:
        """Create a subproject in Notion with status 'potential'."""
        try:
            # Get related page IDs
            project_id = self._get_page_id_by_title(
                self.projects_db_id, mapped_task["project_display_name"]
            )
            step_id = self._get_page_id_by_title(self.steps_db_id, mapped_task["step"])
            person_id = self._get_page_id_by_title(
                self.people_db_id, "Miles Porter"
            )  # Hardcoded for now

            if not all([project_id, step_id, person_id]):
                logger.error("Failed to get all required page IDs")
                logger.error(
                    f"Project ID: {project_id}, Step ID: {step_id}, Person ID: {person_id}"
                )
                return False

            url = f"{self.base_url}/pages"
            data = {
                "parent": {"database_id": self.subprojects_db_id},
                "properties": {
                    "Sub-project": {
                        "title": [{"text": {"content": mapped_task["subproject"]}}]
                    },
                    "Status": {"status": {"name": "Potential"}},
                    "Project": {"relation": [{"id": project_id}]},
                    "Step": {"relation": [{"id": step_id}]},
                    "Team Comp": {"relation": [{"id": person_id}]},
                },
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
            results.append({**task, "notion_created": success})
        return results

    def create_webhook(self, url: str):
        """Create a new webhook in Notion."""
        try:
            webhook_url = f"{self.base_url}/webhooks"
            data = {
                "url": url,
                "events": [
                    "page_properties_changed"
                ],  # This will trigger when button properties change
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
                        "button": {},
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
                "parent": {"database_id": self.subprojects_db_id},
                "properties": {"Test Button": {"button": {}}},
                "url": webhook_url,
                "events": ["page_properties_changed"],
            }

            response = self.create_webhook(webhook_url)
            if response:
                logger.info("Successfully set up webhook integration")
                return True
            return False

        except Exception as e:
            logger.error(f"Error setting up webhook integration: {e}")
            return False

    def get_user_subprojects(
        self, person_id="bdf265bb07fe4d9d88773686ed9dbddf"
    ):  # Miles Porter's Notion ID
        """Get all potential/not started subprojects for a person by their Notion ID."""
        try:
            url = f"{self.base_url}/databases/{self.subprojects_db_id}/query"

            logger.info(f"Querying subprojects for person ID: {person_id}")

            data = {
                "filter": {
                    "and": [
                        # Team Comp filter
                        {"property": "Team Comp", "relation": {"contains": person_id}},
                        # Status filter - exclude "Out of current scope" and "Done"
                        {
                            "property": "Status",
                            "status": {"does_not_equal": "Out of current scope"},
                        },
                        {"property": "Status", "status": {"does_not_equal": "Done"}},
                        # Project Status filter - only Active projects
                        {
                            "property": "Project Status",
                            "rollup": {"any": {"select": {"equals": "Active"}}},
                        },
                    ]
                }
            }

            # Add debug logging for the query
            logger.info(f"Sending query to Notion: {json.dumps(data, indent=2)}")

            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()

            results = response.json().get("results", [])
            logger.info(f"Found {len(results)} subprojects")

            subprojects = []
            for item in results:
                properties = item.get("properties", {})

                # Convert text values to numeric scores
                urgency = (
                    properties.get("Urgency", {}).get("select", {}).get("name", "Low")
                )
                importance = (
                    properties.get("Importance", {})
                    .get("select", {})
                    .get("name", "Low")
                )
                impact = (
                    properties.get("Impact", {}).get("select", {}).get("name", "Low")
                )

                # Get project priority (1-5) and map to our 5-1 scale
                project_priority_raw = (
                    properties.get("Project Priority", {})
                    .get("rollup", {})
                    .get("number", 5)
                )

                subprojects.append(
                    {
                        "id": item["id"],
                        "title": self._extract_title(properties.get("Sub-project", {})),
                        "urgency": self.priority_map.get(urgency, 0),
                        "importance": self.priority_map.get(importance, 0),
                        "impact": self.priority_map.get(impact, 0),
                        "project_priority": self.project_priority_map.get(
                            project_priority_raw, 0
                        ),
                        "blocking": properties.get("Blocking", {}).get("relation", []),
                        "blocked_by": properties.get("Blocked by", {}).get(
                            "relation", []
                        ),
                        "status": properties.get("Status", {})
                        .get("status", {})
                        .get("name"),
                        # Add raw values for debugging
                        "raw_values": {
                            "urgency": urgency,
                            "importance": importance,
                            "impact": impact,
                            "project_priority": project_priority_raw,
                        },
                    }
                )

                # Log the conversion for debugging
                logger.info(f"""
                Value conversion for "{self._extract_title(properties.get('Sub-project', {}))}":
                - Urgency: {urgency} -> {self.priority_map.get(urgency, 0)}
                - Importance: {importance} -> {self.priority_map.get(importance, 0)}
                - Impact: {impact} -> {self.priority_map.get(impact, 0)}
                - Project Priority: {project_priority_raw} -> {self.project_priority_map.get(project_priority_raw, 0)}
                """)

            return subprojects

        except Exception as e:
            logger.error(f"Error fetching user subprojects: {e}")
            if isinstance(e, requests.exceptions.HTTPError):
                logger.error(f"Response content: {e.response.content}")
            return []

    def _extract_title(self, title_prop):
        """Helper to extract title from Notion property."""
        try:
            return title_prop.get("title", [{}])[0].get("text", {}).get("content", "")
        except:
            return ""

    def get_person_by_user_id(self, user_id: str):
        """Get person details from People database using their Notion user ID."""
        try:
            url = f"{self.base_url}/databases/{self.people_db_id}/query"

            # Query for the person with matching Notion User ID
            data = {
                "filter": {"property": "Notion User", "relation": {"contains": user_id}}
            }

            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()

            results = response.json().get("results", [])
            if results:
                person = results[0]
                person_id = person["id"]
                logger.info(f"Found person in People database with ID: {person_id}")
                return person_id

            logger.error(f"No person found in People database for user ID: {user_id}")
            return None

        except Exception as e:
            logger.error(f"Error getting person by user ID: {e}")
            if isinstance(e, requests.exceptions.HTTPError):
                logger.error(f"Response content: {e.response.content}")
            return None

    def update_subproject_status(self, subproject_id: str, status: str):
        """Update the status of a subproject in Notion."""
        url = f"{self.base_url}/pages/{subproject_id}"
        data = {"properties": {"Status": {"status": {"name": status}}}}
        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        logger.info(f"Updated status for subproject {subproject_id} to {status}")
        return True

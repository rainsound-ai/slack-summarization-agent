from typing import Dict, List, Optional
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
    NOTION_PROCESSES_DATABASE_ID,
    NOTION_SYSTEMS_DATABASE_ID,
    NOTION_SUBPROJECT_TEMPLATE_PAGE_ID,
)

load_dotenv()

logger = logging.getLogger(__name__)


class NotionClient:
    def __init__(self):
        if not all(
            [
                NOTION_SUBPROJECTS_DATABASE_ID,
                NOTION_STEPS_DATABASE_ID,
                NOTION_PROJECTS_DATABASE_ID,
            ]
        ):
            raise ValueError("All database IDs must be provided")

        self.api_key = NOTION_API_KEY
        self.subprojects_db_id = NOTION_SUBPROJECTS_DATABASE_ID
        self.steps_db_id = NOTION_STEPS_DATABASE_ID
        self.projects_db_id = NOTION_PROJECTS_DATABASE_ID
        self.processes_db_id = NOTION_PROCESSES_DATABASE_ID
        self.systems_db_id = NOTION_SYSTEMS_DATABASE_ID

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

    def _get_page_id_by_title(
        self, database_id: str, title: Optional[str]
    ) -> Optional[str]:
        """Get Notion page ID by searching for its title in a database."""
        if not database_id or not title:
            logger.error(
                f"Missing required parameter: database_id={database_id}, title={title}"
            )
            return None

        try:
            url = f"{self.base_url}/databases/{database_id}/query"
            data = {"filter": {"property": "Name", "title": {"equals": title}}}
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            results = response.json().get("results", [])

            if not results:
                logger.warning(
                    f"No results found for title '{title}' in database {database_id}"
                )
                return None

            return results[0]["id"]

        except Exception as e:
            logger.error(f"Error getting page ID for {title}: {e}")
            return None

    def create_subproject(self, mapped_task: Dict) -> bool:
        """Create a subproject in Notion with status 'potential'."""
        try:
            # Validate required fields
            project_name = mapped_task.get("project_display_name")
            step_name = mapped_task.get("step")

            if not project_name or not step_name:
                logger.error(
                    f"Missing required fields: project_name={project_name}, step_name={step_name}"
                )
                return False

            logger.info(f"Project Name: {project_name}")
            logger.info(f"Step Name: {step_name}")

            # Get related page IDs
            project_id = self._get_page_id_by_title(self.projects_db_id, project_name)
            if not project_id:
                logger.error(f"Could not find project with name: {project_name}")

            step_id = self._get_page_id_by_title(self.steps_db_id, step_name)
            if not step_id:
                logger.error(f"Could not find step with name: {step_name}")

            if not project_id and not step_id:
                return False

            # Get Miles' Notion ID from users.json
            with open("next_step_agent/data/users.json") as f:
                users_data = json.load(f)
                user_id = None
                for user in users_data["users"]:  # Access the "users" array
                    if user.get("name") == "Miles Porter":
                        user_id = user.get("notion_id")
                        break

            logger.info(f"User ID: {user_id}")
            if not user_id:
                logger.error("Could not find Miles Porter's Notion ID in users.json")
                return False

            if not all([project_id, step_id, user_id]):
                logger.error("Failed to get all required page IDs")
                logger.error(
                    f"Project ID: {project_id}, Step ID: {step_id}, User ID: {user_id}"
                )

            url = f"{self.base_url}/pages"
            logger.info(f"URL: {url}")

            data = {
                "parent": {"database_id": self.subprojects_db_id},
                "properties": {
                    "Sub-project": {
                        "title": [{"text": {"content": mapped_task["subproject"]}}]
                    },
                    "Status": {"status": {"name": "Potential"}},
                    "Team Comp": {"people": [{"id": user_id}]},
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": "Description"}}]
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"text": {"content": mapped_task["description"]}}
                            ]
                        },
                    },
                ],
            }

            if project_id:
                data["properties"]["Project"] = {"relation": [{"id": project_id}]}
            if step_id:
                data["properties"]["Step"] = {"relation": [{"id": step_id}]}

            logger.info(f"Data: {data}")
            logger.info(f"Creating subproject: {mapped_task['subproject']}")
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

    def fetch_user_subprojects(self, user_id):
        """Get all potential/not started subprojects for a person by their Notion ID."""
        try:
            url = f"{self.base_url}/databases/{self.subprojects_db_id}/query"

            logger.info(f"Querying subprojects for person ID: {user_id}")

            data = {
                "filter": {
                    "and": [
                        # Team Comp filter
                        {"property": "Team Comp", "people": {"contains": user_id}},
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

            # Add debug logging for raw response
            logger.info(f"Raw response status code: {response.status_code}")
            logger.info(f"Raw response headers: {response.headers}")

            response_json = response.json()
            if not response_json:
                logger.error("Received empty response from Notion")
                return []

            logger.info(f"Response JSON: {json.dumps(response_json, indent=2)}")

            results = response_json.get("results", [])
            if not results:
                logger.info("No results found in response")
                return []

            logger.info(f"Found {len(results)} subprojects")

            subprojects = []
            for item in results:
                if not item:
                    logger.warning("Found null item in results")
                    continue

                properties = item.get("properties")
                if not properties:
                    logger.warning(f"No properties found for item: {item}")
                    continue

                # Convert text values to numeric scores
                urgency = (
                    properties.get("Urgency", {}).get("select", {}).get("name", "Low")
                    if properties.get("Urgency")
                    and properties.get("Urgency").get("select")
                    else "Low"
                )
                importance = (
                    properties.get("Importance", {})
                    .get("select", {})
                    .get("name", "Low")
                    if properties.get("Importance")
                    and properties.get("Importance").get("select")
                    else "Low"
                )
                impact = (
                    properties.get("Impact", {}).get("select", {}).get("name", "Low")
                    if properties.get("Impact")
                    and properties.get("Impact").get("select")
                    else "Low"
                )
                effort = (
                    properties.get("Effort", {}).get("select", {}).get("name", "Low")
                    if properties.get("Effort")
                    and properties.get("Effort").get("select")
                    else "Low"
                )

                # Get project priority (1-5) and map to our 5-1 scale
                project_priority_raw = (
                    properties.get("Project Priority", {})
                    .get("rollup", {})
                    .get("number", 5)
                )

                # Safely get step and parent project IDs
                step_relations = properties.get("Step", {}).get("relation", [])
                step = (
                    self.get_title_by_page_id(step_relations[0].get("id"))
                    if step_relations
                    else ""
                )
                logger.info(f"Step: {step}")

                project_relations = properties.get("Project", {}).get("relation", [])
                parent_project = (
                    self.get_title_by_page_id(project_relations[0].get("id"))
                    if project_relations
                    else ""
                )
                logger.info(f"Parent Project: {parent_project}")

                subprojects.append(
                    {
                        "id": item["id"],
                        "title": self._extract_title(properties.get("Sub-project", {})),
                        "urgency": self.priority_map.get(urgency, 0),
                        "importance": self.priority_map.get(importance, 0),
                        "impact": self.priority_map.get(impact, 0),
                        "parent_project": parent_project,
                        "project_priority": self.project_priority_map.get(
                            project_priority_raw, 0
                        ),
                        "step": step,
                        "effort": self.priority_map.get(effort, 0),
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
                            "effort": effort,
                        },
                        "self_link": f"https://notion.so/{item['id'].replace('-', '')}",
                    }
                )

                # Log the conversion for debugging
                logger.info(f"""
                Value conversion for "{self._extract_title(properties.get('Sub-project', {}))}":
                - Urgency: {urgency} -> {self.priority_map.get(urgency, 0)}
                - Importance: {importance} -> {self.priority_map.get(importance, 0)}
                - Impact: {impact} -> {self.priority_map.get(impact, 0)}
                - Project Priority: {project_priority_raw} -> {self.project_priority_map.get(project_priority_raw, 0)}
                - Effort: {effort} -> {self.priority_map.get(effort, 0)}
                - step: {step}
                - parent_project: {parent_project}
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

    def get_title_by_page_id(self, page_id: str):
        """Get title from Notion page by ID."""
        url = f"{self.base_url}/pages/{page_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return (
            response.json()
            .get("properties", {})
            .get("Name", {})
            .get("title", [{}])[0]
            .get("text", {})
            .get("content", "")
        )

    # def get_person_by_user_id(self, user_id: str):
    #     """Get person details from People database using their Notion user ID."""
    #     try:
    #         url = f"{self.base_url}/databases/{self.people_db_id}/query"

    #         # Query for the person with matching Notion User ID
    #         data = {
    #             "filter": {"property": "Notion User", "relation": {"contains": user_id}}
    #         }

    #         response = requests.post(url, headers=self.headers, json=data)
    #         response.raise_for_status()

    #         results = response.json().get("results", [])
    #         if results:
    #             person = results[0]
    #             person_id = person["id"]
    #             logger.info(f"Found person in People database with ID: {person_id}")
    #             return person_id

    #         logger.error(f"No person found in People database for user ID: {user_id}")
    #         return None

    #     except Exception as e:
    #         logger.error(f"Error getting person by user ID: {e}")
    #         if isinstance(e, requests.exceptions.HTTPError):
    #             logger.error(f"Response content: {e.response.content}")
    #         return None

    def update_subproject_status(self, subproject_id: str, status: str):
        """Update the status of a subproject in Notion."""
        url = f"{self.base_url}/pages/{subproject_id}"
        data = {"properties": {"Status": {"status": {"name": status}}}}
        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        logger.info(f"Updated status for subproject {subproject_id} to {status}")
        return True

    def fetch_all_milestones(self):
        """Fetch all milestones from the Systems database."""
        url = f"{self.base_url}/databases/{self.systems_db_id}/query"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()

        milestones = []
        for page in response.json().get("results", []):
            # Get Next Milestone property
            rich_text = (
                page.get("properties", {})
                .get("Next Milestone", {})
                .get("rich_text", [])
            )

            if rich_text and len(rich_text) > 0:
                next_milestone = rich_text[0].get("text", {}).get("content", "")
                if next_milestone and next_milestone.strip() != "":
                    milestones.append(next_milestone)
                    logger.info(
                        f"Found milestone '{next_milestone}' for system {page['id']}"
                    )

        logger.info(f"All milestones found: {milestones}")
        return list(set(milestones))  # Remove duplicates

    def update_subproject_calendar_event(
        self, subproject: Dict, calendar_event_id: str
    ):
        """Update the calendar event for a subproject in Notion."""
        url = f"{self.base_url}/pages/{subproject['id']}"
        data = {"properties": {"Calendar Event": {"url": calendar_event_id}}}
        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()
        logger.info(f"Updated calendar event for subproject {subproject['id']}")
        return True

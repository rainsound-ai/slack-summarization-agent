from notion_client import Client
from config import (
    NOTION_API_KEY,
    NOTION_STEPS_DATABASE_ID,
    NOTION_PROCESSES_DATABASE_ID,
    NOTION_SOP_DATABASE_ID,
    NOTION_PROJECTS_DATABASE_ID,
)
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class NotionDataFetcher:
    def __init__(self):
        self.client = Client(auth=NOTION_API_KEY)
        # Initialize these at the class level
        self.processes = []
        self.sops = []

    def fetch_step_by_id(self, step_id: str) -> Dict:
        """Fetch a single step by its ID."""
        try:
            response = self.client.pages.retrieve(page_id=step_id)

            # Extract the name from the title property
            name = response["properties"]["Name"]["title"][0]["text"]["content"]

            # Get the page content for description
            description = self.get_page_content(step_id)

            return {"name": name, "description": description}
        except Exception as e:
            logger.error(f"Error fetching step by ID {step_id}: {e}")
            return None

    def fetch_step_data_by_filter(
        self, filter_property_name, filter_property_type, filter_property_value
    ):
        try:
            response = self.client.databases.query(
                database_id=NOTION_STEPS_DATABASE_ID,
                filter={
                    "property": filter_property_name,
                    filter_property_type: {"contains": filter_property_value},
                },
            )

            # Format steps into text
            formatted_steps = []

            # Fetch processes and SOPs first
            self.processes = self.fetch_process_data_by_filter(
                "Business Lead Frequency", "select", "Common"
            )
            self.sops = self.fetch_sop_data_by_filter("Status", "select", "Active")

            for result in response["results"]:
                try:
                    # Safely get the name property
                    name_property = result.get("properties", {}).get("Name", {})
                    title_array = name_property.get("title", [])
                    if not title_array:
                        print("Skipping step with empty name")
                        continue

                    name = title_array[0].get("text", {}).get("content", "Unnamed Step")
                    id = result["id"]
                    # Construct the Notion URL for the step
                    step_url = f"https://notion.so/{id.replace('-', '')}"
                    formatted_steps.append(f"Step: {name}\nURL: {step_url}")

                    # Format and append process and SOP data
                    for process in self.processes:
                        formatted_steps.append(f"Process: {process['name']}")
                        if process["body_content"]:
                            formatted_steps.append(process["body_content"])

                    # Modified to format SOPs more cleanly
                    for sop in self.sops:
                        formatted_steps.append(f"SOP: {sop['name']}")
                        if sop["body_content"]:
                            formatted_steps.append(sop["body_content"])
                    formatted_steps.append("-" * 50)  # Add separator between steps

                except (KeyError, IndexError) as e:
                    print(f"Error processing step: {e}")
                    continue

            # Join all steps and write to file
            output_text = "\n".join(formatted_steps)
            with open("outputs/notion_steps.txt", "w", encoding="utf-8") as f:
                f.write(output_text)

            return output_text

        except Exception as e:
            print(f"Error fetching from Notion: {e}")
            return ""  # Return empty string on error

    def fetch_process_data_by_filter(
        self, filter_property_name, filter_property_type, filter_property_value
    ):
        response = self.client.databases.query(
            **{
                "database_id": NOTION_PROCESSES_DATABASE_ID,
                "filter": {
                    "property": filter_property_name,
                    filter_property_type: {"equals": filter_property_value},
                },
            }
        )
        # Extract process data including relations
        processes = []
        for result in response["results"]:
            # Get name
            name = result["properties"]["Name"]["title"][0]["text"]["content"]

            # Get SOPs relation
            sops = []
            if "SOPs" in result["properties"]:
                sops = [
                    relation["id"]
                    for relation in result["properties"]["SOPs"].get("relation", [])
                ]

            # Get Steps relation
            steps = []
            if "Steps" in result["properties"]:
                steps = [
                    relation["id"]
                    for relation in result["properties"]["Steps"].get("relation", [])
                ]

            # Get Business Lead Frequency
            frequency = None
            if "Business Lead Frequency" in result["properties"]:
                frequency = (
                    result["properties"]["Business Lead Frequency"]
                    .get("select", {})
                    .get("name")
                )

            processes.append(
                {
                    "id": result["id"],  # Add the process ID
                    "name": name,
                    "sops": sops,
                    "steps": steps,
                    "business_lead_frequency": frequency,
                }
            )

        return processes

    def fetch_sop_data_by_filter(
        self, filter_property_name, filter_property_type, filter_property_value
    ):
        # Query the Notion SOPs database
        response = self.client.databases.query(
            **{
                "database_id": NOTION_SOP_DATABASE_ID,
                "filter": {
                    "property": filter_property_name,
                    filter_property_type: {"contains": filter_property_value},
                },
            }
        )
        # Extract name and body content
        sops = []
        for result in response["results"]:
            name = result["properties"]["Name"]["title"][0]["text"]["content"]
            id = result["id"]
            body_content = self.get_page_content(id)
            sops.append({"name": name, "body_content": body_content})
        return sops

    def fetch_project_data_by_filter(
        self, filter_property_name, filter_property_type, filter_property_value
    ):
        response = self.client.databases.query(
            database_id=NOTION_PROJECTS_DATABASE_ID,
            filter={
                "property": filter_property_name,
                filter_property_type: {"contains": filter_property_value},
            },
        )
        return response["results"]

    def get_page_content(self, page_id):
        """Helper function to get all content from a page"""
        blocks = self.client.blocks.children.list(block_id=page_id)
        content = []

        for block in blocks.get("results", []):
            text = self.extract_block_content(block)
            if text:
                content.append(text)

        return "\n".join(filter(None, content))  # Filter out empty strings

    def extract_block_content(self, block):
        """Helper function to extract text content from different block types"""
        block_type = block["type"]

        if block_type not in block:
            return ""

        text_content = []
        rich_text = []

        if block_type == "column_list":
            # Handle column lists by recursively processing each column
            columns = self.client.blocks.children.list(block_id=block["id"]).get(
                "results", []
            )
            for column in columns:
                # Get content within each column
                column_blocks = self.client.blocks.children.list(
                    block_id=column["id"]
                ).get("results", [])
                for col_block in column_blocks:
                    col_content = self.extract_block_content(col_block)
                    if col_content:
                        text_content.append(col_content)
        elif block_type == "paragraph":
            rich_text = block["paragraph"]["rich_text"]
        elif block_type == "heading_1":
            rich_text = block["heading_1"]["rich_text"]
        elif block_type == "heading_2":
            rich_text = block["heading_2"]["rich_text"]
        elif block_type == "heading_3":
            rich_text = block["heading_3"]["rich_text"]
        elif block_type == "bulleted_list_item":
            rich_text = block["bulleted_list_item"]["rich_text"]
        elif block_type == "numbered_list_item":
            rich_text = block["numbered_list_item"]["rich_text"]
        else:
            return ""

        # Process rich text if it's a text block type
        if block_type != "column_list":
            for text in rich_text:
                if text.get("type") == "text":
                    text_content.append(text.get("text", {}).get("content", ""))

        return " ".join(text_content)

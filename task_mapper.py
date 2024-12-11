from openai import OpenAI
import json
import numpy as np
from typing import List, Dict
import logging
from config import OPENAI_API_KEY
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

class TaskMapper:
    def __init__(self):
        self.processes = self._load_processes()
        self.model = "o1-preview"
        self.embedding_model = "text-embedding-ada-002"

    def _load_processes(self) -> Dict:
        """Load processes from JSON file."""
        try:
            with open('processes.json', 'r') as f:
                processes = json.load(f)
                logger.info(f"Loaded processes: {json.dumps(processes, indent=2)}")
                return processes
        except Exception as e:
            logger.error(f"Error loading processes.json: {e}")
            return {"processes": []}

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        try:
            response = client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            return []

    def extract_tasks(self, messages: List[Dict]) -> List[Dict]:
        """Extract tasks and assignees from messages using GPT-4."""
        try:
            formatted_messages = self._format_messages_for_prompt(messages)
            prompt = self._create_extraction_prompt(formatted_messages)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_content = response.choices[0].message.content.strip()
            logger.info(f"OpenAI Response: {response_content}")
            
            try:
                tasks = json.loads(response_content)
                return tasks
            except json.JSONDecodeError as je:
                logger.error(f"JSON parsing error: {je}")
                logger.error(f"Failed to parse response: {response_content}")
                return []
            
        except Exception as e:
            logger.error(f"Error extracting tasks: {e}")
            return []

    def map_tasks_to_processes(self, tasks: List[Dict]) -> List[Dict]:
        """Map extracted tasks to process steps using embeddings."""
        if not tasks:
            return []

        # Filter for Miles' tasks only
        miles_tasks = [task for task in tasks if task["assignee"].lower() == "miles"]
        if not miles_tasks:
            logger.info("No tasks found assigned to Miles")
            return []

        # Prepare lists for embedding comparison
        task_texts = [task["task"] for task in miles_tasks]
        all_steps = []
        step_to_process = {}
        process_to_project = {}  # New mapping for process to project

        # Build process to project mapping
        for project_name, project_data in self.processes.get("projects", {}).items():
            for process_name in project_data.get("processes", []):
                process_to_project[process_name] = project_name

        # Extract step names from processes
        for process in self.processes.get("processes", []):
            process_name = process["name"]
            for step in process["steps"]:
                if isinstance(step, dict):
                    step_name = step["name"]
                    step_text = f"{step_name} - {step.get('description', '')}"
                else:
                    step_name = step
                    step_text = step
                # Remove numbering from step name
                step_text = re.sub(r'^\d+\.\s*', '', step_text)
                all_steps.append(step_text)
                step_to_process[step_text] = process_name

        if not all_steps:
            logger.warning("No valid steps found in processes")
            return []

        # Get embeddings
        task_embeddings = self.get_embeddings(task_texts)
        step_embeddings = self.get_embeddings(all_steps)

        if not task_embeddings or not step_embeddings:
            logger.error("Failed to get embeddings")
            return []

        # Convert to numpy arrays for easier computation
        task_embeddings_np = np.array(task_embeddings)
        step_embeddings_np = np.array(step_embeddings)

        # Calculate similarities
        similarities = np.dot(task_embeddings_np, step_embeddings_np.T)

        mapped_tasks = []
        for i, task in enumerate(miles_tasks):
            # Find most similar step
            most_similar_idx = np.argmax(similarities[i])
            most_similar_step = all_steps[most_similar_idx]
            parent_process = step_to_process[most_similar_step]
            project = process_to_project.get(parent_process, "Unknown Project")

            mapped_task = {
                "subproject": task["task"],  # Rename task to subproject
                "assignee": task["assignee"],
                "step": most_similar_step.split(" - ")[0],  # Only keep the step name, not the description
                "parent_process": parent_process,
                "project": project,
                "project_display_name": self.processes["projects"][project]["display_name"],
                "similarity_score": float(similarities[i][most_similar_idx])
            }
            mapped_tasks.append(mapped_task)

        # Sort mapped_tasks by similarity_score in descending order
        mapped_tasks.sort(key=lambda x: x['similarity_score'], reverse=True)

        return mapped_tasks

    def _format_messages_for_prompt(self, messages: List[Dict]) -> str:
        """Format messages for the extraction prompt."""
        formatted = []
        for msg in messages:
            user = msg.get("user", "Unknown")
            text = msg.get("text", "")
            formatted.append(f"{user}: {text}")
        return "\n".join(formatted)

    def _create_extraction_prompt(self, formatted_messages: str) -> str:
        """Create the prompt for task extraction."""
        return f"""Extract tasks and their assignees from these Slack messages. 
Return ONLY a valid JSON array with "task" and "assignee" fields.
The response must start with '[' and end with ']'.

Important: For tasks with multiple assignees, create separate entries for each assignee.

Messages:
{formatted_messages}

Required JSON format:
[
    {{"task": "Create the project timeline", "assignee": "John"}},
    {{"task": "Review the proposal", "assignee": "Sarah"}}
]

Ensure the output is a valid JSON array. Do not include any additional text or formatting.""" 
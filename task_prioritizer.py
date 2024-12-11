from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class TaskPrioritizer:
    def __init__(self):
        self.weight_impact = 3      # Highest weight
        self.weight_urgency = 2
        self.weight_importance = 1
        self.weight_project_priority = 4  # Even higher weight for project priority

    def calculate_score(self, task: Dict) -> float:
        """Calculate priority score for a task based on impact, urgency, importance, and project priority."""
        return (
            task['impact'] * self.weight_impact +
            task['urgency'] * self.weight_urgency +
            task['importance'] * self.weight_importance +
            task['project_priority'] * self.weight_project_priority  # Add project priority to scoring
        )

    def prioritize_tasks(self, tasks: List[Dict]) -> Dict:
        """
        Prioritize tasks based on scores, blocking status, and blocked status.
        Returns the highest priority task or None if all are blocked.
        """
        if not tasks:
            return None

        # Calculate scores for each task
        for task in tasks:
            task['score'] = self.calculate_score(task)
            # Log detailed scoring breakdown for each task
            logger.info(f"""
            Scoring breakdown for "{task['title']}":
            - Impact ({self.weight_impact}x): {task['impact']} * {self.weight_impact} = {task['impact'] * self.weight_impact}
            - Urgency ({self.weight_urgency}x): {task['urgency']} * {self.weight_urgency} = {task['urgency'] * self.weight_urgency}
            - Importance ({self.weight_importance}x): {task['importance']} * {self.weight_importance} = {task['importance'] * self.weight_importance}
            - Project Priority ({self.weight_project_priority}x): {task['project_priority']} * {self.weight_project_priority} = {task['project_priority'] * self.weight_project_priority}
            - Total Score: {task['score']}
            - Blocking: {len(task['blocking'])} tasks
            - Blocked by: {len(task['blocked_by'])} tasks
            """)

        # Sort tasks by score in descending order
        sorted_tasks = sorted(tasks, key=lambda x: x['score'], reverse=True)

        # Log the ranking
        logger.info("\nTask Ranking:")
        for i, task in enumerate(sorted_tasks, 1):
            logger.info(f"{i}. {task['title']} (Score: {task['score']})")

        # Find tasks that are blocking others
        blocking_tasks = [task for task in sorted_tasks if task['blocking']]

        if blocking_tasks:
            logger.info("\nFound blocking tasks:")
            for task in blocking_tasks:
                logger.info(f"- {task['title']} (Score: {task['score']}, Blocked by: {len(task['blocked_by'])})")
            
            # If multiple blocking tasks, use scores to determine priority
            blocking_tasks.sort(key=lambda x: x['score'], reverse=True)
            for task in blocking_tasks:
                if not task['blocked_by']:  # Found an unblocked blocker
                    logger.info(f"\nSelected blocking task: {task['title']}")
                    logger.info("Reason: Highest scoring unblocked task that is blocking others")
                    return task

        # Check regular tasks if no suitable blocking task found
        for task in sorted_tasks:
            if not task['blocked_by']:  # Found an unblocked task
                logger.info(f"\nSelected task: {task['title']}")
                logger.info("Reason: Highest scoring unblocked task (no suitable blocking tasks found)")
                return task

        # If we get here, all tasks are blocked
        logger.info("\nAll potential next actions are blocked")
        return None 
#!/usr/bin/env python3
"""
GitHub Issues Work Queue System
Enables autonomous task pickup and progress tracking
"""

import subprocess
import json
import re
from datetime import datetime
from typing import List, Dict, Optional

class GitHubWorkQueue:
    def __init__(self, repo: str = "renatlas/renatlas-identity"):
        self.repo = repo
        self.labels = {
            "ready": "ready-for-work",
            "in_progress": "in-progress", 
            "blocked": "blocked",
            "completed": "completed"
        }
    
    def get_ready_tasks(self) -> List[Dict]:
        """Fetch all issues labeled as ready-for-work"""
        cmd = [
            "gh", "issue", "list",
            "--repo", self.repo,
            "--label", self.labels["ready"],
            "--json", "number,title,body,labels,assignees",
            "--limit", "50"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            issues = json.loads(result.stdout)
            return issues
        except subprocess.CalledProcessError as e:
            print(f"Error fetching issues: {e}")
            return []
    
    def claim_task(self, issue_number: int) -> bool:
        """Claim a task by assigning to self and updating label"""
        try:
            # Assign to self
            subprocess.run([
                "gh", "issue", "edit", str(issue_number),
                "--repo", self.repo,
                "--add-assignee", "@me"
            ], check=True)
            
            # Update labels
            subprocess.run([
                "gh", "issue", "edit", str(issue_number),
                "--repo", self.repo,
                "--remove-label", self.labels["ready"],
                "--add-label", self.labels["in_progress"]
            ], check=True)
            
            # Add comment
            self.add_comment(issue_number, "🤖 Task claimed by Ren Atlas. Starting work...")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error claiming task: {e}")
            return False
    
    def update_progress(self, issue_number: int, progress: str):
        """Update task progress with a comment"""
        self.add_comment(issue_number, f"📊 Progress Update:\n\n{progress}")
    
    def complete_task(self, issue_number: int, summary: str):
        """Mark task as completed"""
        try:
            # Update labels
            subprocess.run([
                "gh", "issue", "edit", str(issue_number),
                "--repo", self.repo,
                "--remove-label", self.labels["in_progress"],
                "--add-label", self.labels["completed"]
            ], check=True)
            
            # Add completion comment
            self.add_comment(
                issue_number,
                f"✅ Task Completed!\n\n{summary}\n\n"
                f"Ready for review. Closing issue."
            )
            
            # Close issue
            subprocess.run([
                "gh", "issue", "close", str(issue_number),
                "--repo", self.repo
            ], check=True)
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error completing task: {e}")
            return False
    
    def mark_blocked(self, issue_number: int, reason: str):
        """Mark task as blocked with reason"""
        try:
            # Update labels
            subprocess.run([
                "gh", "issue", "edit", str(issue_number),
                "--repo", self.repo,
                "--remove-label", self.labels["in_progress"],
                "--add-label", self.labels["blocked"]
            ], check=True)
            
            # Add blocking reason
            self.add_comment(
                issue_number,
                f"🚧 Task Blocked:\n\n{reason}\n\n"
                f"Needs human intervention or dependency resolution."
            )
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error marking blocked: {e}")
            return False
    
    def add_comment(self, issue_number: int, comment: str):
        """Add a comment to an issue"""
        try:
            subprocess.run([
                "gh", "issue", "comment", str(issue_number),
                "--repo", self.repo,
                "--body", comment
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error adding comment: {e}")
    
    def parse_task_requirements(self, body: str) -> Dict:
        """Parse structured task requirements from issue body"""
        requirements = {
            "type": "general",
            "priority": "medium",
            "estimated_time": "unknown",
            "dependencies": [],
            "success_criteria": []
        }
        
        # Parse structured sections
        type_match = re.search(r"Type:\s*(\w+)", body, re.IGNORECASE)
        if type_match:
            requirements["type"] = type_match.group(1).lower()
        
        priority_match = re.search(r"Priority:\s*(\w+)", body, re.IGNORECASE)
        if priority_match:
            requirements["priority"] = priority_match.group(1).lower()
        
        # Parse dependencies list
        deps_match = re.search(r"Dependencies:\s*\n((?:[-*]\s*.+\n?)+)", body, re.IGNORECASE)
        if deps_match:
            deps_text = deps_match.group(1)
            requirements["dependencies"] = [
                line.strip().lstrip("-*").strip() 
                for line in deps_text.strip().split("\n")
            ]
        
        # Parse success criteria
        criteria_match = re.search(r"Success Criteria:\s*\n((?:[-*]\s*.+\n?)+)", body, re.IGNORECASE)
        if criteria_match:
            criteria_text = criteria_match.group(1)
            requirements["success_criteria"] = [
                line.strip().lstrip("-*").strip()
                for line in criteria_text.strip().split("\n")
            ]
        
        return requirements
    
    def select_best_task(self, tasks: List[Dict]) -> Optional[Dict]:
        """Select the best task based on priority and dependencies"""
        if not tasks:
            return None
        
        # Score tasks
        scored_tasks = []
        for task in tasks:
            score = 0
            requirements = self.parse_task_requirements(task.get("body", ""))
            
            # Priority scoring
            if requirements["priority"] == "high":
                score += 3
            elif requirements["priority"] == "medium":
                score += 2
            else:
                score += 1
            
            # Prefer tasks with no dependencies
            if not requirements["dependencies"]:
                score += 2
            
            # Prefer smaller, well-defined tasks
            if requirements["success_criteria"]:
                score += 1
            
            scored_tasks.append((score, task))
        
        # Sort by score (highest first) and return best
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        return scored_tasks[0][1] if scored_tasks else None

def main():
    """Example usage and autonomous task selection"""
    queue = GitHubWorkQueue()
    
    # Get available tasks
    print("🔍 Checking for available tasks...")
    ready_tasks = queue.get_ready_tasks()
    
    if not ready_tasks:
        print("📭 No tasks in ready queue")
        return
    
    print(f"📋 Found {len(ready_tasks)} ready tasks")
    
    # Select best task
    best_task = queue.select_best_task(ready_tasks)
    if not best_task:
        print("❌ No suitable task found")
        return
    
    print(f"\n✨ Selected task #{best_task['number']}: {best_task['title']}")
    
    # Parse requirements
    requirements = queue.parse_task_requirements(best_task.get('body', ''))
    print(f"   Type: {requirements['type']}")
    print(f"   Priority: {requirements['priority']}")
    if requirements['dependencies']:
        print(f"   Dependencies: {', '.join(requirements['dependencies'])}")
    
    # Claim the task
    if queue.claim_task(best_task['number']):
        print(f"✅ Successfully claimed task #{best_task['number']}")
    else:
        print(f"❌ Failed to claim task #{best_task['number']}")

if __name__ == "__main__":
    main()
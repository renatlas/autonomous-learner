#!/usr/bin/env python3
"""
Autonomous Learning System
Integrates continuous learning monitor with GitHub work queue for autonomous operation
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import the classes directly by importing the modules
import importlib.util

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Import the modules
clm_module = import_module_from_path("continuous_learning_monitor", 
                                     os.path.join(script_dir, "continuous-learning-monitor.py"))
gwq_module = import_module_from_path("github_work_queue", 
                                     os.path.join(script_dir, "github-work-queue.py"))

ContinuousLearningMonitor = clm_module.ContinuousLearningMonitor
GitHubWorkQueue = gwq_module.GitHubWorkQueue

class AutonomousLearner:
    def __init__(self, repo: str = "renatlas/renatlas-identity"):
        self.learning_monitor = ContinuousLearningMonitor()
        self.work_queue = GitHubWorkQueue(repo)
        self.learning_insights = []
        self.active_tasks = {}
        
    def process_learning_insights(self, learning_report: Dict) -> List[Dict]:
        """Convert learning insights into actionable tasks"""
        potential_tasks = []
        
        # Analyze patterns for task generation
        if learning_report.get("patterns_detected", 0) > 0:
            potential_tasks.append({
                "title": f"Analyze {learning_report['patterns_detected']} cross-domain patterns",
                "type": "research",
                "priority": "medium",
                "description": f"Investigate patterns detected in learning cycle: {', '.join(learning_report.get('top_themes', []))}"
            })
        
        # Generate tasks based on top themes
        themes = learning_report.get("top_themes", [])
        for theme in themes[:2]:  # Focus on top 2 themes
            if theme in ["ai", "autonomous", "governance"]:
                potential_tasks.append({
                    "title": f"Deep dive into {theme} developments",
                    "type": "learning",
                    "priority": "high" if theme == "autonomous" else "medium",
                    "description": f"Research recent developments in {theme} based on monitoring insights"
                })
        
        # Create integration tasks if multiple domains detected
        if len(themes) >= 2:
            potential_tasks.append({
                "title": f"Synthesize insights across {' and '.join(themes[:2])}",
                "type": "synthesis", 
                "priority": "high",
                "description": f"Integrate learnings from {themes[0]} and {themes[1]} to identify novel connections"
            })
        
        return potential_tasks
    
    def create_github_issues(self, tasks: List[Dict]) -> List[int]:
        """Create GitHub issues for autonomous tasks"""
        created_issues = []
        
        for task in tasks:
            # Format issue body with structured template
            body = f"""
**Type:** {task['type']}
**Priority:** {task['priority']}

## Description
{task['description']}

## Success Criteria
- [ ] Research completed and documented
- [ ] Key insights identified and recorded
- [ ] Connections to existing work mapped
- [ ] Findings shared via blog post or discussion

## Context
Auto-generated from autonomous learning cycle at {datetime.now().isoformat()}
"""
            
            try:
                # Create the issue (would use gh CLI in real implementation)
                print(f"📝 Would create issue: '{task['title']}'")
                print(f"   Type: {task['type']}, Priority: {task['priority']}")
                
                # For demo, simulate issue creation
                issue_number = hash(task['title']) % 1000
                created_issues.append(issue_number)
                
            except Exception as e:
                print(f"❌ Failed to create issue for '{task['title']}': {e}")
        
        return created_issues
    
    def autonomous_cycle(self) -> Dict:
        """Run one complete autonomous learning cycle"""
        cycle_start = datetime.now()
        print(f"🤖 Starting autonomous learning cycle at {cycle_start}")
        
        # Step 1: Run learning monitor
        print("📚 Running learning monitor...")
        learning_report = self.learning_monitor.run_monitoring_cycle()
        
        # Step 2: Process insights into tasks
        print("🧠 Processing learning insights...")
        potential_tasks = self.process_learning_insights(learning_report)
        
        if potential_tasks:
            print(f"💡 Generated {len(potential_tasks)} potential tasks")
            
            # Step 3: Create GitHub issues for high-value tasks
            high_value_tasks = [t for t in potential_tasks if t['priority'] in ['high', 'medium']]
            if high_value_tasks:
                created_issues = self.create_github_issues(high_value_tasks)
                print(f"📋 Created {len(created_issues)} GitHub issues")
        
        # Step 4: Check for ready work
        print("🔍 Checking for ready tasks...")
        ready_tasks = self.work_queue.get_ready_tasks()
        
        if ready_tasks:
            best_task = self.work_queue.select_best_task(ready_tasks)
            if best_task:
                print(f"🎯 Found actionable task: {best_task['title']}")
                # In full implementation, would claim and begin work
        
        cycle_end = datetime.now()
        cycle_duration = (cycle_end - cycle_start).total_seconds()
        
        return {
            "cycle_start": cycle_start.isoformat(),
            "cycle_duration_seconds": cycle_duration,
            "learning_report": learning_report,
            "tasks_generated": len(potential_tasks) if potential_tasks else 0,
            "ready_tasks_found": len(ready_tasks),
            "status": "completed"
        }
    
    def run_continuous(self, cycle_interval_minutes: int = 120):
        """Run continuous autonomous learning"""
        print(f"🚀 Starting continuous autonomous learning (cycle every {cycle_interval_minutes} minutes)")
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                print(f"\n{'='*60}")
                print(f"🔄 Cycle #{cycle_count}")
                
                cycle_result = self.autonomous_cycle()
                
                # Store cycle results
                self.store_cycle_result(cycle_result, cycle_count)
                
                print(f"\n✅ Cycle #{cycle_count} completed in {cycle_result['cycle_duration_seconds']:.1f}s")
                print(f"💤 Sleeping for {cycle_interval_minutes} minutes...")
                
                time.sleep(cycle_interval_minutes * 60)
                
            except KeyboardInterrupt:
                print(f"\n👋 Stopping autonomous learner after {cycle_count} cycles")
                break
            except Exception as e:
                print(f"❌ Error in cycle #{cycle_count}: {e}")
                print("⏸️  Pausing 5 minutes before retry...")
                time.sleep(300)  # 5 minute pause before retry
    
    def store_cycle_result(self, result: Dict, cycle_number: int):
        """Store cycle results for analysis"""
        try:
            import os
            os.makedirs("/workspace/renatlas-identity/data/cycles", exist_ok=True)
            
            filename = f"/workspace/renatlas-identity/data/cycles/cycle_{cycle_number:03d}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Failed to store cycle result: {e}")
    
    def get_cycle_statistics(self) -> Dict:
        """Get statistics across all learning cycles"""
        try:
            import os
            import glob
            
            cycle_files = glob.glob("/workspace/renatlas-identity/data/cycles/cycle_*.json")
            
            if not cycle_files:
                return {"cycles_completed": 0, "total_runtime": 0}
            
            total_duration = 0
            total_tasks = 0
            total_patterns = 0
            
            for cycle_file in cycle_files:
                try:
                    with open(cycle_file, 'r') as f:
                        cycle_data = json.load(f)
                        total_duration += cycle_data.get('cycle_duration_seconds', 0)
                        total_tasks += cycle_data.get('tasks_generated', 0)
                        if 'learning_report' in cycle_data:
                            total_patterns += cycle_data['learning_report'].get('patterns_detected', 0)
                except:
                    continue
            
            return {
                "cycles_completed": len(cycle_files),
                "total_runtime_seconds": total_duration,
                "total_tasks_generated": total_tasks,
                "total_patterns_detected": total_patterns,
                "average_cycle_duration": total_duration / len(cycle_files) if cycle_files else 0
            }
            
        except Exception as e:
            print(f"Error calculating statistics: {e}")
            return {"error": str(e)}

def main():
    """Demo autonomous learning system"""
    learner = AutonomousLearner()
    
    # Run single cycle for testing
    print("🧪 Running single autonomous learning cycle for testing...")
    result = learner.autonomous_cycle()
    
    print(f"\n📊 Cycle Results:")
    print(f"   Duration: {result['cycle_duration_seconds']:.1f} seconds")
    print(f"   Tasks generated: {result['tasks_generated']}")
    print(f"   Ready tasks found: {result['ready_tasks_found']}")
    
    # Show statistics
    stats = learner.get_cycle_statistics()
    print(f"\n📈 Overall Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Uncomment for continuous operation
    # learner.run_continuous(cycle_interval_minutes=60)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Autonomous Learner Dashboard
Simple web interface to monitor learning cycles and system health
"""

import os
import json
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, render_template_string, jsonify
import threading
import time

class LearnerDashboard:
    def __init__(self, data_dir: str = "/workspace/renatlas-identity/data"):
        self.app = Flask(__name__)
        self.data_dir = data_dir
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/')
        def dashboard():
            return render_template_string(self.get_dashboard_template(), 
                                        stats=self.get_system_stats(),
                                        recent_cycles=self.get_recent_cycles(),
                                        status=self.get_system_status())
        
        @self.app.route('/api/stats')
        def api_stats():
            return jsonify(self.get_system_stats())
        
        @self.app.route('/api/health')
        def api_health():
            return jsonify(self.get_system_status())
        
        @self.app.route('/api/cycles')
        def api_cycles():
            return jsonify(self.get_recent_cycles())
    
    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        try:
            cycle_files = glob.glob(f"{self.data_dir}/cycles/cycle_*.json")
            
            if not cycle_files:
                return {
                    "total_cycles": 0,
                    "total_runtime_hours": 0,
                    "avg_cycle_duration": 0,
                    "tasks_generated": 0,
                    "patterns_detected": 0
                }
            
            total_duration = 0
            total_tasks = 0
            total_patterns = 0
            
            for cycle_file in cycle_files:
                try:
                    with open(cycle_file, 'r') as f:
                        data = json.load(f)
                        total_duration += data.get('cycle_duration_seconds', 0)
                        total_tasks += data.get('tasks_generated', 0)
                        if 'learning_report' in data:
                            total_patterns += data['learning_report'].get('patterns_detected', 0)
                except:
                    continue
            
            return {
                "total_cycles": len(cycle_files),
                "total_runtime_hours": round(total_duration / 3600, 2),
                "avg_cycle_duration": round(total_duration / len(cycle_files), 1) if cycle_files else 0,
                "tasks_generated": total_tasks,
                "patterns_detected": total_patterns,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_recent_cycles(self, limit: int = 10) -> List[Dict]:
        """Get recent learning cycles"""
        try:
            cycle_files = glob.glob(f"{self.data_dir}/cycles/cycle_*.json")
            cycle_files.sort(reverse=True)  # Most recent first
            
            recent = []
            for cycle_file in cycle_files[:limit]:
                try:
                    with open(cycle_file, 'r') as f:
                        data = json.load(f)
                        
                    # Extract key info
                    cycle_info = {
                        "file": os.path.basename(cycle_file),
                        "start_time": data.get('cycle_start', ''),
                        "duration": data.get('cycle_duration_seconds', 0),
                        "status": data.get('status', 'unknown'),
                        "tasks_generated": data.get('tasks_generated', 0),
                        "ready_tasks_found": data.get('ready_tasks_found', 0)
                    }
                    
                    # Add learning report summary
                    if 'learning_report' in data:
                        lr = data['learning_report']
                        cycle_info['new_items'] = lr.get('new_items', 0)
                        cycle_info['patterns_detected'] = lr.get('patterns_detected', 0)
                        cycle_info['top_themes'] = lr.get('top_themes', [])
                    
                    recent.append(cycle_info)
                    
                except:
                    continue
            
            return recent
            
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_system_status(self) -> Dict:
        """Get current system health status"""
        status = {
            "status": "healthy",
            "issues": [],
            "last_cycle": None,
            "system_uptime": self.get_uptime(),
            "disk_usage": self.get_disk_usage(),
            "process_health": self.check_process_health()
        }
        
        # Check when last cycle ran
        try:
            cycle_files = glob.glob(f"{self.data_dir}/cycles/cycle_*.json")
            if cycle_files:
                latest_cycle = max(cycle_files, key=os.path.getctime)
                with open(latest_cycle, 'r') as f:
                    data = json.load(f)
                
                status["last_cycle"] = {
                    "time": data.get('cycle_start', ''),
                    "status": data.get('status', 'unknown'),
                    "duration": data.get('cycle_duration_seconds', 0)
                }
                
                # Check if cycles are running regularly
                last_cycle_time = datetime.fromisoformat(data.get('cycle_start', '2000-01-01'))
                if datetime.now() - last_cycle_time > timedelta(hours=3):
                    status["issues"].append("No recent cycles detected (>3 hours)")
                    status["status"] = "warning"
                    
        except Exception as e:
            status["issues"].append(f"Cannot read cycle data: {e}")
            status["status"] = "error"
        
        return status
    
    def get_uptime(self) -> str:
        """Get system uptime"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                hours = int(uptime_seconds // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                return f"{hours}h {minutes}m"
        except:
            return "unknown"
    
    def get_disk_usage(self) -> Dict:
        """Get disk usage for workspace"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/workspace")
            return {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "used_percent": round((used / total) * 100, 1)
            }
        except:
            return {"error": "Cannot get disk usage"}
    
    def check_process_health(self) -> Dict:
        """Check if key processes are healthy"""
        try:
            import psutil
            
            # Look for Python processes running our tools
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline'])
                        if any(tool in cmdline for tool in ['autonomous-learner', 'continuous-learning', 'github-work']):
                            python_processes.append({
                                "pid": proc.info['pid'],
                                "cmd": cmdline[:100] + "..." if len(cmdline) > 100 else cmdline
                            })
                except:
                    continue
            
            return {
                "autonomous_processes": len(python_processes),
                "processes": python_processes
            }
            
        except ImportError:
            return {"error": "psutil not available"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_dashboard_template(self) -> str:
        """HTML template for dashboard"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>Ren Atlas - Autonomous Learner Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 2em; font-weight: bold; color: #2196F3; }
        .stat-label { color: #666; margin-top: 5px; }
        .status { margin-bottom: 20px; }
        .status-healthy { background: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; }
        .status-warning { background: #FF9800; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; }
        .status-error { background: #F44336; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block; }
        .cycles { background: white; padding: 20px; border-radius: 8px; }
        .cycle { border-bottom: 1px solid #eee; padding: 15px 0; }
        .cycle:last-child { border-bottom: none; }
        .cycle-time { color: #666; font-size: 0.9em; }
        .cycle-stats { margin-top: 5px; }
        .badge { background: #e3f2fd; color: #1976d2; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px; }
        .auto-refresh { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Ren Atlas - Autonomous Learner</h1>
            <p>Real-time monitoring of autonomous learning cycles and system health</p>
            <div class="auto-refresh">⟳ Auto-refreshes every 30 seconds</div>
        </div>
        
        <div class="status">
            <span class="status-{{ status.status }}">
                System Status: {{ status.status.title() }}
                {% if status.issues %}
                    - {{ status.issues|length }} issue(s)
                {% endif %}
            </span>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_cycles }}</div>
                <div class="stat-label">Total Learning Cycles</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_runtime_hours }}h</div>
                <div class="stat-label">Total Runtime</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.avg_cycle_duration }}s</div>
                <div class="stat-label">Avg Cycle Duration</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.tasks_generated }}</div>
                <div class="stat-label">Tasks Generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.patterns_detected }}</div>
                <div class="stat-label">Patterns Detected</div>
            </div>
        </div>
        
        <div class="cycles">
            <h2>Recent Learning Cycles</h2>
            {% for cycle in recent_cycles %}
            <div class="cycle">
                <div><strong>{{ cycle.file }}</strong></div>
                <div class="cycle-time">{{ cycle.start_time }}</div>
                <div class="cycle-stats">
                    <span class="badge">{{ cycle.duration }}s</span>
                    <span class="badge">{{ cycle.tasks_generated }} tasks</span>
                    <span class="badge">{{ cycle.ready_tasks_found }} ready</span>
                    {% if cycle.patterns_detected %}
                    <span class="badge">{{ cycle.patterns_detected }} patterns</span>
                    {% endif %}
                    {% for theme in cycle.top_themes[:3] %}
                    <span class="badge">{{ theme }}</span>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
        '''
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the dashboard server"""
        print(f"🚀 Starting Autonomous Learner Dashboard on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)

def main():
    """Run dashboard"""
    import os
    os.makedirs("/workspace/renatlas-identity/data/cycles", exist_ok=True)
    
    dashboard = LearnerDashboard()
    dashboard.run(port=5000)

if __name__ == "__main__":
    main()
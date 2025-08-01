from typing import List,Dict

def generate_schedule(tasks:List[Dict],available_time:int)->List[Dict]:
    """
    Generate a daily task schedule based on available time.
    
    Each task should have:
    - 'title': str
    - 'estimated_time': int (in minutes)
    - 'priority': int (lower = more important)
    - 'deadline': str (optional: YYYY-MM-DD)
    """
    sorted_tasks = sorted(tasks, key=lambda t: (t['priority'], t.get('deadline', '9999-12-31')))
    
    schedule = []
    used_time = 0
    
    for task in sorted_tasks:
        if used_time + task['estimated_time'] <= available_time:
            schedule.append(task)
            used_time += task['estimated_time']
    return schedule
        
    
    
"""
Smart Task Scheduler Module
Optimizes task scheduling based on priority, deadlines, and available time.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def generate_schedule(tasks: List[Dict[str, Any]], available_time: int) -> List[Dict[str, Any]]:
    """
    Generate an optimized schedule based on tasks and available time.
    
    Args:
        tasks: List of task dictionaries with keys: title, estimated_time, priority, deadline
        available_time: Total available time in minutes
    
    Returns:
        List of scheduled tasks with allocated_time
    """
    if not tasks or available_time <= 0:
        return []
    
    # Filter and prepare tasks
    valid_tasks = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
            
        # Ensure required fields exist with defaults
        processed_task = {
            'title': task.get('title', 'Untitled Task'),
            'estimated_time': task.get('estimated_time', 30),
            'priority': task.get('priority', 2),
            'deadline': task.get('deadline'),
            'id': task.get('id')
        }
        
        # Validate and convert data types
        try:
            processed_task['estimated_time'] = int(processed_task['estimated_time'])
            processed_task['priority'] = int(processed_task['priority'])
        except (ValueError, TypeError):
            processed_task['estimated_time'] = 30
            processed_task['priority'] = 2
        
        # Skip tasks that are too long for available time
        if processed_task['estimated_time'] <= available_time:
            valid_tasks.append(processed_task)
    
    if not valid_tasks:
        return []
    
    # Sort tasks by priority algorithm
    sorted_tasks = prioritize_tasks(valid_tasks)
    
    # Allocate time to tasks
    scheduled_tasks = allocate_time(sorted_tasks, available_time)
    
    return scheduled_tasks


def prioritize_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prioritize tasks based on multiple factors:
    1. Priority level (1=High, 2=Medium, 3=Low)
    2. Deadline urgency
    3. Task duration (shorter tasks get slight boost)
    """
    def calculate_priority_score(task: Dict[str, Any]) -> float:
        """Calculate a composite priority score for sorting."""
        
        # Base priority score (lower number = higher priority)
        priority_score = task['priority']
        
        # Deadline urgency factor
        deadline_factor = 0
        if task.get('deadline'):
            try:
                if isinstance(task['deadline'], str):
                    deadline_date = datetime.strptime(task['deadline'], '%Y-%m-%d').date()
                else:
                    deadline_date = task['deadline']
                
                today = datetime.now().date()
                days_until_deadline = (deadline_date - today).days
                
                if days_until_deadline < 0:
                    # Overdue tasks get highest priority
                    deadline_factor = -2.0
                elif days_until_deadline == 0:
                    # Due today
                    deadline_factor = -1.5
                elif days_until_deadline == 1:
                    # Due tomorrow
                    deadline_factor = -1.0
                elif days_until_deadline <= 3:
                    # Due within 3 days
                    deadline_factor = -0.5
                elif days_until_deadline <= 7:
                    # Due within a week
                    deadline_factor = -0.25
                # No adjustment for tasks due later
                
            except (ValueError, TypeError, AttributeError):
                # Invalid deadline format, no adjustment
                pass
        
        # Duration factor (slight preference for shorter tasks when priorities are equal)
        duration_factor = min(task['estimated_time'] / 100.0, 0.5)  # Max 0.5 adjustment
        
        # Combine factors
        final_score = priority_score + deadline_factor + duration_factor
        
        return final_score
    
    # Sort by priority score (lower scores first)
    return sorted(tasks, key=calculate_priority_score)


def allocate_time(sorted_tasks: List[Dict[str, Any]], available_time: int) -> List[Dict[str, Any]]:
    """
    Allocate available time to tasks using intelligent algorithms.
    """
    if not sorted_tasks:
        return []
    
    scheduled_tasks = []
    remaining_time = available_time
    
    # Strategy 1: Try to fit as many high-priority tasks as possible
    for task in sorted_tasks:
        if remaining_time <= 0:
            break
            
        estimated_time = task['estimated_time']
        
        if estimated_time <= remaining_time:
            # Task fits completely
            allocated_time = estimated_time
            remaining_time -= allocated_time
        else:
            # Task doesn't fit completely
            if remaining_time >= 15:  # Minimum 15 minutes to make it worthwhile
                # Allocate remaining time if it's substantial
                allocated_time = remaining_time
                remaining_time = 0
            else:
                # Skip task if remaining time is too small
                continue
        
        scheduled_task = task.copy()
        scheduled_task['allocated_time'] = allocated_time
        scheduled_tasks.append(scheduled_task)
    
    # Strategy 2: If we have remaining time, try to partially schedule more tasks
    if remaining_time >= 15 and len(scheduled_tasks) < len(sorted_tasks):
        for task in sorted_tasks:
            if remaining_time < 15:
                break
                
            # Skip already scheduled tasks
            if any(scheduled['title'] == task['title'] for scheduled in scheduled_tasks):
                continue
            
            # Try to allocate remaining time
            if task['estimated_time'] > remaining_time:
                # Partial allocation
                allocated_time = remaining_time
                remaining_time = 0
                
                scheduled_task = task.copy()
                scheduled_task['allocated_time'] = allocated_time
                scheduled_task['partial'] = True  # Mark as partial
                scheduled_tasks.append(scheduled_task)
                break
    
    return scheduled_tasks


def optimize_daily_schedule(tasks: List[Dict[str, Any]], 
    available_slots: List[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Create an optimized daily schedule with time slots.
    
    Args:
        tasks: List of tasks to schedule
        available_slots: List of time slots with 'start_time' and 'duration' in minutes
    
    Returns:
        Dictionary with scheduled tasks organized by time slots
    """
    if not available_slots:
        # Default slots: morning, afternoon, evening
        available_slots = [
            {'name': 'Morning Focus', 'duration': 120},  # 2 hours
            {'name': 'Afternoon Work', 'duration': 90},   # 1.5 hours
            {'name': 'Evening Tasks', 'duration': 60},    # 1 hour
        ]
    
    schedule = {}
    remaining_tasks = tasks.copy()
    
    for slot in available_slots:
        if not remaining_tasks:
            break
            
        slot_schedule = generate_schedule(remaining_tasks, slot['duration'])
        schedule[slot['name']] = slot_schedule
        
        # Remove scheduled tasks from remaining tasks
        scheduled_titles = {task['title'] for task in slot_schedule}
        remaining_tasks = [
            task for task in remaining_tasks 
            if task['title'] not in scheduled_titles
        ]
    
    # Add any remaining unscheduled tasks
    if remaining_tasks:
        schedule['Unscheduled'] = remaining_tasks
    
    return schedule


def get_task_recommendations(tasks: List[Dict[str, Any]]) -> List[str]:
    """
    Generate recommendations based on task analysis.
    """
    if not tasks:
        return ["Start by adding some tasks to get organized!"]
    
    recommendations = []
    
    # Analyze task distribution
    total_tasks = len(tasks)
    high_priority = sum(1 for task in tasks if task.get('priority') == 1)
    no_deadline = sum(1 for task in tasks if not task.get('deadline'))
    long_tasks = sum(1 for task in tasks if task.get('estimated_time', 0) > 90)
    
    # Check for overloaded high priority
    if high_priority > total_tasks * 0.6:
        recommendations.append(
            "You have many high-priority tasks. Consider reviewing priorities to focus on what's truly urgent."
        )
    
    # Check for missing deadlines
    if no_deadline > total_tasks * 0.5:
        recommendations.append(
            "Many tasks don't have deadlines. Setting deadlines can improve time management and motivation."
        )
    
    # Check for task length balance
    if long_tasks > total_tasks * 0.4:
        recommendations.append(
            "Consider breaking down large tasks into smaller, more manageable chunks for better productivity."
        )
    
    # Deadline urgency check
    today = datetime.now().date()
    overdue_tasks = []
    due_soon = []
    
    for task in tasks:
        if task.get('deadline'):
            try:
                if isinstance(task['deadline'], str):
                    deadline_date = datetime.strptime(task['deadline'], '%Y-%m-%d').date()
                else:
                    deadline_date = task['deadline']
                
                days_until = (deadline_date - today).days
                
                if days_until < 0:
                    overdue_tasks.append(task)
                elif days_until <= 2:
                    due_soon.append(task)
                    
            except (ValueError, TypeError):
                continue
    
    if overdue_tasks:
        recommendations.append(
            f"You have {len(overdue_tasks)} overdue task(s). Consider rescheduling or prioritizing them."
        )
    
    if due_soon:
        recommendations.append(
            f"You have {len(due_soon)} task(s) due within 2 days. Consider prioritizing them in your schedule."
        )
    
    # Time management recommendations
    total_estimated_time = sum(task.get('estimated_time', 0) for task in tasks)
    if total_estimated_time > 480:  # More than 8 hours
        recommendations.append(
            "Your tasks require significant time. Consider spreading them across multiple days."
        )
    
    # Positive reinforcement
    if not recommendations:
        recommendations.append("Great job! Your task management looks well-organized.")
    
    return recommendations


def calculate_completion_stats(completed_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics for completed tasks.
    
    Args:
        completed_tasks: List of completed task dictionaries
    
    Returns:
        Dictionary with completion statistics
    """
    if not completed_tasks:
        return {
            'total_completed': 0,
            'total_time_spent': 0,
            'avg_completion_time': 0,
            'completion_rate_by_priority': {},
            'productivity_score': 0
        }
    
    total_completed = len(completed_tasks)
    total_time_spent = sum(task.get('actual_time', task.get('estimated_time', 0)) for task in completed_tasks)
    avg_completion_time = total_time_spent / total_completed if total_completed > 0 else 0
    
    # Completion rate by priority
    priority_completion = {}
    for priority in [1, 2, 3]:
        priority_tasks = [task for task in completed_tasks if task.get('priority') == priority]
        priority_completion[priority] = len(priority_tasks)
    
    # Calculate productivity score (0-100)
    productivity_score = min(100, (total_completed * 10) + min(total_time_spent / 60, 40))
    
    return {
        'total_completed': total_completed,
        'total_time_spent': total_time_spent,
        'avg_completion_time': round(avg_completion_time, 1),
        'completion_rate_by_priority': priority_completion,
        'productivity_score': round(productivity_score, 1)
    }


def suggest_optimal_work_sessions(tasks: List[Dict[str, Any]], 
                                session_length: int = 25) -> List[Dict[str, Any]]:
    """
    Suggest optimal work sessions (Pomodoro-style) based on tasks.
    
    Args:
        tasks: List of tasks to organize into sessions
        session_length: Length of each work session in minutes (default: 25 for Pomodoro)
    
    Returns:
        List of work sessions with suggested tasks
    """
    if not tasks:
        return []
    
    sessions = []
    prioritized_tasks = prioritize_tasks(tasks)
    current_session_tasks = []
    current_session_time = 0
    session_number = 1
    
    for task in prioritized_tasks:
        task_time = task.get('estimated_time', 30)
        
        # If task fits in current session
        if current_session_time + task_time <= session_length:
            current_session_tasks.append(task)
            current_session_time += task_time
        else:
            # Save current session if it has tasks
            if current_session_tasks:
                sessions.append({
                    'session_number': session_number,
                    'tasks': current_session_tasks.copy(),
                    'total_time': current_session_time,
                    'break_after': session_number % 4 == 0  # Long break every 4 sessions
                })
                session_number += 1
            
            # Start new session with current task
            if task_time <= session_length:
                current_session_tasks = [task]
                current_session_time = task_time
            else:
                # Task is too long for a single session, suggest breaking it down
                sessions.append({
                    'session_number': session_number,
                    'tasks': [task],
                    'total_time': session_length,
                    'note': f"Consider breaking down '{task['title']}' - it's longer than a single session",
                    'partial_task': True
                })
                session_number += 1
                current_session_tasks = []
                current_session_time = 0
    
    # Add final session if it has tasks
    if current_session_tasks:
        sessions.append({
            'session_number': session_number,
            'tasks': current_session_tasks,
            'total_time': current_session_time,
            'break_after': session_number % 4 == 0
        })
    
    return sessions


def estimate_completion_time(tasks: List[Dict[str, Any]], 
    efficiency_factor: float = 0.8) -> Dict[str, Any]:
    """
    Estimate when tasks will be completed based on available time and efficiency.
    
    Args:
        tasks: List of tasks to analyze
        efficiency_factor: Factor to account for interruptions, breaks, etc. (0.0-1.0)
    
    Returns:
        Dictionary with completion estimates
    """
    if not tasks:
        return {'total_time': 0, 'estimated_completion': None, 'daily_breakdown': []}
    
    total_estimated_time = sum(task.get('estimated_time', 0) for task in tasks)
    adjusted_time = total_estimated_time / efficiency_factor
    
    # Assume 6 productive hours per day (360 minutes)
    daily_capacity = 360
    days_needed = adjusted_time / daily_capacity
    
    # Calculate completion date
    completion_date = datetime.now() + timedelta(days=int(days_needed) + 1)
    
    # Break down by priority
    high_priority_time = sum(task.get('estimated_time', 0) for task in tasks if task.get('priority') == 1)
    medium_priority_time = sum(task.get('estimated_time', 0) for task in tasks if task.get('priority') == 2)
    low_priority_time = sum(task.get('estimated_time', 0) for task in tasks if task.get('priority') == 3)
    
    return {
        'total_time': total_estimated_time,
        'adjusted_time': round(adjusted_time),
        'days_needed': round(days_needed, 1),
        'estimated_completion': completion_date.strftime('%Y-%m-%d'),
        'priority_breakdown': {
            'high': high_priority_time,
            'medium': medium_priority_time,
            'low': low_priority_time
        },
        'daily_capacity': daily_capacity,
        'efficiency_factor': efficiency_factor
    }
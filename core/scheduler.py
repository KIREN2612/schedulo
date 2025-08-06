"""
Task Scheduling Engine for TaskFlow
Provides intelligent task scheduling and optimization algorithms
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import math


def optimize_schedule_for_energy(tasks: List[Dict], energy_pattern: str = "morning") -> List[Dict]:
    """
    Optimize task schedule based on user's energy patterns
    
    Args:
        tasks: List of tasks to schedule
        energy_pattern: "morning", "afternoon", or "evening" for peak energy
        
    Returns:
        Reordered tasks optimized for energy levels
    """
    try:
        if not tasks:
            return []
        
        # Categorize tasks by energy requirement
        high_energy_tasks = []
        medium_energy_tasks = []
        low_energy_tasks = []
        
        for task in tasks:
            estimated_time = task.get('estimated_time', 30)
            priority = task.get('priority', 2)
            
            # Determine energy requirement
            if priority == 1 and estimated_time > 60:  # High priority, long tasks
                high_energy_tasks.append(task)
            elif priority == 1 or estimated_time > 90:  # High priority or very long
                medium_energy_tasks.append(task)
            else:
                low_energy_tasks.append(task)
        
        # Arrange based on energy pattern
        if energy_pattern == "morning":
            # High energy tasks first, then medium, then low
            optimized_schedule = high_energy_tasks + medium_energy_tasks + low_energy_tasks
        elif energy_pattern == "afternoon":
            # Medium energy tasks first, then high, then low
            optimized_schedule = medium_energy_tasks + high_energy_tasks + low_energy_tasks
        else:  # evening
            # Low energy tasks first, then medium, then high (if any energy left)
            optimized_schedule = low_energy_tasks + medium_energy_tasks + high_energy_tasks
        
        # Add optimization metadata
        for i, task in enumerate(optimized_schedule):
            task['energy_optimized_order'] = i + 1
            task['energy_category'] = (
                'high' if task in high_energy_tasks else
                'medium' if task in medium_energy_tasks else
                'low'
            )
        
        return optimized_schedule
        
    except Exception as e:
        print(f"Error optimizing schedule for energy: {str(e)}")
        return tasks


def calculate_schedule_efficiency(scheduled_tasks: List[Dict], available_time: int) -> Dict[str, Any]:
    """
    Calculate efficiency metrics for a given schedule
    
    Args:
        scheduled_tasks: List of tasks in the schedule
        available_time: Total available time
        
    Returns:
        Dictionary with efficiency metrics
    """
    try:
        if not scheduled_tasks or available_time <= 0:
            return {
                'time_utilization': 0,
                'priority_score': 0,
                'task_count': 0,
                'estimated_completion': 0
            }
        
        total_allocated_time = sum(task.get('allocated_time', 0) for task in scheduled_tasks)
        time_utilization = (total_allocated_time / available_time) * 100
        
        # Calculate priority score (higher is better)
        priority_score = 0
        for task in scheduled_tasks:
            priority = task.get('priority', 2)
            allocated_time = task.get('allocated_time', 0)
            
            if priority == 1:  # High priority
                priority_score += allocated_time * 3
            elif priority == 2:  # Medium priority
                priority_score += allocated_time * 2
            else:  # Low priority
                priority_score += allocated_time * 1
        
        # Normalize priority score
        max_possible_score = available_time * 3  # If all time was high priority
        normalized_priority_score = (priority_score / max_possible_score) * 100 if max_possible_score > 0 else 0
        
        # Calculate estimated completion percentage
        total_task_time = sum(task.get('estimated_time', 0) for task in scheduled_tasks)
        estimated_completion = (total_allocated_time / total_task_time) * 100 if total_task_time > 0 else 0
        
        return {
            'time_utilization': round(time_utilization, 2),
            'priority_score': round(normalized_priority_score, 2),
            'task_count': len(scheduled_tasks),
            'total_allocated_time': total_allocated_time,
            'estimated_completion': round(estimated_completion, 2),
            'schedule_quality': _calculate_schedule_quality(scheduled_tasks)
        }
        
    except Exception as e:
        return {
            'error': f"Failed to calculate schedule efficiency: {str(e)}",
            'time_utilization': 0,
            'priority_score': 0,
            'task_count': 0
        }


def _calculate_schedule_quality(tasks: List[Dict]) -> str:
    """Calculate overall schedule quality rating"""
    try:
        if not tasks:
            return "poor"
        
        score = 0
        total_factors = 0
        
        # Factor 1: Priority distribution
        high_priority = sum(1 for t in tasks if t.get('priority') == 1)
        medium_priority = sum(1 for t in tasks if t.get('priority') == 2)
        low_priority = sum(1 for t in tasks if t.get('priority') == 3)
        
        if high_priority > 0:
            score += 30
        if medium_priority > 0:
            score += 20
        if low_priority > 0:
            score += 10
        total_factors += 60
        
        # Factor 2: Task size variety
        short_tasks = sum(1 for t in tasks if t.get('allocated_time', 0) <= 30)
        long_tasks = sum(1 for t in tasks if t.get('allocated_time', 0) > 90)
        
        if short_tasks > 0 and long_tasks > 0:
            score += 20  # Good variety
        elif short_tasks > 0 or long_tasks > 0:
            score += 10  # Some variety
        total_factors += 20
        
        # Factor 3: Completion potential
        avg_completion = sum(t.get('completion_percentage', 0) for t in tasks) / len(tasks)
        if avg_completion >= 80:
            score += 20
        elif avg_completion >= 60:
            score += 15
        elif avg_completion >= 40:
            score += 10
        total_factors += 20
        
        # Calculate final quality
        quality_percentage = (score / total_factors) * 100 if total_factors > 0 else 0
        
        if quality_percentage >= 80:
            return "excellent"
        elif quality_percentage >= 60:
            return "good"
        elif quality_percentage >= 40:
            return "fair"
        else:
            return "poor"
            
    except Exception:
        return "unknown"


def suggest_task_splitting(task: Dict[str, Any], max_session_time: int = 90) -> List[Dict[str, Any]]:
    """
    Suggest how to split a large task into smaller sessions
    
    Args:
        task: Task dictionary to potentially split
        max_session_time: Maximum time per session in minutes
        
    Returns:
        List of task sessions or original task if no splitting needed
    """
    try:
        estimated_time = task.get('estimated_time', 30)
        
        # Don't split if task is already small enough
        if estimated_time <= max_session_time:
            return [task]
        
        # Calculate number of sessions needed
        num_sessions = math.ceil(estimated_time / max_session_time)
        time_per_session = estimated_time / num_sessions
        
        sessions = []
        for i in range(num_sessions):
            session = task.copy()
            session['title'] = f"{task.get('title', 'Task')} - Session {i + 1}"
            session['estimated_time'] = round(time_per_session)
            session['is_split_task'] = True
            session['original_task_id'] = task.get('id')
            session['session_number'] = i + 1
            session['total_sessions'] = num_sessions
            
            # Adjust priority for later sessions (slightly lower)
            if i > 0 and task.get('priority', 2) > 1:
                session['priority'] = min(3, task.get('priority', 2) + 1)
            
            sessions.append(session)
        
        return sessions
        
    except Exception as e:
        print(f"Error splitting task: {str(e)}")
        return [task]


def generate_focus_schedule(tasks: List[Dict], session_length: int = 25, break_length: int = 5) -> List[Dict]:
    """
    Generate a Pomodoro-style focus schedule
    
    Args:
        tasks: List of tasks to schedule
        session_length: Length of focus session in minutes (default: 25 for Pomodoro)
        break_length: Length of break in minutes
        
    Returns:
        List of focus sessions and breaks
    """
    try:
        if not tasks:
            return []
        
        schedule = []
        session_count = 0
        
        for task in tasks:
            estimated_time = task.get('estimated_time', 30)
            sessions_needed = math.ceil(estimated_time / session_length)
            
            for session in range(sessions_needed):
                session_count += 1
                
                # Focus session
                focus_session = {
                    'type': 'focus',
                    'task_id': task.get('id'),
                    'task_title': task.get('title', 'Task'),
                    'session_number': session + 1,
                    'total_sessions_for_task': sessions_needed,
                    'duration': min(session_length, estimated_time - (session * session_length)),
                    'priority': task.get('priority', 2),
                    'session_count': session_count
                }
                schedule.append(focus_session)
                
                # Break (except after the last session)
                if session < sessions_needed - 1 or task != tasks[-1]:
                    break_type = "long" if session_count % 4 == 0 else "short"
                    break_duration = break_length * 3 if break_type == "long" else break_length
                    
                    break_session = {
                        'type': 'break',
                        'break_type': break_type,
                        'duration': break_duration,
                        'suggestion': _get_break_suggestion(break_type)
                    }
                    schedule.append(break_session)
        
        return schedule
        
    except Exception as e:
        print(f"Error generating focus schedule: {str(e)}")
        return []


def _get_break_suggestion(break_type: str) -> str:
    """Get a suggestion for what to do during a break"""
    short_break_suggestions = [
        "Stand up and stretch",
        "Take a few deep breaths",
        "Look away from your screen",
        "Drink some water",
        "Do a quick walk around"
    ]
    
    long_break_suggestions = [
        "Take a walk outside",
        "Have a healthy snack",
        "Do some light exercise",
        "Practice mindfulness",
        "Chat with a friend"
    ]
    
    import random
    if break_type == "long":
        return random.choice(long_break_suggestions)
    else:
        return random.choice(short_break_suggestions)


def generate_schedule(tasks: List[Dict], available_time: int) -> List[Dict]:
    """
    Generate an optimized task schedule based on available time and priorities
    
    Args:
        tasks: List of task dictionaries with keys: id, title, estimated_time, priority, deadline
        available_time: Available time in minutes
        
    Returns:
        List of scheduled tasks with allocated time slots
    """
    try:
        if not tasks or available_time <= 0:
            return []
        
        # Filter out completed tasks and sort by priority and deadline
        active_tasks = [task for task in tasks if not task.get('completed', False)]
        
        if not active_tasks:
            return []
        
        # Sort tasks by scheduling priority
        scheduled_tasks = _prioritize_tasks(active_tasks)
        
        # Allocate time slots
        allocated_tasks = []
        remaining_time = available_time
        
        for task in scheduled_tasks:
            if remaining_time <= 0:
                break
                
            estimated_time = task.get('estimated_time', 30)
            
            # Allocate available time, but don't exceed task's estimated time
            allocated_time = min(estimated_time, remaining_time)
            
            if allocated_time >= 15:  # Minimum 15 minutes to be useful
                scheduled_task = task.copy()
                scheduled_task['allocated_time'] = allocated_time
                scheduled_task['remaining_time'] = max(0, estimated_time - allocated_time)
                scheduled_task['completion_percentage'] = min(100, (allocated_time / estimated_time) * 100)
                
                allocated_tasks.append(scheduled_task)
                remaining_time -= allocated_time
        
        # Add scheduling metadata
        for i, task in enumerate(allocated_tasks):
            task['schedule_order'] = i + 1
            task['recommended_break'] = _calculate_break_time(task['allocated_time'])
        
        return allocated_tasks
        
    except Exception as e:
        print(f"Error in generate_schedule: {str(e)}")
        return []


def _prioritize_tasks(tasks: List[Dict]) -> List[Dict]:
    """
    Prioritize tasks based on multiple factors
    
    Priority scoring factors:
    - Task priority (1=High, 2=Medium, 3=Low)
    - Deadline urgency
    - Task size (shorter tasks get slight boost)
    """
    def calculate_priority_score(task):
        score = 0
        
        # Base priority score (lower number = higher priority)
        priority = task.get('priority', 2)
        if priority == 1:  # High
            score += 100
        elif priority == 2:  # Medium
            score += 50
        else:  # Low
            score += 10
        
        # Deadline urgency bonus
        deadline_str = task.get('deadline')
        if deadline_str:
            try:
                if isinstance(deadline_str, str):
                    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
                else:
                    deadline = deadline_str
                    
                today = date.today()
                days_until_deadline = (deadline - today).days
                
                if days_until_deadline < 0:  # Overdue
                    score += 80
                elif days_until_deadline == 0:  # Due today
                    score += 60
                elif days_until_deadline <= 3:  # Due within 3 days
                    score += 40
                elif days_until_deadline <= 7:  # Due within a week
                    score += 20
            except (ValueError, TypeError):
                pass
        
        # Small boost for shorter tasks (easier to complete)
        estimated_time = task.get('estimated_time', 30)
        if estimated_time <= 30:
            score += 5
        elif estimated_time <= 60:
            score += 3
        
        return score
    
    # Sort by priority score (descending) then by estimated time (ascending)
    return sorted(tasks, key=lambda t: (-calculate_priority_score(t), t.get('estimated_time', 30)))


def _calculate_break_time(task_time: int) -> int:
    """Calculate recommended break time after a task"""
    if task_time <= 30:
        return 5
    elif task_time <= 60:
        return 10
    elif task_time <= 120:
        return 15
    else:
        return 20


def get_task_recommendations(tasks: List[Dict]) -> List[str]:
    """
    Generate task management recommendations based on current task load
    
    Args:
        tasks: List of all tasks
        
    Returns:
        List of recommendation strings
    """
    try:
        recommendations = []
        
        if not tasks:
            return ["🎯 Start by adding some tasks to get personalized recommendations!"]
        
        active_tasks = [task for task in tasks if not task.get('completed', False)]
        completed_tasks = [task for task in tasks if task.get('completed', False)]
        
        # Analyze task distribution
        high_priority = sum(1 for t in active_tasks if t.get('priority') == 1)
        medium_priority = sum(1 for t in active_tasks if t.get('priority') == 2)
        low_priority = sum(1 for t in active_tasks if t.get('priority') == 3)
        
        # Check for overdue tasks
        today = date.today()
        overdue_tasks = []
        for task in active_tasks:
            deadline_str = task.get('deadline')
            if deadline_str:
                try:
                    if isinstance(deadline_str, str):
                        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
                    else:
                        deadline = deadline_str
                    if deadline < today:
                        overdue_tasks.append(task)
                except (ValueError, TypeError):
                    continue
        
        # Generate recommendations
        if len(overdue_tasks) > 0:
            recommendations.append(f"🚨 You have {len(overdue_tasks)} overdue task{'s' if len(overdue_tasks) > 1 else ''}. Consider addressing these first!")
        
        if len(active_tasks) > 20:
            recommendations.append("📊 You have many active tasks. Consider breaking large tasks into smaller, manageable pieces.")
        elif len(active_tasks) < 3:
            recommendations.append("🎯 Great job staying on top of your tasks! Consider planning ahead by adding upcoming tasks.")
        
        if high_priority > 5:
            recommendations.append("⚡ You have many high-priority tasks. Focus on completing a few before adding more.")
        elif high_priority == 0 and len(active_tasks) > 0:
            recommendations.append("📈 Consider setting priorities for your tasks to improve focus and productivity.")
        
        # Time management recommendations
        total_estimated_time = sum(task.get('estimated_time', 30) for task in active_tasks)
        if total_estimated_time > 480:  # More than 8 hours
            recommendations.append("⏰ Your task load is quite heavy. Consider scheduling tasks across multiple days.")
        
        # Completion rate analysis
        if len(tasks) > 0:
            completion_rate = len(completed_tasks) / len(tasks)
            if completion_rate < 0.3:
                recommendations.append("🎪 Try focusing on completing smaller tasks first to build momentum.")
            elif completion_rate > 0.8:
                recommendations.append("🌟 Excellent completion rate! You're doing great at following through on tasks.")
        
        # Deadline management
        tasks_with_deadlines = sum(1 for t in active_tasks if t.get('deadline'))
        if tasks_with_deadlines < len(active_tasks) / 2:
            recommendations.append("📅 Consider setting deadlines for more tasks to improve time management.")
        
        # Task size recommendations
        long_tasks = sum(1 for t in active_tasks if t.get('estimated_time', 30) > 120)
        if long_tasks > len(active_tasks) / 3:
            recommendations.append("✂️ You have several long tasks. Consider breaking them into smaller, 30-60 minute chunks.")
        
        if not recommendations:
            recommendations.append("✨ Your task management looks well-balanced! Keep up the good work.")
        
        return recommendations[:5]  # Return top 5 recommendations
        
    except Exception as e:
        return [f"Unable to generate recommendations: {str(e)}"]


def calculate_completion_stats(tasks: List[Dict]) -> Dict[str, Any]:
    """
    Calculate detailed completion statistics
    
    Args:
        tasks: List of all tasks
        
    Returns:
        Dictionary containing completion statistics
    """
    try:
        if not tasks:
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'completion_rate': 0,
                'avg_completion_time': 0,
                'priority_stats': {},
                'time_accuracy': 0
            }
        
        completed_tasks = [task for task in tasks if task.get('completed', False)]
        active_tasks = [task for task in tasks if not task.get('completed', False)]
        
        total_tasks = len(tasks)
        completed_count = len(completed_tasks)
        completion_rate = (completed_count / total_tasks) * 100 if total_tasks > 0 else 0
        
        # Calculate average completion time
        completion_times = []
        time_accuracies = []
        
        for task in completed_tasks:
            actual_time = task.get('actual_time')
            estimated_time = task.get('estimated_time', 30)
            
            if actual_time:
                completion_times.append(actual_time)
                # Calculate time estimation accuracy
                accuracy = min(100, (estimated_time / actual_time) * 100) if actual_time > 0 else 100
                time_accuracies.append(accuracy)
            else:
                completion_times.append(estimated_time)
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        avg_time_accuracy = sum(time_accuracies) / len(time_accuracies) if time_accuracies else 100
        
        # Priority-based statistics
        priority_stats = {}
        for priority in [1, 2, 3]:
            priority_name = {1: 'high', 2: 'medium', 3: 'low'}[priority]
            
            priority_tasks = [t for t in tasks if t.get('priority') == priority]
            priority_completed = [t for t in priority_tasks if t.get('completed', False)]
            
            priority_stats[priority_name] = {
                'total': len(priority_tasks),
                'completed': len(priority_completed),
                'completion_rate': (len(priority_completed) / len(priority_tasks)) * 100 if priority_tasks else 0,
                'avg_time': sum(t.get('actual_time', t.get('estimated_time', 30)) 
                              for t in priority_completed) / len(priority_completed) if priority_completed else 0
            }
        
        # Deadline performance
        deadline_performance = _analyze_deadline_performance(tasks)
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_count,
            'active_tasks': len(active_tasks),
            'completion_rate': round(completion_rate, 2),
            'avg_completion_time': round(avg_completion_time, 2),
            'time_accuracy': round(avg_time_accuracy, 2),
            'priority_stats': {k: {**v, 'completion_rate': round(v['completion_rate'], 2), 
                                  'avg_time': round(v['avg_time'], 2)} 
                              for k, v in priority_stats.items()},
            'deadline_performance': deadline_performance
        }
        
    except Exception as e:
        return {
            'error': f"Failed to calculate completion stats: {str(e)}",
            'total_tasks': 0,
            'completed_tasks': 0,
            'completion_rate': 0
        }


def _analyze_deadline_performance(tasks: List[Dict]) -> Dict[str, Any]:
    """Analyze how well the user meets deadlines"""
    try:
        tasks_with_deadlines = []
        
        for task in tasks:
            if task.get('deadline') and task.get('completed'):
                tasks_with_deadlines.append(task)
        
        if not tasks_with_deadlines:
            return {
                'tasks_with_deadlines': 0,
                'on_time_completion': 0,
                'late_completion': 0,
                'avg_days_early': 0
            }
        
        on_time = 0
        late = 0
        days_differences = []
        
        for task in tasks_with_deadlines:
            try:
                deadline_str = task.get('deadline')
                completed_at = task.get('completed_at')
                
                if isinstance(deadline_str, str):
                    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
                else:
                    deadline = deadline_str
                
                if completed_at:
                    if isinstance(completed_at, str):
                        completion_date = datetime.strptime(completed_at, '%Y-%m-%d').date()
                    else:
                        completion_date = completed_at.date() if hasattr(completed_at, 'date') else completed_at
                    
                    days_diff = (deadline - completion_date).days
                    days_differences.append(days_diff)
                    
                    if days_diff >= 0:
                        on_time += 1
                    else:
                        late += 1
                        
            except (ValueError, TypeError, AttributeError):
                continue
        
        avg_days_early = sum(days_differences) / len(days_differences) if days_differences else 0
        
        return {
            'tasks_with_deadlines': len(tasks_with_deadlines),
            'on_time_completion': on_time,
            'late_completion': late,
            'on_time_rate': round((on_time / len(tasks_with_deadlines)) * 100, 2) if tasks_with_deadlines else 0,
            'avg_days_early': round(avg_days_early, 2)
        }
        
    except Exception as e:
        return {
            'error': f"Failed to analyze deadline performance: {str(e)}",
            'tasks_with_deadlines': 0,
            'on_time_completion': 0,
            'late_completion': 0
        }
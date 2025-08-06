"""
Analytics utilities for TaskFlow
Provides functions for calculating user performance metrics and trends
"""

from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import Task, UserStats, db


def calculate_weekly_performance():
    """Calculate weekly performance metrics"""
    try:
        # Get date range for the last 7 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        # Get tasks completed in the last week
        completed_tasks = Task.query.filter(
            Task.completed == True,
            Task.completed_at >= datetime.combine(start_date, datetime.min.time()),
            Task.completed_at <= datetime.combine(end_date, datetime.max.time())
        ).all()
        
        # Calculate daily completion counts
        daily_counts = {}
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            daily_counts[current_date.strftime('%Y-%m-%d')] = 0
        
        # Count completed tasks per day
        for task in completed_tasks:
            completion_date = task.completed_at.date()
            date_str = completion_date.strftime('%Y-%m-%d')
            if date_str in daily_counts:
                daily_counts[date_str] += 1
        
        # Calculate metrics
        total_completed = len(completed_tasks)
        avg_daily_completion = total_completed / 7
        
        # Calculate total time spent
        total_time = sum(task.actual_time or task.estimated_time for task in completed_tasks)
        avg_daily_time = total_time / 7
        
        # Calculate completion rate (completed vs created in this period)
        total_tasks_created = Task.query.filter(
            Task.created_at >= datetime.combine(start_date, datetime.min.time()),
            Task.created_at <= datetime.combine(end_date, datetime.max.time())
        ).count()
        
        completion_rate = (total_completed / total_tasks_created * 100) if total_tasks_created > 0 else 0
        
        # Priority distribution of completed tasks
        priority_stats = {
            'high': sum(1 for t in completed_tasks if t.priority == 1),
            'medium': sum(1 for t in completed_tasks if t.priority == 2),
            'low': sum(1 for t in completed_tasks if t.priority == 3)
        }
        
        return {
            'period': f"{start_date} to {end_date}",
            'daily_completion_counts': daily_counts,
            'total_completed': total_completed,
            'avg_daily_completion': round(avg_daily_completion, 2),
            'total_time_minutes': total_time,
            'avg_daily_time': round(avg_daily_time, 2),
            'completion_rate': round(completion_rate, 1),
            'priority_distribution': priority_stats,
            'most_productive_day': max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None
        }
        
    except Exception as e:
        return {
            'error': f"Failed to calculate weekly performance: {str(e)}",
            'period': 'last 7 days',
            'daily_completion_counts': {},
            'total_completed': 0,
            'avg_daily_completion': 0,
            'total_time_minutes': 0,
            'avg_daily_time': 0,
            'completion_rate': 0,
            'priority_distribution': {'high': 0, 'medium': 0, 'low': 0}
        }


def calculate_monthly_stats():
    """Calculate monthly performance statistics"""
    try:
        # Get date range for the last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Get all tasks from the last month
        monthly_tasks = Task.query.filter(
            Task.created_at >= datetime.combine(start_date, datetime.min.time()),
            Task.created_at <= datetime.combine(end_date, datetime.max.time())
        ).all()
        
        completed_tasks = [t for t in monthly_tasks if t.completed]
        active_tasks = [t for t in monthly_tasks if not t.completed]
        
        # Calculate basic metrics
        total_tasks = len(monthly_tasks)
        total_completed = len(completed_tasks)
        completion_percentage = (total_completed / total_tasks * 100) if total_tasks > 0 else 0
        
        # Time analysis
        total_estimated_time = sum(t.estimated_time for t in monthly_tasks)
        total_actual_time = sum(t.actual_time or t.estimated_time for t in completed_tasks)
        time_efficiency = (total_actual_time / total_estimated_time * 100) if total_estimated_time > 0 else 0
        
        # Weekly breakdown
        weekly_stats = []
        for week in range(4):
            week_start = start_date + timedelta(days=week * 7)
            week_end = min(week_start + timedelta(days=6), end_date)
            
            week_tasks = [t for t in monthly_tasks if 
                        week_start <= t.created_at.date() <= week_end]
            week_completed = [t for t in week_tasks if t.completed]
            
            weekly_stats.append({
                'week': week + 1,
                'period': f"{week_start} to {week_end}",
                'tasks_created': len(week_tasks),
                'tasks_completed': len(week_completed),
                'completion_rate': (len(week_completed) / len(week_tasks) * 100) if week_tasks else 0
            })
        
        # Priority analysis
        priority_analysis = {}
        for priority in [1, 2, 3]:
            priority_tasks = [t for t in monthly_tasks if t.priority == priority]
            priority_completed = [t for t in priority_tasks if t.completed]
            
            priority_name = {1: 'high', 2: 'medium', 3: 'low'}[priority]
            priority_analysis[priority_name] = {
                'total': len(priority_tasks),
                'completed': len(priority_completed),
                'completion_rate': (len(priority_completed) / len(priority_tasks) * 100) if priority_tasks else 0
            }
        
        # Streak analysis
        user_stats = UserStats.query.filter_by(user_id='default_user').first()
        streak_info = {
            'current_streak': user_stats.current_streak if user_stats else 0,
            'longest_streak': user_stats.longest_streak if user_stats else 0
        }
        
        return {
            'period': f"{start_date} to {end_date}",
            'total_tasks': total_tasks,
            'total_completed': total_completed,
            'completion_percentage': round(completion_percentage, 1),
            'total_estimated_time': total_estimated_time,
            'total_actual_time': total_actual_time,
            'time_efficiency': round(time_efficiency, 1),
            'weekly_breakdown': weekly_stats,
            'priority_analysis': priority_analysis,
            'streak_info': streak_info,
            'avg_tasks_per_day': round(total_tasks / 30, 2),
            'avg_completion_per_day': round(total_completed / 30, 2)
        }
        
    except Exception as e:
        return {
            'error': f"Failed to calculate monthly stats: {str(e)}",
            'period': 'last 30 days',
            'total_tasks': 0,
            'total_completed': 0,
            'completion_percentage': 0
        }


def get_productivity_trends(days=30):
    """Get productivity trends over specified number of days"""
    try:
        if days <= 0 or days > 365:
            days = 30
        
        # Get date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get tasks from the specified period
        tasks = Task.query.filter(
            Task.created_at >= datetime.combine(start_date, datetime.min.time()),
            Task.created_at <= datetime.combine(end_date, datetime.max.time())
        ).all()
        
        if not tasks:
            return {
                'period_days': days,
                'trends': [],
                'summary': {
                    'trend_direction': 'neutral',
                    'avg_daily_completion': 0,
                    'total_tasks': 0
                }
            }
        
        # Create daily data points
        daily_data = {}
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            daily_data[current_date] = {
                'date': current_date.strftime('%Y-%m-%d'),
                'tasks_created': 0,
                'tasks_completed': 0,
                'completion_rate': 0,
                'total_time': 0,
                'avg_priority': 0
            }
        
        # Populate daily data
        for task in tasks:
            task_date = task.created_at.date()
            if task_date in daily_data:
                daily_data[task_date]['tasks_created'] += 1
                daily_data[task_date]['total_time'] += task.estimated_time
                
                if task.completed:
                    daily_data[task_date]['tasks_completed'] += 1
        
        # Calculate completion rates and trends
        trend_points = []
        completion_rates = []
        
        for date_key in sorted(daily_data.keys()):
            day_data = daily_data[date_key]
            
            if day_data['tasks_created'] > 0:
                completion_rate = (day_data['tasks_completed'] / day_data['tasks_created']) * 100
                day_data['completion_rate'] = round(completion_rate, 1)
                completion_rates.append(completion_rate)
            
            trend_points.append(day_data)
        
        # Calculate trend direction
        if len(completion_rates) >= 2:
            recent_avg = sum(completion_rates[-7:]) / min(7, len(completion_rates[-7:]))
            earlier_avg = sum(completion_rates[:7]) / min(7, len(completion_rates[:7]))
            
            if recent_avg > earlier_avg + 5:
                trend_direction = 'improving'
            elif recent_avg < earlier_avg - 5:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        # Calculate summary statistics
        total_tasks = len(tasks)
        total_completed = sum(1 for t in tasks if t.completed)
        avg_daily_completion = total_completed / days
        
        summary = {
            'trend_direction': trend_direction,
            'avg_daily_completion': round(avg_daily_completion, 2),
            'total_tasks': total_tasks,
            'total_completed': total_completed,
            'overall_completion_rate': round((total_completed / total_tasks * 100), 1) if total_tasks > 0 else 0,
            'most_productive_day': max(trend_points, key=lambda x: x['tasks_completed']) if trend_points else None,
            'least_productive_day': min(trend_points, key=lambda x: x['tasks_completed']) if trend_points else None
        }
        
        return {
            'period_days': days,
            'period_range': f"{start_date} to {end_date}",
            'trends': trend_points,
            'summary': summary,
            'completion_rate_trend': completion_rates
        }
        
    except Exception as e:
        return {
            'error': f"Failed to calculate productivity trends: {str(e)}",
            'period_days': days,
            'trends': [],
            'summary': {
                'trend_direction': 'error',
                'avg_daily_completion': 0,
                'total_tasks': 0
            }
        }


def get_task_completion_analytics():
    """Get detailed task completion analytics"""
    try:
        all_tasks = Task.query.all()
        completed_tasks = [t for t in all_tasks if t.completed]
        
        if not completed_tasks:
            return {
                'message': 'No completed tasks available for analysis',
                'analytics': {}
            }
        
        # Time accuracy analysis
        time_accuracy = []
        for task in completed_tasks:
            if task.actual_time and task.estimated_time:
                accuracy = (task.actual_time / task.estimated_time) * 100
                time_accuracy.append({
                    'task_id': task.id,
                    'estimated': task.estimated_time,
                    'actual': task.actual_time,
                    'accuracy_percentage': round(accuracy, 1),
                    'variance': task.actual_time - task.estimated_time
                })
        
        # Average time accuracy
        avg_accuracy = sum(t['accuracy_percentage'] for t in time_accuracy) / len(time_accuracy) if time_accuracy else 100
        
        # Priority completion analysis
        priority_completion = {}
        for priority in [1, 2, 3]:
            priority_tasks = [t for t in all_tasks if t.priority == priority]
            priority_completed = [t for t in priority_tasks if t.completed]
            
            priority_name = {1: 'high', 2: 'medium', 3: 'low'}[priority]
            
            if priority_tasks:
                avg_completion_time = sum(t.actual_time or t.estimated_time for t in priority_completed) / len(priority_completed) if priority_completed else 0
                
                priority_completion[priority_name] = {
                    'total_tasks': len(priority_tasks),
                    'completed_tasks': len(priority_completed),
                    'completion_rate': round((len(priority_completed) / len(priority_tasks)) * 100, 1),
                    'avg_completion_time': round(avg_completion_time, 1)
                }
        
        return {
            'total_analyzed_tasks': len(completed_tasks),
            'time_accuracy_analysis': {
                'individual_tasks': time_accuracy,
                'avg_accuracy_percentage': round(avg_accuracy, 1),
                'total_tasks_with_time_data': len(time_accuracy)
            },
            'priority_completion_analysis': priority_completion,
            'overall_completion_rate': round((len(completed_tasks) / len(all_tasks)) * 100, 1) if all_tasks else 0
        }
        
    except Exception as e:
        return {
            'error': f"Failed to calculate completion analytics: {str(e)}",
            'analytics': {}
        }
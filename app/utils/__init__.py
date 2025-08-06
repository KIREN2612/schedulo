"""
Utility modules for TaskFlow application
"""

from .analytics import (
    calculate_weekly_performance,
    calculate_monthly_stats, 
    get_productivity_trends,
    get_task_completion_analytics
)

__all__ = [
    'calculate_weekly_performance',
    'calculate_monthly_stats',
    'get_productivity_trends', 
    'get_task_completion_analytics'
]
/**
 * TaskFlow - Smart Task Scheduling Application
 * Main JavaScript Application File
 */

// ====================================
// GLOBAL VARIABLES & CONFIGURATION
// ====================================

let currentTasks = [];
let currentStats = {};

// Performance monitoring
let lastLoadTime = Date.now();

// ====================================
// INITIALIZATION & SETUP
// ====================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 TaskFlow initializing...');
    
    initializeApplication();
    setupEventListeners();
    setupPerformanceMonitoring();
    
    console.log('🚀 TaskFlow initialized successfully!');
});

function initializeApplication() {
    loadDashboard();
    setTodayAsMinDate();
    loadSavedForm();
    
    // Load initial data with staggered loading for better UX
    setTimeout(() => {
        loadTasks();
        loadAnalytics();
        loadUserStats();
    }, 500);
}

function setTodayAsMinDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('deadline').setAttribute('min', today);
    document.getElementById('editDeadline').setAttribute('min', today);
}

function setupEventListeners() {
    // Modal close on outside click
    window.addEventListener('click', function(event) {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (event.target === modal) {
                closeModal();
            }
        });
    });
    
    // Form auto-save
    const taskForm = document.getElementById('taskForm');
    if (taskForm) {
        taskForm.addEventListener('input', saveFormData);
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        if (event.ctrlKey || event.metaKey) {
            switch(event.key) {
                case 'n':
                    event.preventDefault();
                    switchTab('add-task');
                    document.getElementById('taskTitle').focus();
                    break;
                case 'f':
                    event.preventDefault();
                    switchTab('search-tasks');
                    document.getElementById('searchQuery').focus();
                    break;
            }
        }
        if (event.key === 'Escape') {
            closeModal();
        }
    });
}

function setupPerformanceMonitoring() {
    // Monitor page load performance
    window.addEventListener('load', function() {
        const loadTime = Date.now() - lastLoadTime;
        console.log(`📊 Page loaded in ${loadTime}ms`);
    });
}

// ====================================
// DASHBOARD & STATS FUNCTIONS
// ====================================

async function loadDashboard() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (response.ok) {
            currentStats = data;
            updateStatsGrid(data);
        } else {
            showAlert('Error loading dashboard: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Dashboard load error:', error);
        showAlert('Network error loading dashboard: ' + error.message, 'error');
    }
}

function updateStatsGrid(stats) {
    const grid = document.getElementById('statsGrid');
    
    grid.innerHTML = `
        <div class="stat-card fade-in">
            <h3>📋 Total Tasks</h3>
            <div class="stat-value">${stats.total_tasks || 0}</div>
            <div class="stat-label">All time</div>
        </div>
        
        <div class="stat-card fade-in">
            <h3>⚡ Active Tasks</h3>
            <div class="stat-value">${stats.active_tasks || 0}</div>
            <div class="stat-label">In progress</div>
        </div>
        
        <div class="stat-card fade-in">
            <h3>✅ Completed</h3>
            <div class="stat-value">${stats.completed_tasks || 0}</div>
            <div class="stat-label">${stats.completion_rate || 0}% rate</div>
        </div>
        
        <div class="stat-card fade-in">
            <h3>🎯 Level</h3>
            <div class="stat-value">${stats.level || 1}</div>
            <div class="stat-label">${stats.xp || 0} XP</div>
        </div>
        
        <div class="stat-card fade-in">
            <h3>🔥 Streak</h3>
            <div class="stat-value">${stats.streak || 0}</div>
            <div class="stat-label">days</div>
        </div>
        
        <div class="stat-card fade-in">
            <h3>⏰ Total Time</h3>
            <div class="stat-value">${Math.round((stats.total_estimated_time || 0) / 60)}</div>
            <div class="stat-label">hours estimated</div>
        </div>
    `;
}

// ====================================
// TASK MANAGEMENT FUNCTIONS
// ====================================

async function addTask(event) {
    event.preventDefault();
    
    const formData = getTaskFormData();
    if (!validateTaskData(formData)) return;
    
    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Task added successfully! 🎉', 'success', 'taskAlert');
            resetTaskForm();
            refreshData();
            clearSavedForm();
        } else {
            showAlert('Error: ' + result.error, 'error', 'taskAlert');
        }
    } catch (error) {
        console.error('Add task error:', error);
        showAlert('Network error: ' + error.message, 'error', 'taskAlert');
    }
}

function getTaskFormData() {
    return {
        title: document.getElementById('taskTitle').value.trim(),
        estimated_time: parseInt(document.getElementById('estimatedTime').value),
        priority: parseInt(document.getElementById('priority').value),
        deadline: document.getElementById('deadline').value || null
    };
}

function validateTaskData(data) {
    if (!data.title) {
        showAlert('Task title is required!', 'error', 'taskAlert');
        return false;
    }
    if (data.estimated_time <= 0 || data.estimated_time > 1440) {
        showAlert('Please enter a valid time between 1-1440 minutes!', 'error', 'taskAlert');
        return false;
    }
    return true;
}

function resetTaskForm() {
    document.getElementById('taskForm').reset();
    document.getElementById('estimatedTime').value = 30;
    document.getElementById('priority').value = 2;
}

async function loadTasks() {
    try {
        const response = await fetch('/api/tasks');
        const data = await response.json();
        
        if (response.ok) {
            currentTasks = data.tasks || [];
            displayTasks(currentTasks);
        } else {
            showAlert('Error loading tasks: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Load tasks error:', error);
        showAlert('Network error loading tasks: ' + error.message, 'error');
    }
}

function displayTasks(tasks) {
    const container = document.getElementById('taskList');
    
    if (tasks.length === 0) {
        container.innerHTML = createEmptyState('No tasks found', 'Add your first task to get started!');
        return;
    }
    
    container.innerHTML = tasks.map(task => createTaskHTML(task)).join('');
}

function createTaskHTML(task) {
    const priorityIcons = {1: '🔴', 2: '🟡', 3: '🟢'};
    const priorityText = {1: 'High', 2: 'Medium', 3: 'Low'};
    
    const deadlineText = task.deadline ? 
        `<div class="task-deadline">📅 ${formatDate(task.deadline)}</div>` : '';
    
    const completedClass = task.completed ? 'completed' : '';
    const completedButton = task.completed ? 
        `<span class="completed-badge">✅ Completed</span>` :
        `<button class="btn btn-sm btn-success" onclick="openCompleteModal(${task.id})">✅ Complete</button>`;
    
    return `
        <div class="task-item ${completedClass}" data-task-id="${task.id}">
            <div class="task-header">
                <h4>${escapeHtml(task.title)}</h4>
                <div class="task-priority">
                    ${priorityIcons[task.priority]} ${priorityText[task.priority]}
                </div>
            </div>
            <div class="task-details">
                <div class="task-time">⏱️ ${task.estimated_time} min</div>
                ${deadlineText}
                <div class="task-created">Created ${formatDateTime(task.created_at)}</div>
            </div>
            <div class="task-actions">
                ${completedButton}
                <button class="btn btn-sm" onclick="editTask(${task.id})">✏️ Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">🗑️ Delete</button>
            </div>
        </div>
    `;
}

function createEmptyState(title, message) {
    return `
        <div class="empty-state">
            <div class="empty-icon">📝</div>
            <h3>${title}</h3>
            <p>${message}</p>
        </div>
    `;
}

async function updateTask(event) {
    event.preventDefault();
    
    const taskId = document.getElementById('editTaskId').value;
    const formData = {
        title: document.getElementById('editTaskTitle').value.trim(),
        estimated_time: parseInt(document.getElementById('editEstimatedTime').value),
        priority: parseInt(document.getElementById('editPriority').value),
        deadline: document.getElementById('editDeadline').value || null
    };
    
    if (!validateTaskData(formData)) return;
    
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Task updated successfully! ✨', 'success');
            closeModal();
            refreshData();
        } else {
            showAlert('Error: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Update task error:', error);
        showAlert('Network error: ' + error.message, 'error');
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('Task deleted successfully! 🗑️', 'success');
            refreshData();
        } else {
            showAlert('Error: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Delete task error:', error);
        showAlert('Network error: ' + error.message, 'error');
    }
}

async function completeTask(event) {
    event.preventDefault();
    
    const taskId = document.getElementById('completeTaskId').value;
    const actualTime = document.getElementById('actualTime').value;
    const focusSessions = parseInt(document.getElementById('focusSessions').value) || 1;
    
    const completionData = {
        actual_time: actualTime ? parseInt(actualTime) : null,
        focus_sessions: focusSessions
    };
    
    try {
        const response = await fetch(`/api/tasks/${taskId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(completionData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert(`Task completed! 🎉 ${result.xp_gained ? `+${result.xp_gained} XP` : ''}`, 'success');
            closeModal();
            refreshData();
        } else {
            showAlert('Error: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Complete task error:', error);
        showAlert('Network error: ' + error.message, 'error');
    }
}

// ====================================
// SEARCH & FILTER FUNCTIONS
// ====================================

async function searchTasks() {
    const query = document.getElementById('searchQuery').value.trim();
    const priority = document.getElementById('priorityFilter').value;
    const completed = document.getElementById('completedFilter').value;
    
    try {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (priority) params.append('priority', priority);
        if (completed) params.append('completed', completed);
        
        const response = await fetch(`/api/tasks/search?${params}`);
        const data = await response.json();
        
        if (response.ok) {
            displaySearchResults(data.tasks || []);
        } else {
            showAlert('Search error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Search error:', error);
        showAlert('Network error: ' + error.message, 'error');
    }
}

function displaySearchResults(tasks) {
    const container = document.getElementById('searchResults');
    
    if (tasks.length === 0) {
        container.innerHTML = createEmptyState('No tasks found', 'Try adjusting your search criteria');
        return;
    }
    
    container.innerHTML = tasks.map(task => createTaskHTML(task)).join('');
}

// ====================================
// SCHEDULING FUNCTIONS
// ====================================

async function generateSchedule() {
    const availableTime = parseInt(document.getElementById('availableTime').value);
    
    if (!availableTime || availableTime <= 0) {
        showAlert('Please enter a valid available time!', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ available_time: availableTime })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displaySchedule(data);
        } else {
            showAlert('Scheduling error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Schedule error:', error);
        showAlert('Network error: ' + error.message, 'error');
    }
}

function displaySchedule(scheduleData) {
    const container = document.getElementById('scheduleResults');
    
    if (!scheduleData.tasks || scheduleData.tasks.length === 0) {
        container.innerHTML = createEmptyState('No tasks to schedule', 'Add some tasks first!');
        return;
    }
    
    const totalTime = scheduleData.tasks.reduce((sum, task) => sum + task.estimated_time, 0);
    
    container.innerHTML = `
        <div class="schedule-summary">
            <h3>📅 Optimized Schedule</h3>
            <p><strong>Total time:</strong> ${totalTime} minutes (${Math.round(totalTime / 60 * 100) / 100} hours)</p>
            <p><strong>Tasks scheduled:</strong> ${scheduleData.tasks.length}</p>
        </div>
        <div class="schedule-list">
            ${scheduleData.tasks.map((task, index) => `
                <div class="schedule-item">
                    <div class="schedule-order">${index + 1}</div>
                    <div class="schedule-task">
                        <h4>${escapeHtml(task.title)}</h4>
                        <div class="schedule-details">
                            <span>⏱️ ${task.estimated_time} min</span>
                            <span>🎯 ${getPriorityText(task.priority)} priority</span>
                            ${task.deadline ? `<span>📅 Due ${formatDate(task.deadline)}</span>` : ''}
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// ====================================
// ANALYTICS FUNCTIONS
// ====================================

async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        const data = await response.json();
        
        if (response.ok) {
            displayAnalytics(data);
        } else {
            showAlert('Analytics error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Analytics error:', error);
        showAlert('Network error loading analytics: ' + error.message, 'error');
    }
}

function displayAnalytics(data) {
    const container = document.getElementById('analyticsOverview');
    
    container.innerHTML = `
        <div class="analytics-grid">
            <div class="analytics-card">
                <h4>📊 Task Distribution</h4>
                <div class="priority-breakdown">
                    <div class="priority-item">
                        <span>🔴 High:</span>
                        <span>${data.priority_breakdown?.high || 0} tasks</span>
                    </div>
                    <div class="priority-item">
                        <span>🟡 Medium:</span>
                        <span>${data.priority_breakdown?.medium || 0} tasks</span>
                    </div>
                    <div class="priority-item">
                        <span>🟢 Low:</span>
                        <span>${data.priority_breakdown?.low || 0} tasks</span>
                    </div>
                </div>
            </div>
            
            <div class="analytics-card">
                <h4>⏰ Time Analytics</h4>
                <div class="time-stats">
                    <div class="time-stat">
                        <span>Average task time:</span>
                        <span>${data.avg_task_time || 0} min</span>
                    </div>
                    <div class="time-stat">
                        <span>Total estimated:</span>
                        <span>${Math.round((data.total_estimated || 0) / 60 * 100) / 100} hours</span>
                    </div>
                    <div class="time-stat">
                        <span>Total actual:</span>
                        <span>${Math.round((data.total_actual || 0) / 60 * 100) / 100} hours</span>
                    </div>
                </div>
            </div>
            
            <div class="analytics-card">
                <h4>📈 Productivity Trends</h4>
                <div class="trend-stats">
                    <div class="trend-stat">
                        <span>Tasks this week:</span>
                        <span>${data.tasks_this_week || 0}</span>
                    </div>
                    <div class="trend-stat">
                        <span>Completion rate:</span>
                        <span>${data.completion_rate || 0}%</span>
                    </div>
                    <div class="trend-stat">
                        <span>Focus sessions:</span>
                        <span>${data.total_focus_sessions || 0}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function loadUserStats() {
    try {
        const response = await fetch('/api/user/stats');
        const data = await response.json();
        
        if (response.ok) {
            displayUserStats(data);
        } else {
            // If API endpoint doesn't exist, show calculated user stats
            displayUserStatsFallback();
        }
    } catch (error) {
        console.error('User stats error:', error);
        // Show fallback data instead of just error message
        displayUserStatsFallback();
    }
}

function displayUserStatsFallback() {
    // Calculate user stats from current tasks and stats
    const completedTasks = currentTasks.filter(task => task.completed);
    const totalTasks = currentTasks.length;
    const completionRate = totalTasks > 0 ? Math.round((completedTasks.length / totalTasks) * 100) : 0;
    
    // Calculate XP based on completed tasks
    const baseXPPerTask = 10;
    const bonusXPForHighPriority = 5;
    
    let totalXP = 0;
    completedTasks.forEach(task => {
        totalXP += baseXPPerTask;
        if (task.priority === 1) totalXP += bonusXPForHighPriority; // High priority bonus
    });
    
    // Calculate level (every 100 XP = 1 level)
    const level = Math.floor(totalXP / 100) + 1;
    const currentXP = totalXP % 100;
    const xpToNext = 100;
    
    // Calculate streak (mock data - would need date tracking in real app)
    const streak = Math.min(completedTasks.length, 7); // Max 7 day streak for demo
    
    // Generate achievements based on performance
    const achievements = generateAchievements(completedTasks, totalTasks, completionRate);
    
    const userStatsData = {
        level: level,
        current_xp: currentXP,
        total_xp: totalXP,
        xp_to_next: xpToNext,
        completed_tasks: completedTasks.length,
        best_streak: streak,
        current_streak: streak,
        achievements: achievements
    };
    
    displayUserStats(userStatsData);
}

function generateAchievements(completedTasks, totalTasks, completionRate) {
    const achievements = [];
    
    // First task achievement
    if (completedTasks.length >= 1) {
        achievements.push({
            icon: '🎯',
            name: 'First Step',
            description: 'Completed your first task!'
        });
    }
    
    // Task quantity achievements
    if (completedTasks.length >= 5) {
        achievements.push({
            icon: '🚀',
            name: 'Getting Started',
            description: 'Completed 5 tasks'
        });
    }
    
    if (completedTasks.length >= 10) {
        achievements.push({
            icon: '💪',
            name: 'Task Warrior',
            description: 'Completed 10 tasks'
        });
    }
    
    if (completedTasks.length >= 25) {
        achievements.push({
            icon: '🏆',
            name: 'Productivity Master',
            description: 'Completed 25 tasks'
        });
    }
    
    // Completion rate achievements
    if (completionRate >= 80 && totalTasks >= 5) {
        achievements.push({
            icon: '⭐',
            name: 'High Achiever',
            description: '80%+ completion rate'
        });
    }
    
    if (completionRate >= 90 && totalTasks >= 10) {
        achievements.push({
            icon: '🌟',
            name: 'Perfectionist',
            description: '90%+ completion rate'
        });
    }
    
    // Priority-based achievements
    const highPriorityCompleted = completedTasks.filter(task => task.priority === 1);
    if (highPriorityCompleted.length >= 3) {
        achievements.push({
            icon: '🔥',
            name: 'Priority Focus',
            description: 'Completed 3+ high priority tasks'
        });
    }
    
    // If no achievements yet, add encouragement
    if (achievements.length === 0) {
        achievements.push({
            icon: '🌱',
            name: 'Getting Started',
            description: 'Welcome to TaskFlow! Complete your first task to earn more achievements.'
        });
    }
    
    return achievements;
}

function displayUserStats(data) {
    const container = document.getElementById('userStatsContent');
    
    const progressPercentage = ((data.current_xp || 0) / (data.xp_to_next || 100)) * 100;
    
    container.innerHTML = `
        <div class="user-stats-grid">
            <div class="stat-card">
                <h4>🎯 Level & Experience</h4>
                <div class="level-info">
                    <div class="level-display">
                        <span class="level-number">Level ${data.level || 1}</span>
                        <span class="total-xp">${data.total_xp || 0} Total XP</span>
                    </div>
                    <div class="xp-progress">
                        <div class="xp-text">${data.current_xp || 0} / ${data.xp_to_next || 100} XP</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progressPercentage}%"></div>
                        </div>
                        <div class="xp-needed">${(data.xp_to_next || 100) - (data.current_xp || 0)} XP to next level</div>
                    </div>
                </div>
            </div>
            
            <div class="stat-card">
                <h4>📊 Performance Stats</h4>
                <div class="performance-stats">
                    <div class="perf-stat">
                        <span class="perf-icon">✅</span>
                        <div class="perf-details">
                            <div class="perf-value">${data.completed_tasks || 0}</div>
                            <div class="perf-label">Tasks Completed</div>
                        </div>
                    </div>
                    <div class="perf-stat">
                        <span class="perf-icon">🔥</span>
                        <div class="perf-details">
                            <div class="perf-value">${data.current_streak || 0}</div>
                            <div class="perf-label">Current Streak</div>
                        </div>
                    </div>
                    <div class="perf-stat">
                        <span class="perf-icon">🏆</span>
                        <div class="perf-details">
                            <div class="perf-value">${data.best_streak || 0}</div>
                            <div class="perf-label">Best Streak</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="stat-card">
                <h4>🏅 Achievements</h4>
                <div class="achievements">
                    ${data.achievements && data.achievements.length > 0 ? 
                        data.achievements.map(achievement => `
                            <div class="achievement" title="${achievement.description || ''}">
                                <span class="achievement-icon">${achievement.icon}</span>
                                <div class="achievement-details">
                                    <div class="achievement-name">${achievement.name}</div>
                                    <div class="achievement-desc">${achievement.description || ''}</div>
                                </div>
                            </div>
                        `).join('') : 
                        '<div class="no-achievements">🌟 Complete tasks to earn achievements!</div>'
                    }
                </div>
            </div>
            
            <div class="stat-card">
                <h4>🎮 Level System</h4>
                <div class="level-system-info">
                    <div class="level-explanation">
                        <div class="level-rule">📝 Complete task: <strong>+10 XP</strong></div>
                        <div class="level-rule">🔴 High priority: <strong>+5 bonus XP</strong></div>
                        <div class="level-rule">📈 Level up every: <strong>100 XP</strong></div>
                    </div>
                    <div class="next-milestone">
                        ${getNextMilestone(data.completed_tasks || 0)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getNextMilestone(completedTasks) {
    const milestones = [
        { tasks: 1, name: "First Step", icon: "🎯" },
        { tasks: 5, name: "Getting Started", icon: "🚀" },
        { tasks: 10, name: "Task Warrior", icon: "💪" },
        { tasks: 25, name: "Productivity Master", icon: "🏆" },
        { tasks: 50, name: "Task Legend", icon: "⭐" },
        { tasks: 100, name: "Productivity Guru", icon: "🌟" }
    ];
    
    const nextMilestone = milestones.find(m => m.tasks > completedTasks);
    
    if (nextMilestone) {
        const remaining = nextMilestone.tasks - completedTasks;
        return `
            <div class="milestone-progress">
                <div class="milestone-icon">${nextMilestone.icon}</div>
                <div class="milestone-text">
                    <div class="milestone-name">Next: ${nextMilestone.name}</div>
                    <div class="milestone-remaining">${remaining} more task${remaining > 1 ? 's' : ''} to go!</div>
                </div>
            </div>
        `;
    } else {
        return `
            <div class="milestone-progress">
                <div class="milestone-icon">👑</div>
                <div class="milestone-text">
                    <div class="milestone-name">Maximum Level Achieved!</div>
                    <div class="milestone-remaining">You're a TaskFlow legend!</div>
                </div>
            </div>
        `;
    }
}

// ====================================
// TAB & MODAL FUNCTIONS
// ====================================

function switchTab(tabName) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to clicked tab and corresponding content
    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    // Auto-focus on relevant input
    setTimeout(() => {
        if (tabName === 'add-task') {
            document.getElementById('taskTitle').focus();
        } else if (tabName === 'search-tasks') {
            document.getElementById('searchQuery').focus();
        }
    }, 100);
}

function switchAnalyticsTab(tabName) {
    // Remove active class from all analytics tabs and content
    document.querySelectorAll('#overview, #user-stats, #productivity').forEach(content => 
        content.classList.remove('active'));
    document.querySelectorAll('.panel:last-of-type .tab').forEach(tab => 
        tab.classList.remove('active'));
    
    // Add active class to clicked tab and corresponding content
    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    // Load data for specific tabs if needed
    if (tabName === 'productivity' && !document.getElementById('productivityContent').innerHTML.includes('productivity-chart')) {
        loadProductivityData();
    }
}

function editTask(taskId) {
    const task = currentTasks.find(t => t.id === taskId);
    if (!task) return;
    
    document.getElementById('editTaskId').value = task.id;
    document.getElementById('editTaskTitle').value = task.title;
    document.getElementById('editEstimatedTime').value = task.estimated_time;
    document.getElementById('editPriority').value = task.priority;
    document.getElementById('editDeadline').value = task.deadline || '';
    
    document.getElementById('taskModal').style.display = 'block';
    setTimeout(() => document.getElementById('editTaskTitle').focus(), 100);
}

function openCompleteModal(taskId) {
    const task = currentTasks.find(t => t.id === taskId);
    if (!task) return;
    
    document.getElementById('completeTaskId').value = task.id;
    document.getElementById('completeTaskInfo').innerHTML = `
        <div class="complete-task-info">
            <h3>${escapeHtml(task.title)}</h3>
            <p>Estimated time: ${task.estimated_time} minutes</p>
        </div>
    `;
    
    document.getElementById('completeModal').style.display = 'block';
    setTimeout(() => {
        const actualTimeInput = document.getElementById('actualTime');
        actualTimeInput.value = task.estimated_time;
        actualTimeInput.focus();
    }, 100);
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

// ====================================
// UTILITY FUNCTIONS
// ====================================

async function exportData() {
    try {
        const response = await fetch('/api/export');
        const data = await response.json();
        
        if (response.ok) {
            const blob = new Blob([JSON.stringify(data, null, 2)], 
                { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `taskflow-export-${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
            
            showAlert('Data exported successfully! 📥', 'success');
        } else {
            showAlert('Export error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Export error:', error);
        showAlert('Network error: ' + error.message, 'error');
    }
}

function confirmReset() {
    if (confirm('⚠️ This will delete ALL your tasks and data! Are you absolutely sure?')) {
        if (confirm('This action cannot be undone. Proceed with reset?')) {
            resetAllData();
        }
    }
}

async function resetAllData() {
    try {
        const response = await fetch('/api/reset', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            showAlert('All data has been reset! 🔄', 'success');
            refreshData();
            clearSavedForm();
        } else {
            showAlert('Reset error: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Reset error:', error);
        showAlert('Network error: ' + error.message, 'error');
    }
}

async function testModels() {
    const container = document.getElementById('utilityResults');
    container.innerHTML = '<div class="loading">Testing models...</div>';
    
    try {
        const response = await fetch('/api/test');
        const data = await response.json();
        
        if (response.ok) {
            container.innerHTML = `
                <div class="test-results">
                    <h4>🧪 Model Test Results</h4>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                </div>
            `;
        } else {
            container.innerHTML = `<p>Test error: ${data.error}</p>`;
        }
    } catch (error) {
        console.error('Test error:', error);
        container.innerHTML = `<p>Network error: ${error.message}</p>`;
    }
}

async function loadProductivityData() {
    try {
        const response = await fetch('/api/productivity');
        const data = await response.json();
        
        if (response.ok) {
            displayProductivityData(data);
        } else {
            // If API endpoint doesn't exist, show calculated productivity data
            displayProductivityDataFallback();
        }
    } catch (error) {
        console.error('Productivity data error:', error);
        // Show fallback data instead of just error message
        displayProductivityDataFallback();
    }
}

function displayProductivityDataFallback() {
    // Calculate basic productivity stats from current tasks
    const completedTasks = currentTasks.filter(task => task.completed);
    const activeTasks = currentTasks.filter(task => !task.completed);
    
    const totalEstimatedTime = currentTasks.reduce((sum, task) => sum + (task.estimated_time || 0), 0);
    const completedEstimatedTime = completedTasks.reduce((sum, task) => sum + (task.estimated_time || 0), 0);
    
    const completionRate = currentTasks.length > 0 ? Math.round((completedTasks.length / currentTasks.length) * 100) : 0;
    const avgTaskTime = currentTasks.length > 0 ? Math.round(totalEstimatedTime / currentTasks.length) : 0;
    
    // Calculate most productive day (mock data for now)
    const today = new Date();
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const mostProductiveDay = days[today.getDay()];
    
    const productivityData = {
        most_productive_day: mostProductiveDay,
        avg_daily_tasks: Math.round(currentTasks.length / 7), // Assuming tasks are from this week
        time_accuracy: 85, // Mock accuracy percentage
        completion_rate: completionRate,
        total_focus_time: Math.round(completedEstimatedTime / 60), // in hours
        weekly_trend: '+15%' // Mock trend
    };
    
    displayProductivityData(productivityData);
}

function displayProductivityData(data) {
    const container = document.getElementById('productivityContent');
    
    container.innerHTML = `
        <div class="productivity-overview">
            <h4>📈 Productivity Insights</h4>
            <div class="productivity-stats">
                <div class="productivity-stat">
                    <span>Most productive day:</span>
                    <span>${data.most_productive_day || 'N/A'}</span>
                </div>
                <div class="productivity-stat">
                    <span>Average daily tasks:</span>
                    <span>${data.avg_daily_tasks || 0}</span>
                </div>
                <div class="productivity-stat">
                    <span>Time accuracy:</span>
                    <span>${data.time_accuracy || 0}%</span>
                </div>
                <div class="productivity-stat">
                    <span>Completion rate:</span>
                    <span>${data.completion_rate || 0}%</span>
                </div>
                <div class="productivity-stat">
                    <span>Total focus time:</span>
                    <span>${data.total_focus_time || 0} hours</span>
                </div>
                <div class="productivity-stat">
                    <span>Weekly trend:</span>
                    <span>${data.weekly_trend || 'N/A'}</span>
                </div>
            </div>
            
            <div class="productivity-insights">
                <h5>💡 Productivity Tips</h5>
                <div class="insight-list">
                    <div class="insight-item">
                        ${getProductivityTip(data)}
                    </div>
                </div>
            </div>
            
            <div class="productivity-chart">
                <h5>📊 Task Distribution</h5>
                <div class="chart-container">
                    ${createSimpleChart(data)}
                </div>
            </div>
        </div>
    `;
}

function getProductivityTip(data) {
    const completionRate = data.completion_rate || 0;
    
    if (completionRate >= 80) {
        return "🎉 Excellent work! You're maintaining a high completion rate. Keep up the momentum!";
    } else if (completionRate >= 60) {
        return "👍 Good progress! Try breaking larger tasks into smaller, manageable chunks to boost your completion rate.";
    } else if (completionRate >= 40) {
        return "💪 You're making progress! Focus on completing 2-3 high-priority tasks each day to build consistency.";
    } else {
        return "🚀 Every expert was once a beginner! Start with small, achievable tasks to build your productivity habits.";
    }
}

function createSimpleChart(data) {
    const completionRate = data.completion_rate || 0;
    const pendingRate = 100 - completionRate;
    
    return `
        <div class="simple-chart">
            <div class="chart-bar">
                <div class="chart-segment completed" style="width: ${completionRate}%">
                    <span>Completed: ${completionRate}%</span>
                </div>
                <div class="chart-segment pending" style="width: ${pendingRate}%">
                    <span>Pending: ${pendingRate}%</span>
                </div>
            </div>
        </div>
    `;
}

// ====================================
// FORM PERSISTENCE FUNCTIONS
// ====================================

function saveFormData() {
    const formData = {
        title: document.getElementById('taskTitle').value,
        estimatedTime: document.getElementById('estimatedTime').value,
        priority: document.getElementById('priority').value,
        deadline: document.getElementById('deadline').value
    };
    
    // Use in-memory storage instead of localStorage
    window.tempFormData = formData;
}

function loadSavedForm() {
    if (window.tempFormData) {
        const data = window.tempFormData;
        document.getElementById('taskTitle').value = data.title || '';
        document.getElementById('estimatedTime').value = data.estimatedTime || 30;
        document.getElementById('priority').value = data.priority || 2;
        document.getElementById('deadline').value = data.deadline || '';
    }
}

function clearSavedForm() {
    delete window.tempFormData;
}

// ====================================
// HELPER FUNCTIONS
// ====================================

function showAlert(message, type = 'info', containerId = null) {
    const alertClass = type === 'error' ? 'alert-error' : 
                      type === 'success' ? 'alert-success' : 'alert-info';
    
    let container;
    if (containerId) {
        container = document.getElementById(containerId);
    } else {
        // Create a global alert container if it doesn't exist
        container = document.getElementById('globalAlert');
        if (!container) {
            container = document.createElement('div');
            container.id = 'globalAlert';
            container.className = 'alert';
            document.querySelector('.container').prepend(container);
        }
    }
    
    container.className = `alert ${alertClass}`;
    container.innerHTML = message;
    container.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        container.style.display = 'none';
    }, 5000);
}

function refreshData() {
    loadDashboard();
    loadTasks();
    loadAnalytics();
    loadUserStats();
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatDateTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffTime / (1000 * 60));
    
    if (diffDays > 7) {
        return date.toLocaleDateString();
    } else if (diffDays > 0) {
        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
        return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else if (diffMinutes > 0) {
        return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
    } else {
        return 'Just now';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getPriorityText(priority) {
    const priorityMap = {1: 'High', 2: 'Medium', 3: 'Low'};
    return priorityMap[priority] || 'Medium';
}

function getPriorityIcon(priority) {
    const iconMap = {1: '🔴', 2: '🟡', 3: '🟢'};
    return iconMap[priority] || '🟡';
}

// ====================================
// ADVANCED FEATURES
// ====================================

function initializeNotifications() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

function showNotification(title, body, icon = '📋') {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: body,
            icon: '/static/images/favicon.ico',
            tag: 'taskflow'
        });
    }
}

function checkDeadlines() {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    currentTasks.forEach(task => {
        if (task.deadline && !task.completed) {
            const deadline = new Date(task.deadline);
            if (deadline.toDateString() === today.toDateString()) {
                showNotification(
                    'Task Due Today! 🚨',
                    `"${task.title}" is due today`
                );
            } else if (deadline.toDateString() === tomorrow.toDateString()) {
                showNotification(
                    'Task Due Tomorrow 📅',
                    `"${task.title}" is due tomorrow`
                );
            }
        }
    });
}

function initializeKeyboardShortcuts() {
    const shortcuts = {
        'Ctrl+N': () => {
            switchTab('add-task');
            document.getElementById('taskTitle').focus();
        },
        'Ctrl+F': () => {
            switchTab('search-tasks');
            document.getElementById('searchQuery').focus();
        },
        'Ctrl+S': () => {
            generateSchedule();
        },
        'Ctrl+R': () => {
            refreshData();
        }
    };
    
    document.addEventListener('keydown', (e) => {
        const key = (e.ctrlKey ? 'Ctrl+' : '') + 
                   (e.shiftKey ? 'Shift+' : '') + 
                   (e.altKey ? 'Alt+' : '') + 
                   e.key;
        
        if (shortcuts[key]) {
            e.preventDefault();
            shortcuts[key]();
        }
    });
}

function initializeAutoSave() {
    let autoSaveTimeout;
    
    const autoSaveElements = ['taskTitle', 'estimatedTime', 'priority', 'deadline'];
    autoSaveElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', () => {
                clearTimeout(autoSaveTimeout);
                autoSaveTimeout = setTimeout(saveFormData, 1000);
            });
        }
    });
}

function initializeDragAndDrop() {
    let draggedElement = null;
    
    document.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('task-item')) {
            draggedElement = e.target;
            e.target.style.opacity = '0.5';
        }
    });
    
    document.addEventListener('dragend', (e) => {
        if (e.target.classList.contains('task-item')) {
            e.target.style.opacity = '1';
        }
    });
    
    document.addEventListener('dragover', (e) => {
        e.preventDefault();
    });
    
    document.addEventListener('drop', (e) => {
        e.preventDefault();
        if (draggedElement && e.target.classList.contains('task-item')) {
            const container = e.target.parentNode;
            const afterElement = getDragAfterElement(container, e.clientY);
            if (afterElement == null) {
                container.appendChild(draggedElement);
            } else {
                container.insertBefore(draggedElement, afterElement);
            }
        }
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.task-item:not(.dragging)')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// ====================================
// THEME & UI ENHANCEMENTS
// ====================================

function initializeTheme() {
    const savedTheme = window.tempTheme || 'light';
    document.body.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.body.setAttribute('data-theme', newTheme);
    window.tempTheme = newTheme;
    
    showAlert(`Switched to ${newTheme} theme! 🎨`, 'success');
}

function animateStats() {
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach((element, index) => {
        const finalValue = parseInt(element.textContent) || 0;
        element.textContent = '0';
        
        const duration = 1000;
        const startTime = performance.now() + (index * 100);
        
        function animate(currentTime) {
            if (currentTime >= startTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const currentValue = Math.floor(finalValue * progress);
                element.textContent = currentValue;
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            } else {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    });
}

function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = event.target.getAttribute('data-tooltip');
    
    document.body.appendChild(tooltip);
    
    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    
    event.target.tooltipElement = tooltip;
}

function hideTooltip(event) {
    if (event.target.tooltipElement) {
        document.body.removeChild(event.target.tooltipElement);
        event.target.tooltipElement = null;
    }
}

// ====================================
// SEARCH ENHANCEMENTS
// ====================================

function initializeSmartSearch() {
    const searchInput = document.getElementById('searchQuery');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSmartSearch(e.target.value);
            }, 300);
        });
    }
}

function performSmartSearch(query) {
    if (!query.trim()) {
        document.getElementById('searchResults').innerHTML = '';
        return;
    }
    
    const results = currentTasks.filter(task => {
        const searchTerm = query.toLowerCase();
        return task.title.toLowerCase().includes(searchTerm) ||
               getPriorityText(task.priority).toLowerCase().includes(searchTerm) ||
               (task.deadline && task.deadline.includes(searchTerm));
    });
    
    displaySearchResults(results);
}

function highlightSearchTerms(text, query) {
    if (!query) return escapeHtml(text);
    
    const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
    return escapeHtml(text).replace(regex, '<mark>$1</mark>');
}

function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\function showAlert(message,');
}

// ====================================
// PERFORMANCE OPTIMIZATIONS
// ====================================

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// ====================================
// ERROR HANDLING & LOGGING
// ====================================

function setupErrorHandling() {
    window.addEventListener('error', (event) => {
        console.error('Global error:', event.error);
        showAlert('An unexpected error occurred. Please refresh the page.', 'error');
    });
    
    window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection:', event.reason);
        showAlert('A network error occurred. Please check your connection.', 'error');
    });
}

function logUserAction(action, details = {}) {
    const logEntry = {
        timestamp: new Date().toISOString(),
        action: action,
        details: details,
        userAgent: navigator.userAgent
    };
    
    console.log('User Action:', logEntry);
    
    // Store in memory for potential debugging
    if (!window.actionLog) window.actionLog = [];
    window.actionLog.push(logEntry);
    
    // Keep only last 100 entries
    if (window.actionLog.length > 100) {
        window.actionLog = window.actionLog.slice(-100);
    }
}

// ====================================
// INITIALIZATION COMPLETION
// ====================================

function completeInitialization() {
    initializeNotifications();
    initializeKeyboardShortcuts();
    initializeAutoSave();
    initializeDragAndDrop();
    initializeTheme();
    initializeTooltips();
    initializeSmartSearch();
    setupErrorHandling();
    
    // Set up periodic tasks
    setInterval(checkDeadlines, 60000); // Check every minute
    setInterval(refreshData, 300000);   // Refresh every 5 minutes
    
    // Log completion
    logUserAction('app_initialized');
    console.log('🎉 TaskFlow fully initialized with all features!');
}

// Enhanced setup function
function setupEventListeners() {
    // Modal close on outside click
    window.addEventListener('click', function(event) {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (event.target === modal) {
                closeModal();
            }
        });
    });
    
    // Form auto-save
    const taskForm = document.getElementById('taskForm');
    if (taskForm) {
        taskForm.addEventListener('input', debounce(saveFormData, 1000));
    }
    
    // Search with debouncing
    const searchInput = document.getElementById('searchQuery');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(searchTasks, 300));
    }
    
    // Complete initialization after DOM is ready
    setTimeout(completeInitialization, 1000);
}

// ====================================
// EXPORT FUNCTIONS FOR GLOBAL ACCESS
// ====================================

// Make key functions available globally for HTML onclick handlers
window.TaskFlow = {
    switchTab,
    switchAnalyticsTab,
    editTask,
    deleteTask,
    openCompleteModal,
    closeModal,
    addTask,
    updateTask,
    completeTask,
    searchTasks,
    generateSchedule,
    exportData,
    confirmReset,
    testModels,
    loadDashboard,
    refreshData,
    toggleTheme
};

// Assign individual functions to window for backward compatibility
Object.assign(window, window.TaskFlow);
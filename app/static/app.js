// TaskFlow - Smart Task Management
// Frontend JavaScript

class TaskFlow {
    constructor() {
        this.tasks = [];
        this.stats = {};
        this.schedule = [];
        this.focusTimer = null;
        this.currentTask = null;
        this.priorityChart = null;
        
        this.init();
    }

    init() {
        console.log('TaskFlow initialized!');
        this.bindEvents();
        this.loadInitialData();
        this.initChart();
    }

    bindEvents() {
        // Task form submission
        document.getElementById('task-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addTask();
        });

        // Schedule form submission
        document.getElementById('schedule-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.generateSchedule();
        });

        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('focus-modal')) {
                this.closeFocusModal();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeFocusModal();
            }
        });
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadTasks(),
                this.loadStats(),
                this.loadCurrentSchedule()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Failed to load data', 'error');
        }
    }

    async loadTasks() {
        try {
            const response = await fetch('/tasks');
            if (!response.ok) throw new Error('Failed to fetch tasks');
            
            this.tasks = await response.json();
            this.renderTasks();
            this.updatePriorityChart();
        } catch (error) {
            console.error('Error loading tasks:', error);
            this.showNotification('Failed to load tasks', 'error');
        }
    }

    async loadStats() {
        try {
            const response = await fetch('/stats');
            if (!response.ok) throw new Error('Failed to fetch stats');
            
            this.stats = await response.json();
            this.renderStats();
        } catch (error) {
            console.error('Error loading stats:', error);
            this.showNotification('Failed to load statistics', 'error');
        }
    }

    async loadCurrentSchedule() {
        try {
            const response = await fetch('/current_schedule');
            if (!response.ok) throw new Error('Failed to fetch schedule');
            
            const data = await response.json();
            this.schedule = data.schedule || [];
            this.renderSchedule();
        } catch (error) {
            console.error('Error loading schedule:', error);
            this.renderSchedule([]); // Show empty schedule on error
        }
    }

    async addTask() {
        const form = document.getElementById('task-form');
        const formData = new FormData(form);
        
        const taskData = {
            title: formData.get('title') || document.getElementById('title').value,
            estimated_time: parseInt(document.getElementById('estimated_time').value),
            priority: parseInt(document.getElementById('priority').value),
            deadline: document.getElementById('deadline').value || null
        };

        // Basic validation
        if (!taskData.title.trim()) {
            this.showNotification('Please enter a task title', 'error');
            return;
        }

        if (taskData.estimated_time < 5 || taskData.estimated_time > 480) {
            this.showNotification('Duration must be between 5 and 480 minutes', 'error');
            return;
        }

        try {
            const response = await fetch('/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(taskData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to add task');
            }

            this.showNotification('Task added successfully!', 'success');
            form.reset();
            
            // Reload data
            await this.loadTasks();
            await this.loadStats();
            
        } catch (error) {
            console.error('Error adding task:', error);
            this.showNotification(error.message, 'error');
        }
    }

    async deleteTask(taskId) {
        if (!confirm('Are you sure you want to delete this task?')) {
            return;
        }

        try {
            const response = await fetch(`/tasks/${taskId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to delete task');
            }

            this.showNotification('Task deleted successfully!', 'success');
            
            // Reload data
            await this.loadTasks();
            await this.loadStats();
            await this.loadCurrentSchedule();
            
        } catch (error) {
            console.error('Error deleting task:', error);
            this.showNotification(error.message, 'error');
        }
    }

    async generateSchedule() {
        const availableTime = parseInt(document.getElementById('available_time').value);

        if (availableTime < 15 || availableTime > 480) {
            this.showNotification('Available time must be between 15 and 480 minutes', 'error');
            return;
        }

        try {
            const response = await fetch('/generate_schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    available_time: availableTime
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to generate schedule');
            }

            this.schedule = result.schedule || [];
            this.renderSchedule();
            this.showNotification(`Schedule generated with ${result.total_tasks} tasks!`, 'success');
            
        } catch (error) {
            console.error('Error generating schedule:', error);
            this.showNotification(error.message, 'error');
        }
    }

    renderTasks() {
        const container = document.getElementById('task-list');
        
        if (!this.tasks || this.tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <h3>No tasks yet</h3>
                    <p>Add your first task to get started with productivity!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.tasks.map(task => `
            <div class="task-card animated-card">
                <div class="task-header">
                    <div>
                        <h3 class="task-title">${this.escapeHtml(task.title)}</h3>
                        <div class="task-info">
                            <div class="task-detail">
                                <span class="task-icon">⏱️</span>
                                <span>${task.estimated_time} min</span>
                            </div>
                            ${task.deadline ? `
                                <div class="task-detail">
                                    <span class="task-icon">📅</span>
                                    <span>${this.formatDate(task.deadline)}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    <span class="task-priority priority-${this.getPriorityClass(task.priority)}">
                        ${this.getPriorityText(task.priority)}
                    </span>
                </div>
                <div class="task-actions">
                    <button class="btn btn-success btn-sm" onclick="taskFlow.startFocus(${task.id}, '${this.escapeHtml(task.title)}', ${task.estimated_time})">
                        <span class="btn-icon">🎯</span>
                        Focus
                    </button>
                    <button class="btn btn-warning btn-sm" onclick="taskFlow.rescheduleTask('${this.escapeHtml(task.title)}')">
                        <span class="btn-icon">📅</span>
                        Reschedule
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="taskFlow.deleteTask(${task.id})">
                        <span class="btn-icon">🗑️</span>
                        Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    renderStats() {
        if (!this.stats) return;

        document.getElementById('total-tasks').textContent = this.stats.total_tasks || 0;
        document.getElementById('xp').textContent = this.stats.xp || 0;
        document.getElementById('streak').textContent = this.stats.streak || 0;

        // Update XP progress bar
        const xpBar = document.getElementById('xp-bar');
        const currentLevelXP = (this.stats.xp || 0) % 100;
        xpBar.value = currentLevelXP;
        xpBar.max = 100;
    }

    renderSchedule() {
        const container = document.getElementById('schedule');
        
        if (!this.schedule || this.schedule.length === 0) {
            container.innerHTML = `
                <div class="schedule-empty">
                    <div class="empty-icon">📅</div>
                    <h3>No schedule yet</h3>
                    <p>Generate a schedule to optimize your time!</p>
                </div>
            `;
            return;
        }

        const totalTime = this.schedule.reduce((sum, task) => sum + (task.allocated_time || task.estimated_time || 0), 0);
        
        container.innerHTML = `
            <div class="schedule-header">
                <h3 class="card-title">Today's Schedule</h3>
                <div class="schedule-summary">
                    <span>${this.schedule.length} tasks</span>
                    <span>${totalTime} min total</span>
                </div>
            </div>
            <div class="schedule-list">
                ${this.schedule.map((task, index) => `
                    <div class="schedule-item">
                        <div>
                            <div class="schedule-task-title">${this.escapeHtml(task.title)}</div>
                            <div class="schedule-task-time">
                                <span class="time-icon">⏱️</span>
                                <span>${task.allocated_time || task.estimated_time} minutes</span>
                                <span class="task-priority priority-${this.getPriorityClass(task.priority)}">
                                    ${this.getPriorityText(task.priority)}
                                </span>
                            </div>
                        </div>
                        <div class="schedule-actions">
                            <button class="btn btn-success btn-sm" onclick="taskFlow.startFocus(${task.id}, '${this.escapeHtml(task.title)}', ${task.allocated_time || task.estimated_time})">
                                <span class="btn-icon">🎯</span>
                                Start
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async rescheduleTask(taskTitle) {
        try {
            const response = await fetch(`/reschedule_task/${encodeURIComponent(taskTitle)}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to reschedule task');
            }

            this.showNotification('Task rescheduled successfully!', 'success');
            
            // Reload data
            await this.loadTasks();
            await this.loadCurrentSchedule();
            
        } catch (error) {
            console.error('Error rescheduling task:', error);
            this.showNotification(error.message, 'error');
        }
    }

    startFocus(taskId, taskTitle, duration) {
        this.currentTask = { id: taskId, title: taskTitle, duration: duration };
        this.showFocusModal();
    }

    showFocusModal() {
        const modal = document.getElementById('focus-modal');
        const duration = this.currentTask.duration;
        
        modal.innerHTML = `
            <div class="focus-modal-content">
                <div class="focus-header">
                    <h2>Focus Session</h2>
                    <button class="close-btn" onclick="taskFlow.closeFocusModal()">×</button>
                </div>
                <h3>${this.escapeHtml(this.currentTask.title)}</h3>
                <div class="focus-timer">
                    <div class="countdown-display" id="countdown">${this.formatTime(duration * 60)}</div>
                    <div class="focus-controls">
                        <button class="btn btn-success" id="start-timer">Start Focus</button>
                        <button class="btn btn-warning" id="pause-timer" style="display: none;">Pause</button>
                        <button class="btn btn-danger" onclick="taskFlow.closeFocusModal()">Cancel</button>
                    </div>
                </div>
                <div class="feedback-buttons" id="completion-feedback" style="display: none;">
                    <h3>How did it go?</h3>
                    <button class="btn btn-success" onclick="taskFlow.completeTask(true)">✅ Completed Successfully</button>
                    <button class="btn btn-warning" onclick="taskFlow.completeTask(false)">⏸️ Need More Time</button>
                    <button class="btn btn-secondary" onclick="taskFlow.closeFocusModal()">Cancel</button>
                </div>
            </div>
        `;

        modal.classList.remove('hidden');
        
        // Bind timer controls
        document.getElementById('start-timer').addEventListener('click', () => {
            this.startTimer(duration * 60);
        });
    }

    startTimer(seconds) {
        const countdownEl = document.getElementById('countdown');
        const startBtn = document.getElementById('start-timer');
        const pauseBtn = document.getElementById('pause-timer');
        
        let timeLeft = seconds;
        let isPaused = false;
        
        startBtn.style.display = 'none';
        pauseBtn.style.display = 'inline-flex';
        
        pauseBtn.addEventListener('click', () => {
            isPaused = !isPaused;
            pauseBtn.textContent = isPaused ? 'Resume' : 'Pause';
        });

        this.focusTimer = setInterval(() => {
            if (!isPaused) {
                timeLeft--;
                countdownEl.textContent = this.formatTime(timeLeft);
                
                if (timeLeft <= 0) {
                    clearInterval(this.focusTimer);
                    this.showCompletionFeedback();
                }
            }
        }, 1000);
    }

    showCompletionFeedback() {
        document.querySelector('.focus-timer').style.display = 'none';
        document.getElementById('completion-feedback').style.display = 'block';
        
        // Play notification sound (if supported)
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmAcBj2a3PDBciMFLIHO8tiINgcZZ7zp46hbGAg9j9nxy2waASKG2+FnN1sNV7Pt6rFtGgkqd9fq01sDKHTN8NSGOS4EJ3bP6+iOO');
            audio.play();
        } catch (e) {
            // Ignore audio errors
        }
        
        this.showNotification('Focus session completed! 🎉', 'success');
    }

    async completeTask(wasCompleted) {
        if (!this.currentTask) return;

        try {
            const response = await fetch(`/complete_task/${this.currentTask.id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    focus_time: this.currentTask.duration * 60 // Convert to seconds
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to complete task');
            }

            this.showNotification(
                `Task completed! +${result.xp_earned} XP earned! 🎉`, 
                'success'
            );
            
            this.closeFocusModal();
            
            // Reload data
            await this.loadTasks();
            await this.loadStats();
            await this.loadCurrentSchedule();
            
        } catch (error) {
            console.error('Error completing task:', error);
            this.showNotification(error.message, 'error');
        }
    }

    closeFocusModal() {
        const modal = document.getElementById('focus-modal');
        modal.classList.add('hidden');
        
        if (this.focusTimer) {
            clearInterval(this.focusTimer);
            this.focusTimer = null;
        }
        
        this.currentTask = null;
    }

    initChart() {
        const ctx = document.getElementById('priority-chart').getContext('2d');
        
        this.priorityChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['High Priority', 'Medium Priority', 'Low Priority'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#ef4444', '#f59e0b', '#10b981'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });
    }

    updatePriorityChart() {
        if (!this.priorityChart || !this.tasks) return;

        const priorityCounts = [
            this.tasks.filter(t => t.priority === 1).length, // High
            this.tasks.filter(t => t.priority === 2).length, // Medium
            this.tasks.filter(t => t.priority === 3).length  // Low
        ];

        this.priorityChart.data.datasets[0].data = priorityCounts;
        this.priorityChart.update();
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        notification.innerHTML = `
            <span class="notification-icon">${icons[type] || icons.info}</span>
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    // Utility functions
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    getPriorityClass(priority) {
        const classes = { 1: 'high', 2: 'medium', 3: 'low' };
        return classes[priority] || 'medium';
    }

    getPriorityText(priority) {
        const texts = { 1: 'High', 2: 'Medium', 3: 'Low' };
        return texts[priority] || 'Medium';
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.taskFlow = new TaskFlow();
});

console.log('TaskFlow script loaded successfully!');
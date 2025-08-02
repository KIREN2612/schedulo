// ─────────────────────────────────────────────
// 📦 MAIN: DOMContentLoaded – On page load
// ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadTasks();   // Load tasks from DB
    loadStats();   // Load dashboard stats

    // 📌 Task Form Submission
    const taskForm = document.getElementById("task-form");
    taskForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const task = {
            title: document.getElementById("title").value.trim(),
            estimated_time: parseInt(document.getElementById("estimated_time").value),
            priority: parseInt(document.getElementById("priority").value),
            deadline: document.getElementById("deadline").value || null,
        };

        const res = await fetch("/tasks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(task)
        });

        if (res.ok) {
            taskForm.reset();
            loadTasks();
            loadStats();
        }
    });

    // 📌 Schedule Form Submission
    const scheduleForm = document.getElementById("schedule-form");
    scheduleForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const available_time = parseInt(document.getElementById("available_time").value);

        const res = await fetch("/generate_schedule", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ available_time })
        });

        const data = await res.json();
        const scheduleDiv = document.getElementById("schedule");

        if (data.schedule && data.schedule.length > 0) {
            scheduleDiv.innerHTML = `
                <h3>Today's Schedule:</h3>
                <ul class="timeline">
                    ${data.schedule.map(task => `
                        <li>
                            <strong>${task.title}</strong> - ${task.allocated_time} min
                        </li>
                    `).join("")}
                </ul>
            `;
        } else {
            scheduleDiv.textContent = "No schedule could be generated.";
        }
    });
});

// ─────────────────────────────────────────────
// 📋 Load and Display Tasks
// ─────────────────────────────────────────────
async function loadTasks() {
    const res = await fetch("/tasks");
    const data = await res.json();
    const tasks = data.tasks || [];

    const list = document.getElementById("task-list");
    list.innerHTML = "";

    tasks.forEach(task => {
        const card = document.createElement("div");
        card.className = "task-card animated-card";
        card.innerHTML = `
            <div class="task-title">${task.title}</div>
            <div class="task-info">
                <span>${task.estimated_time} min</span>
                <span>Priority: ${task.priority}</span>
                ${task.deadline ? `<span>Deadline: ${task.deadline}</span>` : ""}
            </div>
            <button class="delete-btn" onclick="deleteTask(${task.id})">Delete</button>
        `;
        list.appendChild(card);
    });
}

// ❌ Delete Task (by ID)
async function deleteTask(id) {
    const res = await fetch(`/tasks/${id}`, { method: "DELETE" });
    if (res.ok) {
        loadTasks();
        loadStats();
    } else {
        alert("Failed to delete task.");
    }
}

// ─────────────────────────────────────────────
// 📊 Load Dashboard Stats
// ─────────────────────────────────────────────
async function loadStats() {
    const res = await fetch("/stats");
    const stats = await res.json();

    document.getElementById("total-tasks").textContent = stats.total_tasks;
    document.getElementById("xp").textContent = stats.xp;
    document.getElementById("streak").textContent = stats.streak;
    document.getElementById("xp-bar").value = stats.xp % 100;

    // Pie chart logic
    const ctx = document.getElementById("priority-chart").getContext("2d");
    if (window.priorityChart) window.priorityChart.destroy();

    // Adjust keys here based on your backend output:
    // Example assumes keys are strings: "High", "Medium", "Low"
    const priorityCounts = stats.priority_counts || {};
    const highCount = priorityCounts["High"] || 0;
    const mediumCount = priorityCounts["Medium"] || 0;
    const lowCount = priorityCounts["Low"] || 0;

    window.priorityChart = new Chart(ctx, {
        type: "pie",
        data: {
            labels: ["High", "Medium", "Low"],
            datasets: [{
                label: "Task Priority",
                data: [highCount, mediumCount, lowCount],
                backgroundColor: ["#ef5350", "#ffa726", "#29b6f6"],
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

// ─────────────────────────────────────────────
// 🕐 Schedule Control Functions
// ─────────────────────────────────────────────

// 🔘 Start a Task (start focus mode)
async function startTask(title) {
    alert(`✅ Task "${title}" started!`);
}

// 🔁 Postpone task to tomorrow
async function postponeTask(title) {
    const res = await fetch(`/reschedule_task/${title}`, { method: "POST" });
    if (res.ok) {
        alert(`🔁 "${title}" postponed to tomorrow.`);
        loadSchedule();
    }
}

// ❌ Remove task from schedule
async function removeTask(title) {
    const res = await fetch(`/remove_task_from_schedule/${title}`, { method: "DELETE" });
    if (res.ok) {
        alert(`🗑️ "${title}" removed from schedule.`);
        loadSchedule();
    }
}

// 🔄 Load current day schedule
async function loadSchedule() {
    const res = await fetch("/current_schedule");
    const data = await res.json();
    const scheduleDiv = document.getElementById("schedule");

    if (data.schedule.length === 0) {
        scheduleDiv.innerHTML = "No tasks scheduled.";
        return;
    }

    scheduleDiv.innerHTML = `<h3>Today's Schedule:</h3>`;
    data.schedule.forEach(task => {
        const card = document.createElement("div");
        card.className = "task-card";
        card.innerHTML = `
            <strong>${task.title}</strong> - ${task.allocated_time} min
            <div class="actions">
                <button onclick="startTask('${task.title}')">Start Now</button>
                <button onclick="postponeTask('${task.title}')">Do Later</button>
                <button onclick="removeTask('${task.title}')">Remove</button>
            </div>
        `;
        scheduleDiv.appendChild(card);
    });
}

// ─────────────────────────────────────────────
// 🔒 Focus Mode Timer (Pomodoro-like)
// ─────────────────────────────────────────────
let countdownInterval;
let currentFocusTask = null;

function startTask(title) {
    const taskCard = document.querySelector(`.task-card:has(button[onclick="startTask('${title}')"])`);
    const timeMatch = taskCard.innerHTML.match(/(\d+)\s*min/);
    const duration = timeMatch ? parseInt(timeMatch[1]) : 25;

    currentFocusTask = title;
    openFocusModal(title, duration);
}

function openFocusModal(title, duration) {
    document.getElementById("focus-modal").classList.remove("hidden");
    document.getElementById("focus-task-title").textContent = `Focus Mode – ${title}`;
    document.getElementById("feedback-buttons").classList.add("hidden");

    let remaining = duration * 60;
    updateCountdown(remaining);

    countdownInterval = setInterval(() => {
        remaining--;
        updateCountdown(remaining);

        if (remaining <= 0) {
            clearInterval(countdownInterval);
            showFeedbackPrompt();
        }
    }, 1000);
}

function updateCountdown(seconds) {
    const min = String(Math.floor(seconds / 60)).padStart(2, '0');
    const sec = String(seconds % 60).padStart(2, '0');
    document.getElementById("countdown").textContent = `${min}:${sec}`;
}

function showFeedbackPrompt() {
    document.getElementById("feedback-buttons").classList.remove("hidden");
    const beep = new Audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg");
    beep.play();
}

function submitFocusFeedback(completed) {
    alert(completed ? "🎉 Great job!" : "😅 You’ll get it next time!");
    document.getElementById("focus-modal").classList.add("hidden");
    currentFocusTask = null;
    loadStats(); // optionally reward XP
}

function closeFocusModal() {
    clearInterval(countdownInterval);
    document.getElementById("focus-modal").classList.add("hidden");
}

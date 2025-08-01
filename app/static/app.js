document.addEventListener("DOMContentLoaded", () => {
    loadTasks();
    loadStats();

    const taskForm = document.getElementById("task-form");
    taskForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const task = {
            title: document.getElementById("title").value,
            estimated_time: parseInt(document.getElementById("estimated_time").value),
            priority: parseInt(document.getElementById("priority").value),
            deadline: document.getElementById("deadline").value,
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

        if (data.schedule) {
            scheduleDiv.innerHTML = `
                <h3>Today's Schedule:</h3>
                <ul>
                    ${data.schedule.map(task => `<li><strong>${task.title}</strong> - ${task.allocated_time} min</li>`).join('')}
                </ul>
            `;
        } else {
            scheduleDiv.textContent = "No schedule could be generated.";
        }
    });
});

async function loadTasks() {
    const res = await fetch("/tasks");
    const tasks = await res.json();

    const list = document.getElementById("task-list");
    list.innerHTML = "";

    tasks.forEach(task => {
        const div = document.createElement("div");
        div.className = "task-card";
        div.innerHTML = `
            <strong>${task.title}</strong> - ${task.estimated_time} min | Priority: ${task.priority} ${task.deadline ? "| Deadline: " + task.deadline : ""}
            <button onclick="deleteTask('${task.title}')">🗑</button>
        `;
        list.appendChild(div);
    });
}

async function deleteTask(title) {
    const res = await fetch(`/tasks/${title}`, {
        method: "DELETE"
    });

    if (res.ok) {
        loadTasks();
        loadStats();
    }
}

async function loadStats() {
    const res = await fetch("/stats");
    const stats = await res.json();

    document.getElementById("total-tasks").textContent = stats.total_tasks;
    document.getElementById("xp").textContent = stats.xp;
    document.getElementById("streak").textContent = stats.streak;
    document.getElementById("xp-bar").value = stats.xp % 100;

    // Chart update
    const ctx = document.getElementById('priority-chart').getContext('2d');
    if (window.priorityChart) window.priorityChart.destroy(); // avoid overlap

    window.priorityChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['High', 'Medium', 'Low'],
            datasets: [{
                label: 'Task Priority',
                data: [stats.priority_counts[1], stats.priority_counts[2], stats.priority_counts[3]],
                backgroundColor: ['#ff6b6b', '#ffa726', '#64b5f6'],
            }]
        }
    });
}

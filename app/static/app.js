document.addEventListener("DOMContentLoaded", () => {
    const taskForm = document.getElementById("task-form");
    const taskList = document.getElementById("task-list");
    const scheduleForm = document.getElementById("schedule-form");
    const scheduleDiv = document.getElementById("schedule");

    async function loadTasks() {
        const res = await fetch("/tasks");
        const data = await res.json();
        renderTasks(data.tasks);
    }

    function renderTasks(tasks) {
        taskList.innerHTML = "";
        tasks.forEach(task => {
            const div = document.createElement("div");
            div.className = "task-card";
            div.innerHTML = `
                <strong>${task.title}</strong><br>
                Time: ${task.estimated_time} min | Priority: ${task.priority}${task.deadline ? ` | Deadline: ${task.deadline}` : ""}
                <button onclick="deleteTask('${task.title}')">Delete</button>
            `;
            taskList.appendChild(div);
        });
    }

    taskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const task = {
            title: document.getElementById("title").value,
            estimated_time: parseInt(document.getElementById("estimated_time").value),
            priority: parseInt(document.getElementById("priority").value),
            deadline: document.getElementById("deadline").value || null
        };

        const res = await fetch("/tasks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(task)
        });

        if (res.ok) {
            taskForm.reset();
            loadTasks();
        }
    });

    scheduleForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const available_time = parseInt(document.getElementById("available_time").value);

        const res = await fetch("/generate_schedule", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ available_time })
        });

        const data = await res.json();
        if (data.schedule) {
            renderSchedule(data.schedule);
        } else {
            scheduleDiv.innerHTML = `<p style="color: red;">${data.error}</p>`;
        }
    });

    function renderSchedule(schedule) {
        scheduleDiv.innerHTML = "<h3>Generated Schedule:</h3>";
        schedule.forEach(task => {
            const div = document.createElement("div");
            div.className = "task-card";
            div.innerHTML = `
                <strong>${task.title}</strong><br>
                Time: ${task.estimated_time} min | Priority: ${task.priority}
            `;
            scheduleDiv.appendChild(div);
        });
    }

    window.deleteTask = async (title) => {
        const res = await fetch(`/tasks/${encodeURIComponent(title)}`, {
            method: "DELETE"
        });

        if (res.ok) {
            loadTasks();
        }
    };

    loadTasks();
});

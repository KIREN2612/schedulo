document.addEventListener("DOMContentLoaded", () => {
    fetchTasks();
//this is for the fetching and is done by js
    document.getElementById("taskForm").addEventListener("submit", async (e) => {
        e.preventDefault();
        const task = {
            title: document.getElementById("title").value,
            estimated_time: parseInt(document.getElementById("estimated_time").value),
            priority: parseInt(document.getElementById("priority").value),
            deadline: document.getElementById("deadline").value || null,
        };
//fetching tasks to the backend
        await fetch("/tasks", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(task),
        });
        fetchTasks();
    });
});

async function fetchTasks() {
    const res = await fetch("/tasks");
    const data = await res.json();
    const list = document.getElementById("taskList");
    list.innerHTML = "";

    data.tasks.forEach((task) => {
        const li = document.createElement("li");
        li.innerHTML = `${task.title} (⏱ ${task.estimated_time} min, ⚡ ${task.priority})
            <button onclick="deleteTask('${task.title}')">🗑</button>`;
        list.appendChild(li);
    });
}
//deleting the task
async function deleteTask(title) {
    await fetch(`/tasks/${encodeURIComponent(title)}`, { method: "DELETE" });
    fetchTasks();
}

//this is for generating schedule
async function generateSchedule() {
    const available_time = parseInt(prompt("Available time in minutes:"));

    const res = await fetch("/generate_schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ available_time }),
    });
    const data = await res.json();
    const list = document.getElementById("scheduleList");
    list.innerHTML = "";

    data.schedule.forEach((task) => {
        const li = document.createElement("li");
        li.textContent = `${task.title} (⏱ ${task.estimated_time} min, ⚡ ${task.priority})`;
        list.appendChild(li);
    });
}

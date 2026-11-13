import React, { useState } from 'react';

export default function RoutineView({ tasks, setTasks }) {
  const [newTask, setNewTask] = useState("");

  const addTask = () => {
    if (!newTask) return;
    setTasks([...tasks, { text: newTask, done: false }]);
    setNewTask("");
  };

  const toggleTask = (index) => {
    const updated = [...tasks];
    updated[index].done = !updated[index].done;
    setTasks(updated);
  };

  return (
    <div style={{ padding: "20px", height: "100vh", backgroundColor: "#f3f4f6", overflowY: "auto" }}>
      <h1 style={{ fontSize: "24px", fontWeight: "bold", marginBottom: "20px", color: "#1e3a8a" }}>My Daily Routine</h1>
      
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
        <input 
          value={newTask} 
          onChange={(e) => setNewTask(e.target.value)} 
          placeholder="Add a custom task..." 
          style={{ flex: 1, padding: "12px", borderRadius: "8px", border: "1px solid #d1d5db", outline: "none" }}
          onKeyDown={(e) => e.key === 'Enter' && addTask()}
        />
        <button onClick={addTask} style={{ backgroundColor: "#2563eb", color: "white", padding: "0 20px", borderRadius: "8px", border: "none", fontWeight: "bold" }}>Add</button>
      </div>

      {tasks.map((task, i) => (
        <div 
          key={i} 
          onClick={() => toggleTask(i)} 
          style={{ 
            padding: "16px", marginBottom: "12px", borderRadius: "12px", border: "1px solid #e5e7eb", 
            backgroundColor: task.done ? "#dcfce7" : "white", cursor: "pointer", display: "flex", alignItems: "center", gap: "12px",
            transition: "all 0.2s ease", opacity: task.done ? 0.7 : 1
          }}
        >
          <input type="checkbox" checked={task.done} readOnly style={{ width: "20px", height: "20px", accentColor: "#16a34a" }} />
          <span style={{ fontSize: "16px", textDecoration: task.done ? "line-through" : "none", color: task.done ? "#166534" : "#1f2937" }}>
            {task.text}
          </span>
        </div>
      ))}
    </div>
  );
}
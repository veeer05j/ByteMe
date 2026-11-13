import React, { useState, useEffect } from 'react';
import MapView from './MapView';
import ChatView from './ChatView';
import RoutineView from './RoutineView';

export default function App() {
  const [activeTab, setActiveTab] = useState("map");
  
  // Move the routine state here
  const [tasks, setTasks] = useState(() => {
    const saved = localStorage.getItem('myRoutine');
    return saved ? JSON.parse(saved) : [
      { text: "Drink a glass of water", done: false },
      { text: "Take 5 deep breaths", done: false }
    ];
  });

  // Save to local storage whenever tasks change
  useEffect(() => {
    localStorage.setItem('myRoutine', JSON.stringify(tasks));
  }, [tasks]);

  const addTask = (taskText) => {
    setTasks(prev => [...prev, { text: taskText, done: false }]);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", width: "100vw", overflow: "hidden" }}>
      
      <div style={{ flex: 1, overflow: "hidden" }}>
        {activeTab === "map" && <MapView setActiveTab={setActiveTab} />}
        {activeTab === "chat" && <ChatView addTask={addTask} />}
        {activeTab === "routine" && <RoutineView tasks={tasks} setTasks={setTasks} />}
      </div>

      {/* Navigation Bar */}
      <div style={{ display: "flex", justifyContent: "space-around", backgroundColor: "#ffffff", borderTop: "1px solid #e5e7eb", padding: "15px 0", zIndex: 2000 }}>
        <button onClick={() => setActiveTab("map")} style={{ background: "none", border: "none", fontSize: "24px", cursor: "pointer", opacity: activeTab === "map" ? 1 : 0.3 }}>🗺️</button>
        <button onClick={() => setActiveTab("chat")} style={{ background: "none", border: "none", fontSize: "24px", cursor: "pointer", opacity: activeTab === "chat" ? 1 : 0.3 }}>💬</button>
        <button onClick={() => setActiveTab("routine")} style={{ background: "none", border: "none", fontSize: "24px", cursor: "pointer", opacity: activeTab === "routine" ? 1 : 0.3 }}>✅</button>
      </div>
    </div>
  );
}
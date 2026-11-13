import React, { useState, useEffect, useRef } from 'react';

export default function ChatView({ addTask }) {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I am your health assistant. Ask me about food, exercises, or your prescription." }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  useEffect(scrollToBottom, [messages, isTyping]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = input;
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    setIsTyping(true);

    try {
      // 🚨 REPLACE 'YOUR_API_KEY_HERE' WITH YOUR ACTUAL GEMINI KEY
      const API_KEY = "YOUR_API_KEY_HERE"; 
      
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${API_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{
            parts: [{ text: `You are a wellness assistant in Mauritius. If the user mentions a prescription or illness, suggest 1 healthy local meal (like fruit or vegetables) and 1 gentle exercise (like stretching). Add a disclaimer that this is not medical advice. Keep it under 2 sentences. User says: ${userMessage}` }]
          }]
        })
      });

      const data = await response.json();
      const aiText = data.candidates[0].content.parts[0].text;

      setMessages(prev => [...prev, { role: "assistant", content: aiText }]);
      
      // AUTO-ADD TO ROUTINE (If the AI mentioned exercise or meal)
      if (aiText.toLowerCase().includes("stretch") || aiText.toLowerCase().includes("walk")) {
         addTask("Gentle stretching (AI Recommended)");
      }

    } catch (error) {
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I lost connection. Please check your internet and try again." }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", backgroundColor: "#f3f4f6" }}>
      <div style={{ flex: 1, padding: "20px", overflowY: "auto" }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", justifyContent: msg.role === 'user' ? "flex-end" : "flex-start", marginBottom: "15px" }}>
            <div style={{ padding: "12px 16px", borderRadius: "16px", maxWidth: "80%", backgroundColor: msg.role === 'user' ? "#2563eb" : "white", color: msg.role === 'user' ? "white" : "black", boxShadow: "0 2px 5px rgba(0,0,0,0.05)", fontSize: "15px", lineHeight: "1.4" }}>
              {msg.content}
            </div>
          </div>
        ))}
        {isTyping && (
           <div style={{ color: "#6b7280", fontStyle: "italic", fontSize: "14px" }}>VitaBot is typing...</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={{ display: "flex", padding: "15px", backgroundColor: "white", borderTop: "1px solid #e5e7eb" }}>
        <input 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          placeholder="Ask me anything..." 
          style={{ flex: 1, padding: "12px", borderRadius: "24px", border: "1px solid #d1d5db", outline: "none", fontSize: "16px" }}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          disabled={isTyping}
        />
        <button 
          onClick={sendMessage} 
          disabled={isTyping}
          style={{ marginLeft: "10px", backgroundColor: isTyping ? "#93c5fd" : "#2563eb", color: "white", padding: "0 20px", borderRadius: "24px", border: "none", fontWeight: "bold" }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
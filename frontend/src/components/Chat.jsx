import { useState, useRef, useEffect } from "react";
import { chatStream } from "../services/api";
import "../styles/chat.css";

function Chat({activeSource}) {
    const [messages, setMessages] = useState([
        { role: "assistant", text: "Hello! I'm ready to answer questions about your data." }
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    
    const chatEndRef = useRef(null);
    const textareaRef = useRef(null);

    // Auto-scroll to bottom
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Auto-resize textarea logic
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto'; // Reset height
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`; // Set to content height
        }
    }, [input]);

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault(); // Prevent new line
            sendMessage();
        }
    };

    const sendMessage = async () => {
        if (!input.trim() || loading) return;

        const userMessage = { role: "user", text: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLoading(true);

        try {
            setMessages((prev) => [...prev, { role: "assistant", text: "" }]);
            
            await chatStream(input, (token) => {
                setMessages((prev) => {
                    const updated = [...prev];
                    const lastMsg = updated[updated.length - 1];
                    updated[updated.length - 1] = {
                        ...lastMsg,
                        text: lastMsg.text + token,
                    };
                    return updated;
                });
            });
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="chat-container">

        {/* Header */}
        <div className="chat-header">
            <div className="context-chip">
            <i className="ri-file-text-line"></i>
            <span>Using context: <strong>{activeSource}</strong></span>
            </div>
        </div>


            <div className="chat-window">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`chat-bubble ${msg.role}`}>
                        {msg.text}
                    </div>
                ))}
                {loading && (
                    <div className="chat-bubble assistant">...</div>
                )}
                <div ref={chatEndRef} />
            </div>

            <div className="chat-input-area">
                <div className="input-wrapper">
                    <textarea
                        ref={textareaRef}
                        className="chat-textarea"
                        placeholder="Ask a question..."
                        rows={1}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={loading}
                    />
                    
                    <button 
                        className="send-btn" 
                        onClick={sendMessage} 
                        disabled={loading || !input.trim()}
                    >
                        <i className="ri-send-plane-fill"></i>
                    </button>
                </div>


                {/* Footer */}

                <p className="disclaimer-text">
                    RAG Assistant can make mistakes. Please double-check responses.
                </p>
            </div>
        </div>
    );
}

export default Chat;
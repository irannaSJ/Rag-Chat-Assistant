import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { chatStream } from "../services/api";
import "../styles/chat.css";

function Chat({ sources = [] }) {
    const [messages, setMessages] = useState([
        {
            role: "assistant",
            text: "Hello! Ask me anything across your uploaded documents, websites, and notes.",
            sources: [],
        },
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);

    const chatEndRef = useRef(null);
    const textareaRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [input]);

    const handleKeyDown = (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const clearChat = () => {
        if (loading) return;
        setMessages([
            {
                role: "assistant",
                text: "Chat cleared. Ask a new question about your knowledge base!",
                sources: [],
            },
        ]);
    };

    const sendMessage = async () => {
        const trimmed = input.trim();
        if (!trimmed || loading) return;

        const userMessage = { role: "user", text: trimmed };
        setMessages((prev) => [
            ...prev,
            userMessage,
            { role: "assistant", text: "", sources: [], streaming: true },
        ]);
        setInput("");
        setLoading(true);

        try {
            await chatStream(trimmed, {
                onSources: (retrievedSources) => {
                    setMessages((prev) => {
                        const updated = [...prev];
                        const lastMsg = updated[updated.length - 1];
                        updated[updated.length - 1] = {
                            ...lastMsg,
                            sources: retrievedSources,
                        };
                        return updated;
                    });
                },
                onToken: (token) => {
                    setMessages((prev) => {
                        const updated = [...prev];
                        const lastMsg = updated[updated.length - 1];
                        updated[updated.length - 1] = {
                            ...lastMsg,
                            text: lastMsg.text + token,
                        };
                        return updated;
                    });
                },
            });
        } catch (error) {
            setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                updated[updated.length - 1] = {
                    ...lastMsg,
                    text: `⚠️ ${error.message || "Failed to get response from server."}`,
                };
                return updated;
            });
        } finally {
            setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];
                if (lastMsg?.role === "assistant") {
                    updated[updated.length - 1] = { ...lastMsg, streaming: false };
                }
                return updated;
            });
            setLoading(false);
        }
    };

    const sourceSummary =
        sources.length === 1
            ? sources[0].source_name
            : `${sources.length} active sources`;

    return (
        <div className="chat-container">
            {/* Header */}
            <div className="chat-header">
                <div className="context-chip">
                    <i className="ri-database-2-line"></i>
                    <span>
                        Knowledge Base: <strong>{sourceSummary}</strong>
                    </span>
                </div>

                {messages.length > 1 && (
                    <button
                        type="button"
                        className="clear-chat-btn"
                        onClick={clearChat}
                        disabled={loading}
                        title="Clear conversation"
                    >
                        <i className="ri-refresh-line"></i> Clear
                    </button>
                )}
            </div>

            {/* Messages */}
            <div className="chat-window">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`chat-bubble ${msg.role}`}>
                        {msg.role === "assistant" ? (
                            <>
                                {msg.text ? (
                                    <div className="markdown-body">
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                            {msg.text}
                                        </ReactMarkdown>
                                    </div>
                                ) : (
                                    <span className="typing-dots">Thinking...</span>
                                )}

                                {!msg.streaming && msg.sources && msg.sources.length > 0 && (
                                    <div className="citations-bar">
                                        <span className="citations-label">Sources:</span>
                                        {msg.sources.map((src, sIdx) =>
                                            src.url ? (
                                                <a
                                                    key={sIdx}
                                                    href={src.url}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="citation-badge link"
                                                >
                                                    <i className="ri-global-line"></i> {src.label}
                                                </a>
                                            ) : (
                                                <span key={sIdx} className="citation-badge">
                                                    <i
                                                        className={
                                                            src.source_type === "PDF"
                                                                ? "ri-file-pdf-line"
                                                                : "ri-sticky-note-line"
                                                        }
                                                    ></i>{" "}
                                                    {src.label}
                                                </span>
                                            )
                                        )}
                                    </div>
                                )}
                            </>
                        ) : (
                            msg.text
                        )}
                    </div>
                ))}
                <div ref={chatEndRef} />
            </div>

            {/* Input Area */}
            <div className="chat-input-area">
                <div className="input-wrapper">
                    <textarea
                        ref={textareaRef}
                        className="chat-textarea"
                        placeholder="Ask a question across your documents..."
                        rows={1}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={loading}
                    />

                    <button
                        type="button"
                        className="send-btn"
                        onClick={sendMessage}
                        disabled={loading || !input.trim()}
                    >
                        <i className="ri-send-plane-fill"></i>
                    </button>
                </div>

                <p className="disclaimer-text">
                    Answers are grounded in your uploaded sources. Verify important details.
                </p>
            </div>
        </div>
    );
}

export default Chat;
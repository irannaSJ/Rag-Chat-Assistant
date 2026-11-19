import { useEffect, useState } from "react";
import "./styles/global.css";
import Ingest from "./components/Ingest";
import Chat from "./components/Chat";
import { clearAllSources, deleteSource, fetchSources } from "./services/api";

function App() {
    const [sources, setSources] = useState([]);
    const [loadingSources, setLoadingSources] = useState(true);
    const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "light");
    const [isSidebarOpen, setSidebarOpen] = useState(true);

    // Responsive sidebar default on mount
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth < 768) {
                setSidebarOpen(false);
            } else {
                setSidebarOpen(true);
            }
        };

        handleResize();
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    // Apply & persist theme
    useEffect(() => {
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
    }, [theme]);

    // Load existing knowledge base sources from backend on startup
    const loadExistingSources = async () => {
        try {
            const data = await fetchSources();
            setSources(data.sources || []);
        } catch (err) {
            console.error("Failed to fetch existing sources:", err);
        } finally {
            setLoadingSources(false);
        }
    };

    useEffect(() => {
        loadExistingSources();
    }, []);

    const toggleTheme = () => {
        setTheme((prev) => (prev === "light" ? "dark" : "light"));
    };

    const handleIngestComplete = () => {
        loadExistingSources();
    };

    const handleDeleteSource = async (sourceId) => {
        try {
            const data = await deleteSource(sourceId);
            setSources(data.sources || []);
        } catch (err) {
            console.error("Failed to remove source:", err);
        }
    };

    const handleClearAll = async () => {
        try {
            await clearAllSources();
            setSources([]);
        } catch (err) {
            console.error("Failed to clear sources:", err);
        }
    };

    const getSourceIcon = (type) => {
        if (type === "PDF") return "ri-file-pdf-2-line";
        if (type === "WEBSITE") return "ri-global-line";
        return "ri-sticky-note-line";
    };

    return (
        <div className="app-container">
            {/* Hamburger Toggle when Sidebar is collapsed */}
            {!isSidebarOpen && (
                <button
                    type="button"
                    className="menu-btn"
                    onClick={() => setSidebarOpen(true)}
                    title="Open Sidebar"
                >
                    <i className="ri-menu-line"></i>
                </button>
            )}

            {/* Sidebar */}
            <aside className={`sidebar ${isSidebarOpen ? "" : "collapsed"}`}>
                <div className="sidebar-content">
                    <div className="sidebar-header">
                        <h1>RAG Assistant</h1>
                        <button
                            type="button"
                            className="menu-btn"
                            style={{ position: "static" }}
                            onClick={() => setSidebarOpen(false)}
                            title="Collapse Sidebar"
                        >
                            <i className="ri-menu-fold-line"></i>
                        </button>
                    </div>

                    {/* Ingest Component */}
                    <Ingest onIngestComplete={handleIngestComplete} />

                    {/* Active Knowledge Base Sources */}
                    <div className="sources-section">
                        <div className="sources-header">
                            <span>Knowledge Base ({sources.length})</span>
                            {sources.length > 0 && (
                                <button
                                    type="button"
                                    className="clear-all-link"
                                    onClick={handleClearAll}
                                >
                                    Clear All
                                </button>
                            )}
                        </div>

                        {loadingSources ? (
                            <p className="empty-sources-text">Loading sources...</p>
                        ) : sources.length === 0 ? (
                            <p className="empty-sources-text">
                                No documents indexed yet. Add a PDF, URL, or note above.
                            </p>
                        ) : (
                            <ul className="sources-list">
                                {sources.map((src) => (
                                    <li key={src.source_id} className="source-item">
                                        <i className={`${getSourceIcon(src.source_type)} source-type-icon`}></i>
                                        <div className="source-item-info">
                                            <span className="source-item-name" title={src.source_name}>
                                                {src.source_name}
                                            </span>
                                            <span className="source-item-meta">
                                                {src.source_type} • {src.chunk_count} chunks
                                            </span>
                                        </div>
                                        <button
                                            type="button"
                                            className="source-delete-btn"
                                            onClick={() => handleDeleteSource(src.source_id)}
                                            title="Remove source"
                                        >
                                            <i className="ri-close-line"></i>
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>

                    {/* Footer with Theme Toggle */}
                    <div className="sidebar-footer">
                        <button type="button" className="theme-btn" onClick={toggleTheme}>
                            {theme === "light" ? (
                                <>
                                    <i className="ri-moon-line"></i> Dark Mode
                                </>
                            ) : (
                                <>
                                    <i className="ri-sun-line"></i> Light Mode
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main Chat Area */}
            <main className="main-content">
                {sources.length > 0 ? (
                    <Chat sources={sources} />
                ) : (
                    <div className="welcome-empty-state">
                        <div className="welcome-emoji">📚</div>
                        <h2>Multi-Document RAG Assistant</h2>
                        <p>
                            Upload PDFs, add website URLs, or paste notes in the sidebar to start
                            asking grounded questions.
                        </p>
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
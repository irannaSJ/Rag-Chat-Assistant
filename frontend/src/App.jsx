import { useState, useEffect } from "react";
import "./styles/global.css";
import Ingest from "./components/Ingest";
import Chat from "./components/Chat";

function App() {
    const [ready, setReady] = useState(false);
    const [theme, setTheme] = useState("light");
    const [isSidebarOpen, setSidebarOpen] = useState(true);

    const [activeSource,setActiveSource] = useState("")



    // NEW: Check for mobile screen on mount to default sidebar to CLOSED
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth < 768) {
                setSidebarOpen(false);
            } else {
                setSidebarOpen(true);
            }
        };

        // Run once on mount
        handleResize();

        // Optional: Listen for resize (good for rotation)
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);




    useEffect(() => {
        document.documentElement.setAttribute("data-theme", theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme((prev) => (prev === "light" ? "dark" : "light"));
    };


    const handleIngestComplete = (sourceName) =>{
        setActiveSource(sourceName);
        setReady(true)
    }

    return (
        <div className="app-container">
            {/* 1. Toggle Button (Hamburger) - Visible when Sidebar is CLOSED */}
            {!isSidebarOpen && (
                <button 
                    className="menu-btn" 
                    onClick={() => setSidebarOpen(true)}
                    title="Open Sidebar"
                >
                    <i className="ri-menu-line"></i>
                </button>
            )}

            {/* 2. The Sidebar */}
            <aside className={`sidebar ${isSidebarOpen ? "" : "collapsed"}`}>
                <div className="sidebar-content">
                    <div className="sidebar-header">
                        <h1>RAG Assistant</h1>
                        {/* Close Button inside Sidebar */}
                        <button 
                            className="menu-btn" 
                            style={{position: 'static'}}
                            onClick={() => setSidebarOpen(false)}
                        >
                            <i className="ri-menu-fold-line"></i>
                        </button>
                    </div>

                    {/* Ingest Component */}
                    <Ingest onIngestComplete={handleIngestComplete} />

                    

                    {/* Footer with Theme Toggle */}
                    <div className="sidebar-footer">
                        <button className="theme-btn" onClick={toggleTheme}>
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

            {/* 3. Main Chat Area */}
            <main className="main-content">
                {ready ? (
                    <Chat activeSource={activeSource}/>
                ) : (
                    <div style={{
                        display: 'flex', 
                        flexDirection: 'column',
                        alignItems: 'center', 
                        justifyContent: 'center', 
                        height: '100%',
                        color: 'var(--text-secondary)'
                    }}>
                        <div style={{fontSize: '4rem', marginBottom: '1rem'}}>👋</div>
                        <h2>Welcome!</h2>
                        <p>Upload a document to start chatting.</p>
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
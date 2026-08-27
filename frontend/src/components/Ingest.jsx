import { useState } from "react";
import { ingestPDF, ingestWebsite } from "../services/api";
import "../styles/ingest.css";

function Ingest({ onIngestComplete }) {
    const [mode, setMode] = useState("pdf");
    const [file, setFile] = useState(null);
    const [url, setUrl] = useState("");
    const [status, setStatus] = useState("");
    const [loading, setLoading] = useState(false);

    // New: Remove selected file
    const removeFile = () => {
        setFile(null);
        setStatus("");
    };

    const handleIngest = async () => {
        if (!file && mode === "pdf") return;
        if (!url && mode === "website") return;

        setLoading(true);
        setStatus("Ingesting...");
        
        try {
            let response;

            let sourceName = "";

            if (mode === "pdf") {
                response = await ingestPDF(file);
                sourceName = file.name;
            } else {
                response = await ingestWebsite(url);
                sourceName = url;
            }
            
            // Assuming successful response
            setStatus("Ingestion Successful ✅");
            onIngestComplete(sourceName);
        } catch (err) {
            setStatus("Ingestion Failed ❌");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="ingest-container">
            <div className="ingest-modes">
                <button 
                    className={mode === "pdf" ? "active" : ""} 
                    onClick={() => setMode("pdf")}
                >
                    <i className="ri-file-pdf-line"></i> PDF
                </button>
                <button 
                    className={mode === "website" ? "active" : ""} 
                    onClick={() => setMode("website")}
                >
                    <i className="ri-global-line"></i> URL
                </button>
            </div>

            {mode === "pdf" && (
    <>
        {!file ? (
            /* MODERN UPLOAD ZONE */
            <div className="file-upload-area">
                <input
                    type="file"
                    id="pdf-upload"
                    accept="application/pdf"
                    onChange={(e) => setFile(e.target.files[0])}
                />
                <label htmlFor="pdf-upload" className="upload-label">
                    <div className="icon-wrapper">
                        <i className="ri-file-upload-line"></i>
                    </div>
                    <span className="upload-text">
                        <strong>Click to upload</strong> or drag PDF here
                    </span>
                    <span className="upload-hint">MAX 10MB</span>
                </label>
            </div>
        ) : (
            /* MODERN FILE CARD */
            <div className="file-card">
                <div className="file-icon-wrapper">
                    <i className="ri-file-pdf-2-fill"></i>
                </div>
                
                <div className="file-details">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                    </span>
                </div>

                <button 
                    className="remove-btn" 
                    onClick={removeFile} 
                    title="Remove file"
                >
                    <i className="ri-delete-bin-line"></i>
                </button>
            </div>
        )}
    </>
)}

            {mode === "website" && (
                <input
                    className="url-input"
                    type="text"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                />
            )}

            <button className="ingest-btn" onClick={handleIngest} disabled={loading}>
                {loading ? "Processing..." : (
                    <>Start Ingestion <i className="ri-arrow-right-line"></i></>
                )}
            </button>

            {status && <p className="ingest-status">{status}</p>}
        </div>
    );
}

export default Ingest;
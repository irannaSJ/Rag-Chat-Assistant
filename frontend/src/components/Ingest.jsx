import { useRef, useState } from "react";
import {
    ingestNotesFile,
    ingestNotesText,
    ingestPDF,
    ingestWebsite,
} from "../services/api";
import "../styles/ingest.css";

function Ingest({ onIngestComplete }) {
    const [mode, setMode] = useState("pdf");
    const [file, setFile] = useState(null);
    const [url, setUrl] = useState("");
    const [noteTitle, setNoteTitle] = useState("");
    const [noteText, setNoteText] = useState("");
    const [status, setStatus] = useState({ type: "", message: "" });
    const [loading, setLoading] = useState(false);

    const fileInputRef = useRef(null);

    const switchMode = (nextMode) => {
        setMode(nextMode);
        setFile(null);
        setStatus({ type: "", message: "" });
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const removeFile = () => {
        setFile(null);
        setStatus({ type: "", message: "" });
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const isSubmitDisabled = () => {
        if (loading) return true;
        if (mode === "pdf") return !file;
        if (mode === "website") return !url.trim();
        if (mode === "notes") return !file && !noteText.trim();
        return true;
    };

    const handleIngest = async () => {
        if (isSubmitDisabled()) return;

        setLoading(true);
        setStatus({ type: "info", message: "Processing & indexing..." });

        try {
            let result;

            if (mode === "pdf") {
                result = await ingestPDF(file);
                removeFile();
            } else if (mode === "website") {
                result = await ingestWebsite(url.trim());
                setUrl("");
            } else if (mode === "notes") {
                if (file) {
                    result = await ingestNotesFile(file);
                    removeFile();
                } else {
                    result = await ingestNotesText(
                        noteTitle.trim() || "Quick Note",
                        noteText.trim()
                    );
                    setNoteTitle("");
                    setNoteText("");
                }
            }

            setStatus({
                type: "success",
                message: `Added "${result.source.source_name}" (${result.source.chunk_count} chunks)`,
            });

            if (onIngestComplete) {
                onIngestComplete(result.source);
            }
        } catch (err) {
            setStatus({
                type: "error",
                message: err.message || "Ingestion failed",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="ingest-container">
            <div className="ingest-modes">
                <button
                    type="button"
                    className={mode === "pdf" ? "active" : ""}
                    onClick={() => switchMode("pdf")}
                >
                    <i className="ri-file-pdf-line"></i> PDF
                </button>
                <button
                    type="button"
                    className={mode === "website" ? "active" : ""}
                    onClick={() => switchMode("website")}
                >
                    <i className="ri-global-line"></i> URL
                </button>
                <button
                    type="button"
                    className={mode === "notes" ? "active" : ""}
                    onClick={() => switchMode("notes")}
                >
                    <i className="ri-sticky-note-line"></i> Notes
                </button>
            </div>

            {mode === "pdf" && (
                <>
                    {!file ? (
                        <div className="file-upload-area">
                            <input
                                ref={fileInputRef}
                                type="file"
                                id="pdf-upload"
                                accept="application/pdf"
                                onChange={(e) => setFile(e.target.files?.[0] || null)}
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
                                type="button"
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
                    type="url"
                    placeholder="https://example.com/article"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                />
            )}

            {mode === "notes" && (
                <div className="notes-input-group">
                    <input
                        className="url-input"
                        type="text"
                        placeholder="Note title (optional)"
                        value={noteTitle}
                        onChange={(e) => setNoteTitle(e.target.value)}
                        disabled={Boolean(file)}
                    />
                    <textarea
                        className="notes-textarea"
                        rows={4}
                        placeholder="Paste notes or text here..."
                        value={noteText}
                        onChange={(e) => setNoteText(e.target.value)}
                        disabled={Boolean(file)}
                    />
                    <div className="notes-file-row">
                        {!file ? (
                            <label className="notes-file-btn">
                                <i className="ri-attachment-2"></i> Or attach .txt / .md
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".txt,.md,text/plain,text/markdown"
                                    hidden
                                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                                />
                            </label>
                        ) : (
                            <div className="file-card">
                                <div className="file-icon-wrapper note-icon">
                                    <i className="ri-file-text-fill"></i>
                                </div>
                                <div className="file-details">
                                    <span className="file-name">{file.name}</span>
                                    <span className="file-size">
                                        {(file.size / 1024).toFixed(1)} KB
                                    </span>
                                </div>
                                <button
                                    type="button"
                                    className="remove-btn"
                                    onClick={removeFile}
                                    title="Remove file"
                                >
                                    <i className="ri-delete-bin-line"></i>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <button
                type="button"
                className="ingest-btn"
                onClick={handleIngest}
                disabled={isSubmitDisabled()}
            >
                {loading ? (
                    "Processing..."
                ) : (
                    <>
                        Add to Knowledge Base <i className="ri-add-line"></i>
                    </>
                )}
            </button>

            {status.message && (
                <p className={`ingest-status ${status.type}`}>{status.message}</p>
            )}
        </div>
    );
}

export default Ingest;
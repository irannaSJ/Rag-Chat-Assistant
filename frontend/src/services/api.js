const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function _handleResponse(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.detail || `Request failed with status ${response.status}`);
    }
    return data;
}

export const fetchSources = async () => {
    const response = await fetch(`${API_BASE_URL}/sources`);
    return _handleResponse(response);
};

export const deleteSource = async (sourceId) => {
    const response = await fetch(`${API_BASE_URL}/sources/${encodeURIComponent(sourceId)}`, {
        method: "DELETE",
    });
    return _handleResponse(response);
};

export const clearAllSources = async () => {
    const response = await fetch(`${API_BASE_URL}/sources`, {
        method: "DELETE",
    });
    return _handleResponse(response);
};

export const ingestPDF = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/ingest/pdf`, {
        method: "POST",
        body: formData,
    });
    return _handleResponse(response);
};

export const ingestNotesFile = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/ingest/notes`, {
        method: "POST",
        body: formData,
    });
    return _handleResponse(response);
};

export const ingestNotesText = async (title, content) => {
    const response = await fetch(`${API_BASE_URL}/ingest/notes/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content }),
    });
    return _handleResponse(response);
};

export const ingestWebsite = async (url) => {
    const response = await fetch(`${API_BASE_URL}/ingest/website`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
    });
    return _handleResponse(response);
};

export const chatStream = async (query, { onToken, onSources } = {}) => {
    const response = await fetch(`${API_BASE_URL}/chat-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
    });

    if (!response.ok || !response.body) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || "Streaming failed");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;

            try {
                const event = JSON.parse(trimmed);
                if (event.type === "sources" && onSources) {
                    onSources(event.sources || []);
                } else if (event.type === "token" && onToken) {
                    onToken(event.content || "");
                }
            } catch {
                // Fallback if plain text is ever emitted
                if (onToken) onToken(trimmed);
            }
        }
    }

    // Flush any remaining buffered line
    if (buffer.trim()) {
        try {
            const event = JSON.parse(buffer.trim());
            if (event.type === "sources" && onSources) {
                onSources(event.sources || []);
            } else if (event.type === "token" && onToken) {
                onToken(event.content || "");
            }
        } catch {
            if (onToken) onToken(buffer);
        }
    }
};
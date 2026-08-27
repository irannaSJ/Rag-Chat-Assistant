const API_BASE_URL = "http://127.0.0.1:8000";

export const chatStream = async(query,onToken) =>{
    const response = await fetch(`${API_BASE_URL}/chat-stream`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({query}),
    })

    if (!response.ok || !response.body){
        throw new Error("Streaming Failed")
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    while(true){
        const {value,done} = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value,{stream:true})
        onToken(chunk);
    }
};

export const ingestPDF = async(file) =>{
    const formData = new FormData();
    formData.append("file",file);

    return fetch(`${API_BASE_URL}/ingest/pdf`,{
        method:"POST",
        body:formData,
    });
};

export const ingestWebsite = async(url) =>{
    return fetch(`${API_BASE_URL}/ingest/website`,{
        method : "POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({url}),
    });
};
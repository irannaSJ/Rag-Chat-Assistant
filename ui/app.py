import streamlit as st 
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title = "RAG Chat", layout = "centered")

st.title("RAG Chat Assistant")
st.write("Ask questions based on the ingested data.")


st.sidebar.header("Ingest Data")
ingest_type = st.sidebar.selectbox(
    "Select Data type",
    ["PDF","Notes","Website"]
)

if ingest_type == "PDF":
    uploaded_file = st.sidebar.file_uploader("Upload PDF")
    if st.sidebar.button("Ingest PDF"):
        if uploaded_file and uploaded_file.name.lower().endswith(".pdf"):
            
            files= {
                "file":(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf"
                    )
                }


            response = requests.post(f"{API_URL}/ingest/pdf",files = files)
            if response.status_code == 200:
                st.sidebar.success("PDF ingested successfully")
            else:
                st.sidebar.error("PDF ingestion failed")
        else:
            st.sidebar.warning("Please upload the pdf file")

elif ingest_type == "Notes":
    uploaded_file = st.sidebar.file_uploader("Upload Notes",type=["txt","md"])
    if st.sidebar.button("Ingest Notes"):
        if uploaded_file:
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "text/plain"
                )
            }
            response = requests.post(f"{API_URL}/ingest/notes", files=files)
            if response.status_code == 200:
                st.sidebar.success("Notes Ingested Successfully")
            else:
                st.sidebar.error("Notes Ingestion failed")
        else:
            st.sidebar.warning("Please upload the Notes file.")
elif ingest_type == "Website":
    website_url = st.sidebar.text_input("Enter Website URL")
    if st.sidebar.button("Ingest Website"):
        if website_url:
            response = requests.post(
                f"{API_URL}/ingest/website",
                json = {"url":website_url}
            )
            if response.status_code == 200:
                st.sidebar.success("Website Ingested successfully")
            else:
                st.sidebar.error("Website Ingestion Failed")
        else:
            st.sidebar.warning("Please enter a URL.")

st.divider()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


with st.form("chat_form",clear_on_submit= True):
    query = st.text_input("Your Question:")
    submitted = st.form_submit_button("Send")

# if submitted:

#         response = requests.post(
#             f"{API_URL}/chat",
#             json = {"query": query},
#             timeout = 300
#         )

#         if response.status_code == 200:
#             data = response.json()
#             st.session_state.chat_history.append(
#                 {
#                     "question":query,
#                     "answer":data.get("answer",""),
#                     "chunks":data.get("retrieved_chunks",[])
#                 }
#             )
#         else:
#             st.error("Error communicating with backend.")

if submitted:
    placeholder = st.empty()
    full_answer = ""

    response = requests.post(
        f"{API_URL}/chat-stream",
        json= {"query":query},
        stream = True
    )

    response.raise_for_status()

    for chunk in response.iter_content(chunk_size=1):
        if chunk:
            token = chunk.decode("utf-8")
            full_answer += token
            placeholder.markdown(full_answer)
    st.session_state.chat_history.append({
        "question": query,
        "answer": full_answer
    })

for chat in reversed(st.session_state.chat_history):
    st.markdown(f"**You:** {chat['question']}")
    st.markdown(f"**Assistant:** {chat['answer']}")
    st.markdown("---")

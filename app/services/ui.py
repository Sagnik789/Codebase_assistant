import streamlit as st
import requests

st.set_page_config(page_title="AI Codebase Assistant", layout="centered")

st.title("💻 AI Codebase Assistant")
st.caption("Ask questions about any indexed codebase")

API_URL = "http://127.0.0.1:8000/query"

# Chat history (session)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and "sources" in msg:
            with st.expander("📄 Sources"):
                for s in msg["sources"]:
                    st.code(s["text"][:300])


# Chat input
query = st.chat_input("Ask about the codebase...")

if query:
    # Show user message
    st.session_state.messages.append({
        "role": "user",
        "content": query
    })

    with st.chat_message("user"):
        st.markdown(query)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Analyzing code..."):
            try:
                response = requests.get(
                    API_URL,
                    params={"q": query},
                    timeout=400
                )

                data = response.json()

                answer = data.get("answer", "No answer found.")
                sources = data.get("sources", [])

            except Exception as e:
                answer = f"Error: {str(e)}"
                sources = []

        # Show answer
        st.markdown(answer)

        # Show sources
        if sources:
            with st.expander("📄 Sources"):
                for s in sources:
                    st.code(s["text"][:300])

    # Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })


# Clear chat button
if st.button("🗑 Clear Chat"):
    st.session_state.messages = []
    st.rerun()
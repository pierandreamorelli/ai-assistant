import streamlit as st
import time
import os
from openai import OpenAI

st.set_page_config(page_title="Sereno AI", page_icon="💬", layout="centered")

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY mancante nei secrets.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
if not ASSISTANT_ID:
    st.error("ASSISTANT_ID mancante nei secrets.")
    st.stop()

# App title
st.title("Sereno AI")
st.markdown("Chat con il tuo assistente personale.")

# Initialize session state for storing conversation
if "thread_id" not in st.session_state:
    # Create a new thread for this session
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
user_input = st.chat_input("Scrivi un messaggio qui...")

# Process user input
if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user message
    with st.chat_message("user"):
        st.write(user_input)

    try:
        # Add the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, role="user", content=user_input
        )

        # Create a run with the assistant
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id, assistant_id=ASSISTANT_ID
        )

        # Display assistant's "thinking" message
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.write("Sta scrivendo...")

            # Poll for the run to complete
            while run.status in ["queued", "in_progress"]:
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id, run_id=run.id
                )
                time.sleep(0.5)

            # Check if run was completed successfully
            if run.status == "completed":
                # Retrieve messages added by the assistant
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )

                # Get the latest message from the assistant
                for message in messages.data:
                    if message.role == "assistant" and message not in [
                        m["content"]
                        for m in st.session_state.messages
                        if m["role"] == "assistant"
                    ]:
                        assistant_response = message.content[0].text.value

                        # Update the placeholder with the assistant's response
                        message_placeholder.write(assistant_response)

                        # Add assistant message to chat history
                        st.session_state.messages.append(
                            {"role": "assistant", "content": assistant_response}
                        )
                        break
            else:
                error_message = f"Run ended with status: {run.status}"
                if run.status == "failed":
                    error_message += f"\nError: {run.last_error}"
                message_placeholder.error(error_message)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

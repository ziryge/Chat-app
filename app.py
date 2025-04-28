import streamlit as st
from datetime import datetime

# Streamlit app configuration
st.set_page_config(page_title="Chat App", layout="centered")

# Chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Chat interface
def display_chat():
    for message, sender, timestamp in st.session_state["messages"]:
        if sender == "user":
            st.markdown(f"**You:** {message} ({timestamp})")
        else:
            st.markdown(f"**Bot:** {message} ({timestamp})")

# Input form
def chat_input():
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your message:", key="input")
        submitted = st.form_submit_button("Send")
        if submitted and user_input:
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state["messages"].append((user_input, "user", timestamp))
            # Simulate bot reply
            st.session_state["messages"].append(("This is a reply!", "bot", timestamp))

# Main app
def main():
    st.title("Chat App")
    display_chat()
    chat_input()

if __name__ == "__main__":
    main()
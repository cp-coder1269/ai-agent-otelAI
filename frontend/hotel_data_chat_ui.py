import streamlit as st
import requests
import json
from typing import Generator
import time

# Page configuration
st.set_page_config(
    page_title="Hotel Data Analyzer Chatbot",
    page_icon="🏨",
    layout="centered"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "bearer_token" not in st.session_state:
    st.session_state.bearer_token = ""

def stream_chat_response(messages: list, bearer_token: str, backend_url: str) -> Generator[str, None, None]:
    """
    Stream chat response from the backend API
    """
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": messages
    }
    
    try:
        with requests.post(
            backend_url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=60
        ) as response:
            
            if response.status_code != 200:
                yield f"Error: {response.status_code} - {response.text}"
                return
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    
                    if data == "[DONE]":
                        break
                    elif data.startswith("ERROR:"):
                        yield data
                        break
                    else:
                        yield data
                        
    except requests.exceptions.RequestException as e:
        yield f"Connection error: {str(e)}"
    except Exception as e:
        yield f"Unexpected error: {str(e)}"

# App title and description
st.title("🏨 Hotel Data Analyzer Chatbot")
st.markdown("Chat with your hotel data analysis agent")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Backend URL input
    backend_url = st.text_input(
        "Backend URL",
        value="http://localhost:8000/api/v1/chat",
        help="Enter your backend API endpoint URL"
    )
    
    # Bearer token input
    bearer_token = st.text_input(
        "Bearer Token",
        type="password",
        value=st.session_state.bearer_token,
        help="Enter your authentication bearer token"
    )
    
    # Update session state
    st.session_state.bearer_token = bearer_token
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    # Connection status
    st.markdown("---")
    if bearer_token:
        st.success("✅ Token provided")
    else:
        st.warning("⚠️ No token provided")

# Main chat interface
st.markdown("---")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about your hotel data..."):
    # Check if bearer token is provided
    if not st.session_state.bearer_token:
        st.error("Please provide a bearer token in the sidebar first.")
        st.stop()
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Stream the response
            for chunk in stream_chat_response(
                st.session_state.messages, 
                st.session_state.bearer_token,
                backend_url
            ):
                if chunk.startswith("Error:") or chunk.startswith("Connection error:") or chunk.startswith("Unexpected error:"):
                    st.error(chunk)
                    break
                else:
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)  # Small delay for smooth streaming effect
            
            # Final response without cursor
            if full_response and not any(full_response.startswith(err) for err in ["Error:", "Connection error:", "Unexpected error:"]):
                message_placeholder.markdown(full_response)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Failed to get response: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666666;'>
        <small>Hotel Data Analyzer Chatbot • Powered by OpenAI Agents</small>
    </div>
    """, 
    unsafe_allow_html=True
)

# Usage instructions
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. **Configure your settings** in the sidebar:
       - Enter your backend API URL (default: `http://localhost:8000/api/v1/chat`)
       - Provide your bearer token for authentication
    
    2. **Start chatting** by typing your questions in the chat input below
    
    3. **Ask about your hotel data**, for example:
       - "Show me the occupancy rates for last month"
       - "What are the top performing hotels?"
       - "Analyze revenue trends by region"
    
    4. **Clear chat history** anytime using the button in the sidebar
    
    **Note:** Make sure your backend server is running and accessible at the specified URL.
    """)
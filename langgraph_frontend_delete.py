import streamlit as st
from langgraph_backend_delete import chatbot, retrieve_all_threads, delete_thread, get_thread_info
from langchain_core.messages import HumanMessage
import uuid

# **************************************** utility functions *************************

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def delete_chat_thread(thread_id):
    """Delete a specific chat thread"""
    if delete_thread(thread_id):
        # Remove from session state
        if thread_id in st.session_state['chat_threads']:
            st.session_state['chat_threads'].remove(thread_id)
        
        # If we're currently on this thread, start a new chat
        if st.session_state.get('thread_id') == thread_id:
            reset_chat()
        
        st.success(f"Chat deleted successfully!")
        st.rerun()
    else:
        st.error("Failed to delete chat")

# **************************************** Session Setup ******************************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])

# **************************************** Sidebar UI *********************************
st.sidebar.title('🤖 LangGraph Chatbot')

# New Chat button
if st.sidebar.button('➕ New Chat', use_container_width=True):
    reset_chat()

st.sidebar.header('💬 My Conversations')

# Display chat threads
if st.session_state['chat_threads']:
    for thread_id in st.session_state['chat_threads'][::-1]:
        thread_info = get_thread_info(thread_id)
        
        if thread_info:
            topic = thread_info['topic']
            message_count = thread_info['message_count']
            
            # Create two columns: chat button and delete button
            col1, col2 = st.sidebar.columns([4, 1])
            
            with col1:
                if st.button(f"📝 {topic}", key=f"chat_{thread_id}", help=f"{message_count} messages"):
                    st.session_state['thread_id'] = thread_id
                    temp_messages = []
                    for msg in thread_info['messages']:
                        if isinstance(msg, HumanMessage):
                            role = 'user'
                        else:
                            role = 'assistant'
                        temp_messages.append({'role': role, 'content': msg.content})
                    st.session_state['message_history'] = temp_messages
                    st.rerun()
            
            with col2:
                if st.button('🗑️', key=f"del_{thread_id}", help='Delete this chat'):
                    delete_chat_thread(thread_id)
else:
    st.sidebar.write("No conversations yet. Start chatting!")

# Show current thread info
if st.session_state.get('thread_id'):
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Current thread: {str(st.session_state['thread_id'])[:8]}...")

# **************************************** Main UI ************************************

# Display chat history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# Chat input
user_input = st.chat_input('Type here')

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
    
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}
    
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )
    
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
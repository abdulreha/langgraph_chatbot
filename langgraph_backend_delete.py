from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
# Checkpointer
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    
    return list(all_threads)

def delete_thread(thread_id):
    """
    Delete a specific thread from the database
    """
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (str(thread_id),))
        conn.commit()
        print(f"Thread {thread_id} deleted successfully")
        return True
        
    except sqlite3.Error as e:
        print(f"Error deleting thread {thread_id}: {e}")
        conn.rollback()
        return False

def get_thread_info(thread_id):
    """
    Get information about a specific thread
    """
    try:
        state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
        messages = state.values.get('messages', [])
        
        if messages:
            # Get first user message for topic
            topic = str(thread_id)
            message_count = len(messages)
            
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    topic = msg.content[:30] + ("..." if len(msg.content) > 30 else "")
                    break
                    
            return {
                'thread_id': thread_id,
                'topic': topic,
                'message_count': message_count,
                'messages': messages
            }
        return None
        
    except Exception as e:
        print(f"Error getting thread info for {thread_id}: {e}")
        return None
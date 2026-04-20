import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

# Initialize the LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# Chat history to maintain conversation context
chat_history = [
    SystemMessage(content="You are a helpful assistant. Answer clearly and concisely.")
]

print("🤖 Chatbot ready! Type 'quit' to exit.\n")

while True:
    user_input = input("You: ").strip()

    if not user_input:
        continue

    if user_input.lower() in ["quit", "exit", "bye"]:
        print("Bot: Goodbye! 👋")
        break

    # Add user message to history
    chat_history.append(HumanMessage(content=user_input))

    # Get response from LLM
    response = llm.invoke(chat_history)

    # Add AI response to history
    chat_history.append(AIMessage(content=response.content))

    print(f"Bot: {response.content}\n")
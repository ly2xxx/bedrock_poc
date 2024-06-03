import streamlit as st
import boto3
import json
import os
from querycsv_lang2 import query_csv

# CSS for the chat interface and responses
st.markdown('''
<style>
.chat-message {padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex}
.chat-message.user {background-color: #2b313e}
.chat-message.bot {background-color: #475063}
.chat-message .avatar {width: 20%}
.chat-message .avatar img {max-width: 78px; max-height: 78px; border-radius: 50%; object-fit: cover}
.chat-message .message {width: 80%; padding: 0 1.5rem; color: #fff}
.response, .url {padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;}
</style>
''', unsafe_allow_html=True)

# Message templates
bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://i.ibb.co/wRtZstJ/Aurora.png">
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''

st.title("Chat with CSV File")

session = boto3.session.Session()
region_name = session.region_name
bedrock_client = boto3.client('bedrock-agent-runtime')

# Initialize conversation history if not present
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

user_input = st.text_input("You: ")

if st.button("Send") :

    csv_file_name = "claimdata.csv"
    response = query_csv(f"SampleData/{csv_file_name}",user_input,st.session_state.conversation_history)

    print("Response is : " + response)

    display_text =  response

    # Insert the response at the beginning of the conversation history
    st.session_state.conversation_history.insert(0, ("Assistant", f"<div class='response'>{display_text}</div>"))
    st.session_state.conversation_history.insert(0, ("You", user_input))

    # Display conversation history
    for speaker, text in st.session_state.conversation_history:
        if speaker == "You":
            st.markdown(user_template.replace("{{MSG}}", text), unsafe_allow_html=True)
        else:
            st.markdown(bot_template.replace("{{MSG}}", text), unsafe_allow_html=True)

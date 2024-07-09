from llama_index.llms.openai import OpenAI as OpenAI_llama
from llama_index.core.base.response.schema import StreamingResponse
from openai import OpenAI, Stream
import re
import asyncio
import streamlit as st

client = OpenAI(api_key=st.secrets['OPEN_AI_KEY'])

awaiting_response_html = """
<style>
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.9; }
    100% { opacity: 1; }
}
.loading-placeholder {
    background-color: #1a1c24;
    color: white;
    padding: 10px;
    font-family: monospace;
    overflow: auto;
    animation: pulse 1.5s infinite ease-in-out;
    min-height:300px
}
.loading-text {
    width: 100%;
    height: 20px;
    background: rgba(255, 255, 255, 0.1);
    margin-bottom: 10px;
    border-radius: 4px;
}
.loading-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    display: inline-block;
    vertical-align: middle;
    margin-right: 10px;
    margin-bottom:10px;
}
body{
margin:0px !important;
}
</style>
<div class="loading-placeholder">
    <div class="loading-avatar"></div>
    <div class="loading-text" style="width: 30%;"></div>
    <div class="loading-text" style="width: 80%;"></div>
    <div class="loading-text" style="width: 60%;"></div>
    <div class="loading-text" style="width: 50%;"></div>
    <div class="loading-text" style="width: 90%;"></div>
</div>
"""

# General purpose function for rendering a text area - write a separation function is a bespoke logic is needed
def render_text_area(container, label, stream):

    chunk_counter = 0
    cumul_response = ''

    # Generate text area
    if isinstance(stream, str):
        cumul_response = stream
        container.text_area(
            label=label, 
            label_visibility='collapsed', 
            value=re.sub(r'\*\*|\*|_|`|#', '', cumul_response), 
            key=label,
            height=400
        )

    # streaming response - OpenAI
    elif isinstance(stream, Stream):
        for chunk in stream:
            chunk_counter += 1
            content = chunk.choices[0].delta.content or ""
            unique_key = f"{label}_cumul_response_{chunk_counter}"
            cumul_response += content
            container.text_area(
                label=label, 
                label_visibility='collapsed', 
                value=re.sub(r'\*\*|\*|_|`|#', '', cumul_response), 
                key=unique_key, 
                height=400
            )

    # streaming response - llama_index
    elif isinstance(stream, StreamingResponse):
        for chunk in stream.response_gen:
            chunk_counter += 1
            unique_key = f"{label}_cumul_response_{chunk_counter}"
            cumul_response += chunk
            container.text_area(
                label=label, 
                label_visibility='collapsed', 
                value=re.sub(r'\*\*|\*|_|`|#', '', cumul_response), 
                key=unique_key, 
                height=400
            )
            
    return cumul_response



async def call_llm_agent(
        user_query: str, 
        chat_response_container = None, 
        run_status_element = None,
        return_stream = True
    ):

    if run_status_element:
        run_status_element.code('Agent is producing appropriate response', language="plaintext")

    response_stream = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": user_query}
            ],
            stream=True,
            temperature=0.1 # medium temperature for this mode
        )

    # ticker dashboard
    if return_stream:
        output_dict = {
            'agent_response': response_stream
        }
        return output_dict
    

# print(asyncio.run(call_llm_agent(user_query="Write me a short poem?")))
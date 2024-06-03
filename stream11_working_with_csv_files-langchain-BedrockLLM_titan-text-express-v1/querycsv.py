import boto3
import pprint
from botocore.client import Config
import json
import argparse
import pandas as pd
import re
import sys
from io import StringIO
import contextlib
from contextlib import redirect_stdout


pp = pprint.PrettyPrinter(indent=4)

def get_bedrock_client():
    session = boto3.session.Session()
    region = session.region_name
    bedrock_config = Config(connect_timeout=120, read_timeout=120, retries={'max_attempts': 0})
    bedrock_client = boto3.client('bedrock-runtime', 
                                  region_name = region)
    
    return bedrock_client

def invoke_claude_llm(bedrock_client,
                      messages,
                      modelId ='anthropic.claude-instant-v1',
                      accept = 'application/json',
                      contentType = 'application/json',
                      max_tokens = 4096,
                      temperature = 0,
                     ):

    payload = json.dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": max_tokens,
    "temperature": temperature,
    "top_p": 0,
    "messages": messages})
    
    response = bedrock_client.invoke_model(
        body=payload, 
        modelId=modelId, 
        accept=accept, 
        contentType=contentType)
    
    response_body = json.loads(response.get('body').read())
    response_text = response_body.get('content')
    
    return response_text

def get_text_payload(text=None):
    content=None
    if text.strip():
        content = {
        "type":"text",
        "text": text.strip()
        }
    return content

def create_claude_message(prompt):
    
    messages = [
                { "role":"user", 
                  "content":prompt
                }]
    return messages

bedrock_client = get_bedrock_client()

SystemPromptTemplate = """
<Instructions>
You are an expert programmer in Python and use the Pandas library to create programs to process CSV files and extract the data corresponding to user question. You can only answer with an executable Python program which you always put inside the tags <code></code>. 
Avoid comments and do not explain the code. The output of the program should be human readable and using markdown formatting when possible.

You have been give data in the file {file} with the following fields: {fields}

Answer the <question> using the data provided in above file  

</Instructions>

<question>
{question}
</question>
"""

def gen_program(csvfile, question, history=""):

    data = pd.read_csv(csvfile).sample(n=10)

    fdata = data.dtypes.to_string()
    fdata = fdata.replace("object", "str")
    fdata = fdata + "\n" + data.head(2).to_string()
    
    prompt = SystemPromptTemplate.format( 
                                            file=csvfile,
                                            # fields="\n".join(list(data.columns)),
                                            fields="\n" + fdata,
                                            question= question
                                        )
    
    prompt = prompt + "\n Please consider following chat history for the context : " + "\n" + str(history)
                            
    messages = create_claude_message(prompt)
    resp = invoke_claude_llm(bedrock_client,messages)
    resp = resp[0]['text']
    
    return f'```py\n{re.search(r"<code>(.*)</code>", resp, re.MULTILINE | re.DOTALL).groups(0)[0]}\n```'
    
def query_csv(csvfile, question, history=""):
    pythoncode = gen_program(csvfile, question, history)
    pythoncode = "\n".join(pythoncode.split("\n")[1:-1])

    print("### Pythoncode ##")
    print(pythoncode)

    print("### LLM Response ##")
    content = "Sorry, I have not been able to answer your question. Would you mind trying again?"

    try:
        stdout = StringIO()
        _locals = locals()
        with redirect_stdout(stdout):
           exec(pythoncode, globals(), _locals)
        content = stdout.getvalue()

    except Exception as ex:
        print(ex)

    return content


if __name__ == "__main__":
    # Accept the argument from command line
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True)
    parser.add_argument("--question", type=str, default="How Many Rows are there?")
    
    args = parser.parse_args()
    
    if args.file:
        csvfile = args.file
    if args.question:
        question = args.question
    
    content = query_csv(csvfile, question)
    print(content)

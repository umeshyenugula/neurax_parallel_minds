import os

from groq import Groq

client = Groq(
    api_key="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",
)

def parsing(text):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"I will you give a text return single text file consisting of location ,stone size as width * height ,no of stones {text} dont generate anything other than this only a single line, if findings is message no stones are found give me 0 0 0",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    result=chat_completion.choices[0].message.content
    return result
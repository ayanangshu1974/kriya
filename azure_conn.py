

import os
from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()

endpoint = "https://cog-ai-kriya-eus-dev.cognitiveservices.azure.com/"
model_name = "gpt-4o-mini"
deployment = "gpt-4o-mini"

subscription_key = os.getenv("AZURE_API_KEY")
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "Create a Python application that can read data from the kaggle, download housing data, and create a chain of services that can take information from different topics related to this, process null values by removing them, and create a csv report.",
        }
    ],
    max_tokens=4096,
    temperature=1.0,
    top_p=1.0,
    model=deployment
)

print(response.choices[0].message.content)
# Save as test.py and run: python test.py

import os
import sys

# Auto-load variables from .env if present (override system defaults like localhost:8000)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("export "):
                line = line[7:]
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                os.environ[k] = v

import anthropic

api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_BASE_URL", "https://bedrock-mantle.us-east-1.api.aws/anthropic")
workspace_id = os.getenv("ANTHROPIC_WORKSPACE_ID", "default")

client = anthropic.Anthropic(
    api_key=api_key,
    base_url=base_url,
    default_headers={"anthropic-workspace-id": workspace_id} if workspace_id else {},
)

try:
    message = client.messages.create(
        model="anthropic.claude-haiku-4-5",
        max_tokens=64,
        messages=[{"role": "user", "content": "What is Amazon Bedrock?"}],
    )
    print(message.content[0].text)
except Exception as e:
    print(f"Error: {e}")
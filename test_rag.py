import requests
import json

response = requests.post(
    "http://localhost:8000/api/v1/chat/query",
    json={"query": "find me a java developer"},
    headers={"Content-Type": "application/json"}
)

print(json.dumps(response.json(), indent=2))

import json
import urllib.request

payload = {
    "model": "llama3",
    "messages": [{"role": "user", "content": "hi"}],
    "stream": True
}
request = urllib.request.Request(
    url="http://localhost:11434/api/chat",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

print("Contacting Ollama...")
try:
    with urllib.request.urlopen(request, timeout=10) as response:
        print("Response received. Reading lines...")
        while True:
            line = response.readline()
            if not line:
                print("End of stream.")
                break
            chunk = json.loads(line.decode("utf-8"))
            content = chunk.get("message", {}).get("content", "")
            if content:
                print(content, end="", flush=True)
except Exception as e:
    print(f"\nError: {e}")

import json
import urllib.request

try:
    with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
        print("Models list:")
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error fetching tags: {e}")

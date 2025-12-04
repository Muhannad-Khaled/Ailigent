"""Test script for Ailigent APIs."""
import urllib.request
import urllib.error
import json

def test_endpoint(url, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode()
        return {"status": resp.status, "data": json.loads(data) if data else None}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": e.reason}
    except urllib.error.URLError as e:
        return {"status": "error", "error": str(e.reason)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Test all services
services = [
    ("Employee Agent", "http://127.0.0.1:8000/api/v1/health"),
    ("Contracts Agent", "http://127.0.0.1:8001/api/v1/health"),
    ("HR Agent", "http://127.0.0.1:8002/api/v1/health"),
    ("Task Management", "http://127.0.0.1:8003/api/v1/health"),
]

print("=" * 60)
print("Testing Ailigent Services Health Endpoints")
print("=" * 60)

for name, url in services:
    result = test_endpoint(url)
    status = "OK" if result.get("status") == 200 else "FAIL"
    print(f"\n{name}: {status}")
    print(f"  URL: {url}")
    print(f"  Result: {result}")

# Test HR Jobs API
print("\n" + "=" * 60)
print("Testing HR Agent Jobs Endpoint")
print("=" * 60)
headers = {"X-API-Key": "ailigent-hr-api-key-2024"}
result = test_endpoint("http://127.0.0.1:8002/api/v1/recruitment/jobs", headers)
print(f"HR Jobs API: {result}")

# Test Task Management Tasks API
print("\n" + "=" * 60)
print("Testing Task Management Tasks Endpoint")
print("=" * 60)
headers = {"X-API-Key": "ailigent-task-api-key-2024"}
result = test_endpoint("http://127.0.0.1:8003/api/v1/tasks", headers)
print(f"Tasks API: {result}")

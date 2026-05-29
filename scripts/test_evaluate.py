import urllib.request
import json
import sys

def main():
    moodle_url = "http://localhost:8080/local/rubricai/ajax_course_data.php?course_id=8"
    print(f"Fetching course data from: {moodle_url}...")
    try:
        req = urllib.request.urlopen(moodle_url)
        course_data = json.loads(req.read().decode('utf-8'))
        print("Successfully fetched course data.")
    except Exception as e:
        print(f"Error fetching course data: {e}")
        sys.exit(1)

    evaluate_payload = {
        "course_id": 8,
        "rubric_id": "rubric_calidad_moodle",
        "course_data": course_data
    }

    api_url = "http://localhost:8000/evaluate"
    print(f"Sending evaluation request to: {api_url}...")
    
    req_api = urllib.request.Request(
        api_url, 
        data=json.dumps(evaluate_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        res = urllib.request.urlopen(req_api, timeout=120)
        result = json.loads(res.read().decode('utf-8'))
        print("\n=== EVALUATION RESULTS ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error running evaluation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

import requests
import json
import pandas as pd
import matplotlib.pyplot as plt

def load_test_cases(file_path):
    try:
        test_cases_df = pd.read_csv(file_path)
        test_cases = test_cases_df.to_dict(orient='records')
        print(f"Loaded {len(test_cases)} test cases.")
        return test_cases
    except Exception as e:
        print(f"Error loading test cases: {e}")
        return []

def test_app():
    url = 'http://127.0.0.1:5000/process_order'
    test_cases = load_test_cases('test_cases.csv')

    def normalize_string(s):
        return ''.join(s.split())

    results = []
    for case in test_cases:
        try:
            response = requests.post(url, data={'order': case["input"]}, timeout=10)  # Extended timeout to 10 seconds
            actual_output = response.text.strip()
            passed = normalize_string(actual_output) == normalize_string(case["expected_output"])
            results.append({
                "input": case["input"],
                "expected_output": case["expected_output"],
                "actual_output": actual_output,
                "passed": passed
            })
        except requests.exceptions.RequestException as e:
            # Retry once in case of timeout or other request exception
            try:
                response = requests.post(url, data={'order': case["input"]}, timeout=10)
                actual_output = response.text.strip()
                passed = normalize_string(actual_output) == normalize_string(case["expected_output"])
                results.append({
                    "input": case["input"],
                    "expected_output": case["expected_output"],
                    "actual_output": actual_output,
                    "passed": passed
                })
            except requests.exceptions.RequestException as e:
                results.append({
                    "input": case["input"],
                    "expected_output": case["expected_output"],
                    "actual_output": str(e),
                    "passed": False
                })

    results_df = pd.DataFrame(results)
    results_df.to_csv('test_results.csv', index=False)

    # Plot results
    passed_tests = results_df[results_df['passed']].shape[0]
    failed_tests = results_df[~results_df['passed']].shape[0]

    plt.bar(['Passed', 'Failed'], [passed_tests, failed_tests], color=['green', 'red'])
    plt.xlabel('Test Results')
    plt.ylabel('Number of Tests')
    plt.title('Test Results Summary')
    plt.savefig('test_results_summary.png')
    plt.close()  # Close the plot to avoid hanging

    print(results_df)
    return results_df

if __name__ == "__main__":
    test_app()

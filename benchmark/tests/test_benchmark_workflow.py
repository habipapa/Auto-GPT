import pytest
import requests

URL_BENCHMARK = "http://localhost:8080/ap/v1"
URL_AGENT = "http://localhost:8000/ap/v1"

import datetime
import time


@pytest.mark.parametrize(
    "eval_id, input_text, expected_artifact_length, test_name, should_be_successful",
    [
        (
            "81b64bf9-2b6a-4ac8-bcd2-8bfe36244ac0",
            "Write the word 'Washington' to a .txt file",
            0,
            "WriteFile",
            True,
        ),
        (
            "261ccfaa-02a2-4c1a-8a56-c76c66f7dba1",
            "Read the file called file_to_read.txt and write its content to a file called output.txt",
            1,
            "ReadFile",
            False,
        ),
    ],
)
def test_entire_workflow(
    eval_id, input_text, expected_artifact_length, test_name, should_be_successful
):
    task_request = {"eval_id": eval_id, "input": input_text}

    # First POST request
    task_response_benchmark = requests.post(
        URL_BENCHMARK + "/agent/tasks", json=task_request
    )
    timestamp_after_task_eval_created = datetime.datetime.now(datetime.timezone.utc)
    time.sleep(1.1)  # To make sure the 2 timestamps to compare are different
    assert task_response_benchmark.status_code == 200
    task_response_benchmark = task_response_benchmark.json()
    assert task_response_benchmark["input"] == input_text

    task_response_benchmark_id = task_response_benchmark["task_id"]

    response_task_agent = requests.get(
        f"{URL_AGENT}/agent/tasks/{task_response_benchmark_id}"
    )
    assert response_task_agent.status_code == 200
    response_task_agent = response_task_agent.json()
    assert len(response_task_agent["artifacts"]) == expected_artifact_length

    step_request = {"input": input_text}

    step_response = requests.post(
        URL_BENCHMARK + "/agent/tasks/" + task_response_benchmark_id + "/steps",
        json=step_request,
    )
    assert step_response.status_code == 200
    step_response = step_response.json()
    assert step_response["is_last"] == True  # Assuming is_last is always True

    step_response = requests.post(
        URL_BENCHMARK + "/agent/tasks/" + task_response_benchmark_id + "/evaluation",
        json={},
    )

    step_response = requests.post(
        URL_BENCHMARK + "/agent/tasks/" + task_response_benchmark_id + "/steps",
        json=step_request,
    )
    assert step_response.status_code == 200
    step_response = step_response.json()
    assert step_response["is_last"] == True  # Assuming is_last is always True

    eval_response = requests.post(
        URL_BENCHMARK + "/agent/tasks/" + task_response_benchmark_id + "/evaluations",
        json={},
    )
    assert eval_response.status_code == 200
    eval_response = eval_response.json()
    print("eval_response")
    print(eval_response)
    assert eval_response["run_details"]["test_name"] == test_name
    assert eval_response["metrics"]["success"] == should_be_successful
    benchmark_start_time = datetime.datetime.fromisoformat(
        eval_response["run_details"]["benchmark_start_time"]
    )
    print(benchmark_start_time, timestamp_after_task_eval_created)
    test = timestamp_after_task_eval_created - benchmark_start_time
    print(test)
    assert benchmark_start_time < timestamp_after_task_eval_created

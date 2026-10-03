import json
import random
from pathlib import Path


FIXTURE_DIR = Path("fixtures")

NODE_TYPES = [
    "image_generation",
    "t2v",
    "i2v",
    "qa",
    "montage",
    "render"
]

RETRYABLE_FAILURES = [
    "timeout",
    "network_error",
    "temporary_server_error",
    "rate_limit"
]

TERMINAL_FAILURES = [
    "authentication_error",
    "invalid_input",
    "unsupported_model",
    "invalid_configuration"
]


def create_node(node_id, node_type, depends_on=None):
    return {
        "id": node_id,
        "type": node_type,
        "depends_on": depends_on or [],
        "status": "PENDING",
        "failure_reason": None,
        "retry_count": 0,
        "max_retries": 2
    }


def normal_blueprint(number):
    nodes = [
        create_node("T1", "image_generation"),
        create_node("T2", "i2v", ["T1"]),
        create_node("T3", "qa", ["T2"]),
        create_node("T4", "montage", ["T3"]),
        create_node("T5", "render", ["T4"])
    ]

    return {
        "blueprint_id": f"BP{number:03d}",
        "fixture_type": "normal",
        "nodes": nodes
    }


def parallel_blueprint(number):
    nodes = [
        create_node("T1", "image_generation"),
        create_node("T2", "t2v", ["T1"]),
        create_node("T3", "i2v", ["T1"]),
        create_node("T4", "qa", ["T2", "T3"]),
        create_node("T5", "montage", ["T4"]),
        create_node("T6", "render", ["T5"])
    ]

    return {
        "blueprint_id": f"BP{number:03d}",
        "fixture_type": "parallel",
        "nodes": nodes
    }


def retryable_failure_blueprint(number):
    nodes = [
        create_node("T1", "image_generation"),
        create_node("T2", "i2v", ["T1"]),
        create_node("T3", "qa", ["T2"]),
        create_node("T4", "montage", ["T3"]),
        create_node("T5", "render", ["T4"])
    ]

    failed_node = random.choice(nodes[1:])

    failed_node["status"] = "FAILED"
    failed_node["failure_reason"] = random.choice(RETRYABLE_FAILURES)

    return {
        "blueprint_id": f"BP{number:03d}",
        "fixture_type": "retryable_failure",
        "nodes": nodes
    }


def terminal_failure_blueprint(number):
    nodes = [
        create_node("T1", "image_generation"),
        create_node("T2", "i2v", ["T1"]),
        create_node("T3", "qa", ["T2"]),
        create_node("T4", "montage", ["T3"]),
        create_node("T5", "render", ["T4"])
    ]

    failed_node = random.choice(nodes[1:])

    failed_node["status"] = "FAILED"
    failed_node["failure_reason"] = random.choice(TERMINAL_FAILURES)

    return {
        "blueprint_id": f"BP{number:03d}",
        "fixture_type": "terminal_failure",
        "nodes": nodes
    }


def missing_dependency_blueprint(number):
    nodes = [
        create_node("T1", "image_generation"),
        create_node("T2", "i2v", ["T99"]),
        create_node("T3", "qa", ["T2"]),
        create_node("T4", "render", ["T3"])
    ]

    return {
        "blueprint_id": f"BP{number:03d}",
        "fixture_type": "missing_dependency",
        "nodes": nodes
    }


def cycle_blueprint(number):
    nodes = [
        create_node("T1", "image_generation", ["T3"]),
        create_node("T2", "i2v", ["T1"]),
        create_node("T3", "qa", ["T2"])
    ]

    return {
        "blueprint_id": f"BP{number:03d}",
        "fixture_type": "cycle",
        "nodes": nodes
    }


def qa_failure_blueprint(number):
    nodes = [
        create_node("T1", "image_generation"),
        create_node("T2", "i2v", ["T1"]),
        create_node("T3", "qa", ["T2"]),
        create_node("T4", "montage", ["T3"]),
        create_node("T5", "render", ["T4"])
    ]

    qa_node = nodes[2]

    qa_node["status"] = "FAILED"
    qa_node["failure_reason"] = "quality_failure"

    return {
        "blueprint_id": f"BP{number:03d}",
        "fixture_type": "qa_failure",
        "nodes": nodes
    }


def save_fixture(data):
    filename = FIXTURE_DIR / f"{data['blueprint_id']}.json"

    with open(filename, "w") as file:
        json.dump(data, file, indent=2)


def generate_fixtures():
    FIXTURE_DIR.mkdir(exist_ok=True)

    number = 1

    for _ in range(15):
        save_fixture(normal_blueprint(number))
        number += 1

    for _ in range(8):
        save_fixture(parallel_blueprint(number))
        number += 1

    for _ in range(8):
        save_fixture(retryable_failure_blueprint(number))
        number += 1

    for _ in range(6):
        save_fixture(terminal_failure_blueprint(number))
        number += 1

    for _ in range(5):
        save_fixture(missing_dependency_blueprint(number))
        number += 1

    for _ in range(4):
        save_fixture(cycle_blueprint(number))
        number += 1

    for _ in range(4):
        save_fixture(qa_failure_blueprint(number))
        number += 1

    print("Fixture generation completed.")
    print(f"Total fixtures created: {number - 1}")


if __name__ == "__main__":
    generate_fixtures()
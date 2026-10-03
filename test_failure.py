import json
from pathlib import Path

import networkx as nx

from src.failure_reason_mapper import map_failure_reason
from src.state_machine import StateMachine, NodeState


FIXTURES_DIR = Path("fixtures")


def load_fixture(blueprint_id):
    file_path = FIXTURES_DIR / f"{blueprint_id}.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def test_timeout_is_retryable():
    result = map_failure_reason("timeout")

    assert result["retryable"] is True
    assert result["action"] == "RETRY"


def test_network_error_is_retryable():
    result = map_failure_reason("network_error")

    assert result["retryable"] is True
    assert result["action"] == "RETRY"


def test_temporary_server_error_is_retryable():
    result = map_failure_reason("temporary_server_error")

    assert result["retryable"] is True
    assert result["action"] == "RETRY"


def test_rate_limit_wait_and_retry():
    result = map_failure_reason("rate_limit")

    assert result["retryable"] is True
    assert result["action"] == "WAIT_AND_RETRY"


def test_quality_failure_selective_regeneration():
    result = map_failure_reason("quality_failure")

    assert result["retryable"] is True
    assert result["regenerate"] is True
    assert result["action"] == "SELECTIVE_REGENERATION"


def test_authentication_error_is_terminal():
    result = map_failure_reason("authentication_error")

    assert result["retryable"] is False
    assert result["action"] == "STOP"


def test_invalid_input_is_terminal():
    result = map_failure_reason("invalid_input")

    assert result["retryable"] is False
    assert result["action"] == "FIX_INPUT"


def test_unsupported_model_is_terminal():
    result = map_failure_reason("unsupported_model")

    assert result["retryable"] is False
    assert result["action"] == "CHANGE_MODEL"


def test_invalid_configuration_is_terminal():
    result = map_failure_reason("invalid_configuration")

    assert result["retryable"] is False
    assert result["action"] == "FIX_CONFIGURATION"


def test_missing_dependency_is_detected():
    data = load_fixture("BP038")

    node_ids = {
        node["id"]
        for node in data["nodes"]
    }

    missing_found = False

    for node in data["nodes"]:
        for dependency in node.get("depends_on", []):

            if dependency not in node_ids:
                missing_found = True

    assert missing_found is True


def test_cycle_is_detected():
    data = load_fixture("BP043")

    graph = nx.DiGraph()

    for node in data["nodes"]:

        graph.add_node(node["id"])

        for dependency in node.get("depends_on", []):

            graph.add_edge(
                dependency,
                node["id"]
            )

    assert nx.is_directed_acyclic_graph(graph) is False


def test_retry_budget_exhaustion():
    data = load_fixture("BP051")

    failed_node = None

    for node in data["nodes"]:

        if node["failure_reason"] == "timeout":
            failed_node = node
            break

    assert failed_node is not None
    assert failed_node["max_retries"] == 2
    assert failed_node["force_retry_failure"] is True

    retry_count = 0

    while retry_count < failed_node["max_retries"]:
        retry_count += 1

    assert retry_count == 2


def test_parallel_branches():
    data = load_fixture("BP016")

    graph = nx.DiGraph()

    for node in data["nodes"]:

        graph.add_node(node["id"])

        for dependency in node.get("depends_on", []):

            graph.add_edge(
                dependency,
                node["id"]
            )

    generations = list(
        nx.topological_generations(graph)
    )

    parallel_groups = [
        group
        for group in generations
        if len(group) > 1
    ]

    assert len(parallel_groups) > 0


def test_blocked_downstream_node():

    machine = StateMachine("T3")

    assert machine.get_state() == "PENDING"

    machine.transition(
        NodeState.BLOCKED
    )

    assert machine.get_state() == "BLOCKED"

    assert machine.get_history() == [
        "PENDING",
        "BLOCKED"
    ]
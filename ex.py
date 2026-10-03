import json
from pathlib import Path

import networkx as nx

from state_machine import StateMachine, NodeState


FIXTURES_DIR = Path("fixtures")
OUTPUT_DIR = Path("output/results")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


RETRYABLE_FAILURES = {
    "timeout",
    "network_error",
    "temporary_server_error",
    "rate_limit",
    "quality_failure"
}


TERMINAL_FAILURES = {
    "authentication_error",
    "invalid_input",
    "unsupported_model",
    "invalid_configuration"
}


def load_blueprint(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_graph(blueprint):
    graph = nx.DiGraph()
    node_ids = set()

    for node in blueprint["nodes"]:
        node_id = node["id"]

        graph.add_node(
            node_id,
            data=node
        )

        node_ids.add(node_id)

    missing_dependencies = []

    for node in blueprint["nodes"]:
        node_id = node["id"]

        for dependency in node.get("depends_on", []):
            if dependency not in node_ids:
                missing_dependencies.append({
                    "node": node_id,
                    "missing_dependency": dependency
                })

            graph.add_edge(
                dependency,
                node_id
            )

    return graph, missing_dependencies


def is_retryable(reason):
    return reason in RETRYABLE_FAILURES


def is_terminal(reason):
    return reason in TERMINAL_FAILURES


def initialize_state_machine(node):
    machine = StateMachine(node["id"])
    node["state_history"] = machine.get_history()
    return machine


def mark_blocked(node):
    machine = StateMachine(node["id"])

    machine.transition(NodeState.BLOCKED)

    node["status"] = "BLOCKED"
    node["state_history"] = machine.get_history()

    print(f'{node["id"]} → BLOCKED')


def execute_node(node):

    node_id = node["id"]
    node_type = node["type"]

    machine = initialize_state_machine(node)

    print()
    print("-" * 60)
    print(f"Executing {node_id} ({node_type})")

    machine.transition(NodeState.READY)

    node["status"] = "READY"

    print(f"{node_id} → READY")

    machine.transition(NodeState.RUNNING)

    node["status"] = "RUNNING"

    print(f"{node_id} → RUNNING")

    reason = node.get("failure_reason")

    if reason is None:

        machine.transition(NodeState.SUCCESS)

        node["status"] = "SUCCESS"
        node["failure_reason"] = None
        node["state_history"] = machine.get_history()

        print(f"{node_id} → SUCCESS")

        return "SUCCESS"

    machine.transition(NodeState.FAILED)

    node["status"] = "FAILED"
    node["state_history"] = machine.get_history()

    print(f"{node_id} → FAILED")
    print(f"Failure reason: {reason}")

    if is_retryable(reason):

        print("Retryable: YES")

        max_retries = node.get("max_retries", 2)

        while node["retry_count"] < max_retries:

            node["retry_count"] += 1

            print(
                f'Retry {node["retry_count"]} '
                f'of {max_retries}'
            )

            machine.transition(NodeState.RETRYING)

            node["status"] = "RETRYING"

            print(f"{node_id} → RETRYING")

            if node.get("force_retry_failure", False):

                machine.transition(NodeState.RUNNING)

                node["status"] = "RUNNING"

                print(f"{node_id} → RUNNING")

                machine.transition(NodeState.FAILED)

                node["status"] = "FAILED"

                print("Retry result: FAILED")

                continue

            machine.transition(NodeState.RUNNING)

            node["status"] = "RUNNING"

            print(f"{node_id} → RUNNING")

            machine.transition(NodeState.SUCCESS)

            node["status"] = "SUCCESS"
            node["failure_reason"] = None
            node["state_history"] = machine.get_history()

            print("Retry result: SUCCESS")
            print(f"{node_id} → SUCCESS")

            return "SUCCESS"

        node["status"] = "FAILED"
        node["state_history"] = machine.get_history()

        print("Retry budget exhausted.")

        return "STOP"

    if is_terminal(reason):

        print("Retryable: NO")

        machine.transition(NodeState.ABORTED)

        node["status"] = "ABORTED"
        node["state_history"] = machine.get_history()

        print(f"{node_id} → ABORTED")

        return "STOP"

    print("Unknown failure reason.")

    machine.transition(NodeState.ABORTED)

    node["status"] = "ABORTED"
    node["state_history"] = machine.get_history()

    print(f"{node_id} → ABORTED")

    return "STOP"


def dependencies_successful(node, nodes_by_id):

    for dependency in node.get("depends_on", []):

        dependency_node = nodes_by_id.get(dependency)

        if dependency_node is None:
            return False

        if dependency_node.get("status") != "SUCCESS":
            return False

    return True


def process_blueprint(file_path):

    blueprint = load_blueprint(file_path)

    blueprint_id = blueprint.get(
        "blueprint_id",
        file_path.stem
    )

    fixture_type = blueprint.get(
        "fixture_type",
        "unknown"
    )

    print()
    print("=" * 60)
    print(f"BLUEPRINT: {blueprint_id}")
    print(f"Fixture type: {fixture_type}")
    print("=" * 60)

    graph, missing_dependencies = build_graph(blueprint)

    if missing_dependencies:

        print()
        print("INVALID DEPENDENCY")

        for item in missing_dependencies:
            print(
                f'Node {item["node"]} '
                f'has missing dependency '
                f'{item["missing_dependency"]}'
            )

        return {
            "blueprint_id": blueprint_id,
            "fixture_type": fixture_type,
            "status": "INVALID_DEPENDENCY",
            "execution_order": [],
            "nodes": blueprint["nodes"]
        }

    if not nx.is_directed_acyclic_graph(graph):

        print()
        print("CYCLE DETECTED")

        return {
            "blueprint_id": blueprint_id,
            "fixture_type": fixture_type,
            "status": "CYCLE_DETECTED",
            "execution_order": [],
            "nodes": blueprint["nodes"]
        }

    execution_order = list(
        nx.topological_sort(graph)
    )

    print()
    print("Execution order:")
    print(" → ".join(execution_order))

    nodes_by_id = {
        node["id"]: node
        for node in blueprint["nodes"]
    }

    overall_status = "SUCCESS"

    for node_id in execution_order:

        node = nodes_by_id[node_id]

        if not dependencies_successful(
            node,
            nodes_by_id
        ):

            mark_blocked(node)

            overall_status = "FAILED"

            continue

        result = execute_node(node)

        if result == "STOP":

            overall_status = "FAILED"

            descendants = nx.descendants(
                graph,
                node_id
            )

            for descendant_id in descendants:

                descendant = nodes_by_id[descendant_id]

                if descendant["status"] not in {
                    "SUCCESS",
                    "FAILED",
                    "ABORTED"
                }:

                    mark_blocked(descendant)

            break

        if result != "SUCCESS":
            overall_status = "FAILED"

    print()
    print("Final node states:")

    for node in blueprint["nodes"]:
        print(
            f'{node["id"]} → '
            f'{node["status"]}'
        )

    print()
    print("State histories:")

    for node in blueprint["nodes"]:

        history = node.get(
            "state_history",
            []
        )

        print(
            f'{node["id"]}: '
            f'{" → ".join(history)}'
        )

    print()
    print(
        f"SUMMARY: {blueprint_id} | "
        f"{fixture_type} | "
        f"{overall_status}"
    )

    return {
        "blueprint_id": blueprint_id,
        "fixture_type": fixture_type,
        "status": overall_status,
        "execution_order": execution_order,
        "nodes": blueprint["nodes"]
    }


def process_all_fixtures():

    fixture_files = sorted(
        FIXTURES_DIR.glob("BP*.json")
    )

    print("=" * 60)
    print("DAG EXECUTION ENGINE")
    print("=" * 60)

    print(
        f"Total fixtures: {len(fixture_files)}"
    )

    results = []

    for file_path in fixture_files:

        result = process_blueprint(
            file_path
        )

        results.append(result)

    output_file = (
        OUTPUT_DIR /
        "execution_results.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=2
        )

    print()
    print("=" * 60)
    print("ALL FIXTURES PROCESSED")
    print("=" * 60)

    print(
        f"Total fixtures: {len(fixture_files)}"
    )

    print(
        f"Results saved to: {output_file}"
    )


def main():
    process_all_fixtures()


if __name__ == "__main__":
    main()
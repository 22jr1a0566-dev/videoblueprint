import json
from pathlib import Path

import networkx as nx


FIXTURE_DIR = Path("fixtures")
RESULT_DIR = Path("output/results")


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

    with open(file_path, "r") as file:
        return json.load(file)


def build_graph(blueprint):

    graph = nx.DiGraph()

    for node in blueprint["nodes"]:

        graph.add_node(
            node["id"],
            data=node
        )

    for node in blueprint["nodes"]:

        for dependency in node["depends_on"]:

            graph.add_edge(
                dependency,
                node["id"]
            )

    return graph


def validate_dependencies(blueprint):

    node_ids = {
        node["id"]
        for node in blueprint["nodes"]
    }

    errors = []

    for node in blueprint["nodes"]:

        for dependency in node["depends_on"]:

            if dependency not in node_ids:

                errors.append(
                    f'{node["id"]} depends on missing node {dependency}'
                )

    return errors


def is_retryable(reason):

    return reason in RETRYABLE_FAILURES


def is_terminal(reason):

    return reason in TERMINAL_FAILURES


def dependencies_completed(graph, node_id):

    for dependency in graph.predecessors(node_id):

        if dependency not in graph.nodes:

            return False

        dependency_data = graph.nodes[
            dependency
        ]["data"]

        if dependency_data["status"] != "SUCCESS":

            return False

    return True


def execute_node(node):

    print(
        f'Executing {node["id"]} '
        f'({node["type"]})'
    )

    node["status"] = "RUNNING"

    if node["failure_reason"] is None:

        node["status"] = "SUCCESS"

        print("Result: SUCCESS")

        return "SUCCESS"

    reason = node["failure_reason"]

    print(
        f"Failure reason: {reason}"
    )

    if is_retryable(reason):

        print("Retryable: YES")

        while node["retry_count"] < node["max_retries"]:

            node["retry_count"] += 1

            print(
                f'Retry {node["retry_count"]} '
                f'of {node["max_retries"]}'
            )

            node["status"] = "RETRYING"

            if node.get(
                "force_retry_failure",
                False
            ):

                node["status"] = "FAILED"

                print(
                    "Retry result: FAILED"
                )

                continue

            node["failure_reason"] = None

            node["status"] = "SUCCESS"

            print(
                "Retry result: SUCCESS"
            )

            return "SUCCESS"

        node["status"] = "FAILED"

        print(
            "Retry budget exhausted."
        )

        return "STOP"

    if is_terminal(reason):

        node["status"] = "FAILED"

        print("Retryable: NO")
        print("Terminal failure.")
        print("Action: STOP")

        return "STOP"

    node["status"] = "FAILED"

    print("Unknown failure.")
    print("Action: STOP")

    return "STOP"


def execute_dag(blueprint):

    graph = build_graph(blueprint)

    dependency_errors = validate_dependencies(
        blueprint
    )

    if dependency_errors:

        print(
            "\nDependency errors found:"
        )

        for error in dependency_errors:

            print(
                f"  {error}"
            )

        return {
            "blueprint_id": blueprint["blueprint_id"],
            "fixture_type": blueprint["fixture_type"],
            "status": "INVALID_DEPENDENCY",
            "dependency_errors": dependency_errors,
            "cycle_detected": False,
            "execution_order": [],
            "nodes": []
        }

    if not nx.is_directed_acyclic_graph(graph):

        print(
            "\nERROR: Cycle detected."
        )

        return {
            "blueprint_id": blueprint["blueprint_id"],
            "fixture_type": blueprint["fixture_type"],
            "status": "CYCLE_DETECTED",
            "dependency_errors": [],
            "cycle_detected": True,
            "execution_order": [],
            "nodes": []
        }

    execution_order = list(
        nx.topological_sort(graph)
    )

    print("\n")
    print("=" * 60)
    print(
        f'Executing Blueprint: '
        f'{blueprint["blueprint_id"]}'
    )
    print("=" * 60)

    results = []

    overall_status = "SUCCESS"

    for node_id in execution_order:

        node = graph.nodes[node_id]["data"]

        if not dependencies_completed(
            graph,
            node_id
        ):

            node["status"] = "BLOCKED"

            overall_status = "FAILED"

            print(
                f'{node_id} → BLOCKED'
            )

        else:

            result = execute_node(
                node
            )

            if result == "STOP":

                overall_status = "FAILED"

        results.append({
            "node_id": node["id"],
            "type": node["type"],
            "status": node["status"],
            "failure_reason": node["failure_reason"],
            "retry_count": node["retry_count"],
            "max_retries": node["max_retries"]
        })

    print(
        "\nFinal node states:"
    )

    for node in results:

        print(
            f'{node["node_id"]} → '
            f'{node["status"]}'
        )

    return {
        "blueprint_id": blueprint["blueprint_id"],
        "fixture_type": blueprint["fixture_type"],
        "status": overall_status,
        "dependency_errors": [],
        "cycle_detected": False,
        "execution_order": execution_order,
        "nodes": results
    }


def process_all_fixtures():

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    fixture_files = sorted(
        FIXTURE_DIR.glob("BP*.json")
    )

    print(
        f"Found {len(fixture_files)} fixtures.\n"
    )

    all_results = []

    for file_path in fixture_files:

        blueprint = load_blueprint(
            file_path
        )

        result = execute_dag(
            blueprint
        )

        all_results.append(
            result
        )

        print(
            f'\nSUMMARY: '
            f'{result["blueprint_id"]} | '
            f'{result["fixture_type"]} | '
            f'{result["status"]}'
        )

    output_file = (
        RESULT_DIR /
        "execution_results.json"
    )

    with open(
        output_file,
        "w"
    ) as file:

        json.dump(
            all_results,
            file,
            indent=2
        )

    print("\n")
    print("=" * 60)
    print("ALL FIXTURES PROCESSED")
    print("=" * 60)

    print(
        f"Total fixtures: "
        f"{len(fixture_files)}"
    )

    print(
        f"Results saved to: "
        f"{output_file}"
    )


if __name__ == "__main__":

    process_all_fixtures()
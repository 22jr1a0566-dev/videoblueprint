import json
from pathlib import Path

import networkx as nx


FIXTURE_DIR = Path("fixtures")
RESULT_DIR = Path("output/results")


REGENERATABLE_FAILURES = {
    "quality_failure",
    "timeout",
    "network_error",
    "temporary_server_error",
    "rate_limit"
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


def find_failed_nodes(blueprint):

    failed_nodes = []

    for node in blueprint["nodes"]:

        if node["status"] == "FAILED":

            failed_nodes.append(node)

    return failed_nodes


def find_downstream_nodes(graph, node_id):

    downstream = nx.descendants(
        graph,
        node_id
    )

    return downstream


def determine_regeneration_set(
    graph,
    failed_node_id
):

    downstream_nodes = find_downstream_nodes(
        graph,
        failed_node_id
    )

    regeneration_set = set(
        downstream_nodes
    )

    regeneration_set.add(
        failed_node_id
    )

    return regeneration_set


def selective_regeneration(blueprint):

    graph = build_graph(blueprint)

    failed_nodes = find_failed_nodes(
        blueprint
    )

    if not failed_nodes:

        print(
            "No failed nodes found."
        )

        return blueprint

    regeneration_nodes = set()

    for node in failed_nodes:

        reason = node["failure_reason"]

        print(
            f'\nFailed node: {node["id"]}'
        )

        print(
            f'Failure reason: {reason}'
        )

        if reason in REGENERATABLE_FAILURES:

            print(
                "Regeneration allowed: YES"
            )

            nodes_to_regenerate = (
                determine_regeneration_set(
                    graph,
                    node["id"]
                )
            )

            regeneration_nodes.update(
                nodes_to_regenerate
            )

        else:

            print(
                "Regeneration allowed: NO"
            )

    print(
        "\nSelective regeneration set:"
    )

    for node_id in nx.topological_sort(graph):

        if node_id in regeneration_nodes:

            print(
                f"{node_id} → REGENERATE"
            )

        else:

            print(
                f"{node_id} → PRESERVE"
            )

    for node in blueprint["nodes"]:

        if node["id"] in regeneration_nodes:

            node["status"] = "PENDING"

            node["failure_reason"] = None

            node["retry_count"] = 0

    return blueprint


def execute_regeneration(blueprint):

    graph = build_graph(blueprint)

    regeneration_nodes = {
        node["id"]
        for node in blueprint["nodes"]
        if node["status"] == "PENDING"
    }

    print(
        "\nExecuting selective regeneration..."
    )

    execution_order = list(
        nx.topological_sort(graph)
    )

    for node_id in execution_order:

        if node_id not in regeneration_nodes:

            node = graph.nodes[node_id]["data"]

            print(
                f'{node_id} → PRESERVED '
                f'({node["status"]})'
            )

            continue

        node = graph.nodes[node_id]["data"]

        dependencies_ready = True

        for dependency in graph.predecessors(
            node_id
        ):

            dependency_node = (
                graph.nodes[dependency]["data"]
            )

            if dependency_node["status"] != "SUCCESS":

                dependencies_ready = False

                break

        if not dependencies_ready:

            node["status"] = "BLOCKED"

            print(
                f'{node_id} → BLOCKED'
            )

            continue

        print(
            f'Executing regeneration for '
            f'{node_id} ({node["type"]})'
        )

        node["status"] = "RUNNING"

        node["status"] = "SUCCESS"

        print(
            f'{node_id} → SUCCESS'
        )

    return blueprint


def main():

    file_path = (
        FIXTURE_DIR /
        "BP047.json"
    )

    if not file_path.exists():

        print(
            "BP047.json not found."
        )

        return

    blueprint = load_blueprint(
        file_path
    )

    print("=" * 60)

    print(
        "SELECTIVE REGENERATION"
    )

    print("=" * 60)

    print(
        f'Blueprint: '
        f'{blueprint["blueprint_id"]}'
    )

    print(
        f'Fixture type: '
        f'{blueprint["fixture_type"]}'
    )

    blueprint = selective_regeneration(
        blueprint
    )

    blueprint = execute_regeneration(
        blueprint
    )

    print(
        "\nFinal node states:"
    )

    results = []

    for node in blueprint["nodes"]:

        print(
            f'{node["id"]} → '
            f'{node["status"]}'
        )

        results.append({
            "node_id": node["id"],
            "type": node["type"],
            "status": node["status"],
            "failure_reason": node["failure_reason"],
            "retry_count": node["retry_count"]
        })

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        RESULT_DIR /
        "selective_regeneration_result.json"
    )

    with open(
        output_file,
        "w"
    ) as file:

        json.dump(
            {
                "blueprint_id":
                    blueprint["blueprint_id"],
                "regenerated_nodes":
                    [
                        node["node_id"]
                        for node in results
                        if node["status"] == "SUCCESS"
                    ],
                "nodes": results
            },
            file,
            indent=2
        )

    print(
        "\nResult saved to:"
    )

    print(output_file)


if __name__ == "__main__":

    main()
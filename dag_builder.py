import json
from pathlib import Path
import networkx as nx


FIXTURE_DIR = Path("fixtures")
RESULT_DIR = Path("output/results")


def load_blueprint(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def build_dag(blueprint):
    graph = nx.DiGraph()

    for node in blueprint["nodes"]:
        graph.add_node(
            node["id"],
            type=node["type"],
            status=node["status"],
            failure_reason=node["failure_reason"],
            retry_count=node.get("retry_count", 0),
            max_retries=node.get("max_retries", 2)
        )

    for node in blueprint["nodes"]:
        for dependency in node["depends_on"]:
            graph.add_edge(dependency, node["id"])

    return graph


def validate_dependencies(graph, blueprint):
    node_ids = set(graph.nodes)
    errors = []

    for node in blueprint["nodes"]:
        for dependency in node["depends_on"]:
            if dependency not in node_ids:
                errors.append(
                    f'{node["id"]} depends on missing node {dependency}'
                )

    return errors


def check_cycle(graph):
    return not nx.is_directed_acyclic_graph(graph)


def get_execution_order(graph):
    if check_cycle(graph):
        return []

    return list(nx.topological_sort(graph))


def process_fixture(file_path):

    blueprint = load_blueprint(file_path)
    graph = build_dag(blueprint)

    dependency_errors = validate_dependencies(
        graph,
        blueprint
    )

    cycle_detected = check_cycle(graph)

    if dependency_errors:
        execution_order = []
        status = "INVALID_DEPENDENCY"

    elif cycle_detected:
        execution_order = []
        status = "CYCLE_DETECTED"

    else:
        execution_order = get_execution_order(graph)
        status = "VALID_DAG"

    return {
        "blueprint_id": blueprint["blueprint_id"],
        "fixture_type": blueprint["fixture_type"],
        "status": status,
        "dependency_errors": dependency_errors,
        "cycle_detected": cycle_detected,
        "execution_order": execution_order,
        "nodes": len(graph.nodes),
        "edges": len(graph.edges)
    }


def process_all_fixtures():

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    fixture_files = sorted(
        FIXTURE_DIR.glob("BP*.json")
    )

    print(f"Found {len(fixture_files)} fixtures.\n")

    for file_path in fixture_files:

        result = process_fixture(file_path)

        results.append(result)

        print(
            f'{result["blueprint_id"]} | '
            f'{result["fixture_type"]} | '
            f'{result["status"]}'
        )

    output_file = RESULT_DIR / "dag_results.json"

    with open(output_file, "w") as file:
        json.dump(
            results,
            file,
            indent=2
        )

    print("\nProcessing completed.")
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    process_all_fixtures()
import json
from pathlib import Path

import networkx as nx


FIXTURE_DIR = Path("fixtures")
RESULT_DIR = Path("output/results")


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


def find_parallel_groups(graph):

    parallel_groups = []

    for level in nx.topological_generations(graph):

        valid_nodes = [
            node_id
            for node_id in level
            if "data" in graph.nodes[node_id]
        ]

        if len(valid_nodes) > 1:

            parallel_groups.append(
                sorted(valid_nodes)
            )

    return parallel_groups


def analyze_blueprint(blueprint):

    dependency_errors = validate_dependencies(
        blueprint
    )

    if dependency_errors:

        return None

    graph = build_graph(blueprint)

    if not nx.is_directed_acyclic_graph(graph):

        return None

    parallel_groups = find_parallel_groups(
        graph
    )

    if not parallel_groups:

        return None

    groups = []

    for index, group in enumerate(
        parallel_groups,
        start=1
    ):

        nodes = []

        for node_id in group:

            node = graph.nodes[node_id]["data"]

            nodes.append({
                "node_id": node_id,
                "type": node["type"]
            })

        groups.append({
            "group": index,
            "execution_type": "PARALLEL",
            "nodes": nodes
        })

    return {
        "blueprint_id":
            blueprint["blueprint_id"],
        "fixture_type":
            blueprint["fixture_type"],
        "parallel_groups":
            groups
    }


def main():

    fixture_files = sorted(
        FIXTURE_DIR.glob("BP*.json")
    )

    print("=" * 60)
    print("PARALLEL EXECUTION ANALYSIS")
    print("=" * 60)

    print(
        f"Checking {len(fixture_files)} fixtures..."
    )

    all_results = []

    skipped_fixtures = []

    for file_path in fixture_files:

        blueprint = load_blueprint(
            file_path
        )

        result = analyze_blueprint(
            blueprint
        )

        if result is not None:

            all_results.append(result)

            print("\n")
            print(
                f'Blueprint: '
                f'{result["blueprint_id"]}'
            )

            print(
                f'Fixture type: '
                f'{result["fixture_type"]}'
            )

            for group in result[
                "parallel_groups"
            ]:

                print(
                    f'\nGroup '
                    f'{group["group"]}: PARALLEL'
                )

                for node in group["nodes"]:

                    print(
                        f'  '
                        f'{node["node_id"]} '
                        f'({node["type"]})'
                    )

        else:

            skipped_fixtures.append(
                blueprint["blueprint_id"]
            )

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        RESULT_DIR /
        "parallel_analysis.json"
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
    print("PARALLEL ANALYSIS COMPLETE")
    print("=" * 60)

    print(
        f"Fixtures checked: "
        f"{len(fixture_files)}"
    )

    print(
        f"Parallel fixtures found: "
        f"{len(all_results)}"
    )

    print(
        f"Skipped/non-parallel fixtures: "
        f"{len(skipped_fixtures)}"
    )

    print(
        f"Results saved to: "
        f"{output_file}"
    )


if __name__ == "__main__":

    main()
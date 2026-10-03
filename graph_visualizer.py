import json
from pathlib import Path

import networkx as nx
import matplotlib.pyplot as plt


FIXTURE_DIR = Path("fixtures")
GRAPH_DIR = Path("output/graphs")


def load_blueprint(file_path):

    with open(file_path, "r") as file:
        return json.load(file)


def build_graph(blueprint):

    graph = nx.DiGraph()

    for node in blueprint["nodes"]:

        graph.add_node(
            node["id"],
            type=node["type"],
            status=node["status"],
            failure_reason=node["failure_reason"]
        )

    for node in blueprint["nodes"]:

        for dependency in node["depends_on"]:

            graph.add_edge(
                dependency,
                node["id"]
            )

    return graph


def draw_graph(graph, blueprint):

    plt.figure(figsize=(10, 6))

    position = nx.spring_layout(
        graph,
        seed=42
    )

    labels = {}

    for node in graph.nodes:

        node_type = graph.nodes[node].get(
            "type",
            "MISSING NODE"
        )

        labels[node] = f"{node}\n{node_type}"

    nx.draw(
        graph,
        position,
        with_labels=True,
        labels=labels,
        node_size=3000,
        arrows=True,
        font_size=9
    )

    title = (
        f'{blueprint["blueprint_id"]} - '
        f'{blueprint["fixture_type"]}'
    )

    plt.title(title)

    plt.tight_layout()

    output_file = (
        GRAPH_DIR /
        f'{blueprint["blueprint_id"]}.png'
    )

    plt.savefig(output_file)

    plt.close()

    print(f"Graph saved: {output_file}")


def visualize_all():

    GRAPH_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    fixture_files = sorted(
        FIXTURE_DIR.glob("BP*.json")
    )

    print(f"Found {len(fixture_files)} fixtures.")

    for file_path in fixture_files:

        blueprint = load_blueprint(
            file_path
        )

        graph = build_graph(
            blueprint
        )

        draw_graph(
            graph,
            blueprint
        )

    print("\nGraph visualization completed.")


if __name__ == "__main__":

    visualize_all()
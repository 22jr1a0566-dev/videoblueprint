import gradio as gr
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIXTURES_DIR = os.path.join(BASE_DIR, "fixtures")
RESULTS_FILE = os.path.join(
    BASE_DIR, "output", "results", "execution_results.json"
)
GRAPHS_DIR = os.path.join(BASE_DIR, "output", "graphs")


def load_json(path):
    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_blueprints():
    if not os.path.exists(FIXTURES_DIR):
        return []

    files = [
        f for f in os.listdir(FIXTURES_DIR)
        if f.startswith("BP") and f.endswith(".json")
    ]

    return sorted(
        files,
        key=lambda x: int(x.replace("BP", "").replace(".json", ""))
    )


def find_result(results, blueprint_id):
    if isinstance(results, list):
        for item in results:
            if item.get("blueprint_id") == blueprint_id:
                return item

    if isinstance(results, dict):
        if blueprint_id in results:
            return results[blueprint_id]

        for key in ["results", "blueprints", "executions"]:
            if key in results and isinstance(results[key], list):
                for item in results[key]:
                    if item.get("blueprint_id") == blueprint_id:
                        return item

    return None


def analyze_blueprint(blueprint_file):
    if not blueprint_file:
        return (
            "Please select a blueprint.",
            "",
            "",
            "",
            "",
            None
        )

    blueprint_id = blueprint_file.replace(".json", "")

    blueprint_path = os.path.join(FIXTURES_DIR, blueprint_file)

    blueprint = load_json(blueprint_path)

    if blueprint is None:
        return (
            "Blueprint file not found.",
            "",
            "",
            "",
            "",
            None
        )

    results = load_json(RESULTS_FILE)

    result = find_result(results, blueprint_id) if results else None

    # --------------------------------------------------
    # Blueprint information
    # --------------------------------------------------

    blueprint_status = "LOADED"

    if result:
        blueprint_status = result.get(
            "summary",
            result.get("status", "PROCESSED")
        )

    nodes = blueprint.get("nodes", [])

    node_information = []

    for node in nodes:
        node_information.append({
            "Node": node.get("id"),
            "Type": node.get("type"),
            "Depends On": ", ".join(node.get("depends_on", [])),
            "Initial Status": node.get("status", "PENDING"),
            "Failure": node.get("failure_reason"),
            "Max Retries": node.get("max_retries", 0)
        })

    # --------------------------------------------------
    # Execution order
    # --------------------------------------------------

    execution_order = ""

    if result:
        order = result.get("execution_order")

        if order:
            execution_order = " → ".join(order)

    if not execution_order:
        execution_order = "Execution order available from DAG Builder."

    # --------------------------------------------------
    # Final node states
    # --------------------------------------------------

    final_states = []

    if result:
        states = result.get("final_node_states", {})

        if isinstance(states, dict):
            for node_id, state in states.items():
                final_states.append({
                    "Node": node_id,
                    "Final State": state
                })

    if not final_states:
        for node in nodes:
            final_states.append({
                "Node": node.get("id"),
                "Final State": node.get("status", "PENDING")
            })

    # --------------------------------------------------
    # Failure information
    # --------------------------------------------------

    failure_info = []

    for node in nodes:
        reason = node.get("failure_reason")

        if reason:
            failure_info.append({
                "Node": node.get("id"),
                "Failure Reason": reason,
                "Retry Count": node.get("retry_count", 0),
                "Max Retries": node.get("max_retries", 0)
            })

    if not failure_info and result:
        failures = result.get("failures", [])

        if isinstance(failures, list):
            failure_info = failures

    # --------------------------------------------------
    # Retry information
    # --------------------------------------------------

    retry_info = []

    for node in nodes:
        retry_count = node.get("retry_count", 0)
        max_retries = node.get("max_retries", 0)

        if retry_count > 0 or max_retries > 0:
            retry_info.append({
                "Node": node.get("id"),
                "Retry Count": retry_count,
                "Maximum Retries": max_retries
            })

    # --------------------------------------------------
    # State history
    # --------------------------------------------------

    state_history = []

    if result:
        histories = result.get("state_history", {})

        if isinstance(histories, dict):
            for node_id, history in histories.items():
                if isinstance(history, list):
                    state_history.append({
                        "Node": node_id,
                        "State History": " → ".join(history)
                    })

    # --------------------------------------------------
    # Graph image
    # --------------------------------------------------

    graph_path = os.path.join(
        GRAPHS_DIR,
        f"{blueprint_id}.png"
    )

    if not os.path.exists(graph_path):
        graph_path = None

    # --------------------------------------------------
    # JSON output
    # --------------------------------------------------

    raw_output = json.dumps(
        blueprint,
        indent=2
    )

    return (
        f"{blueprint_id} : {blueprint_status}",
        node_information,
        execution_order,
        final_states,
        failure_info,
        graph_path
    )


# ======================================================
# GRADIO INTERFACE
# ======================================================

blueprints = get_blueprints()

with gr.Blocks(
    title="DAG & Retry Planner"
) as app:

    gr.Markdown(
        """
        # DAG & Retry Planner

        **Execution Blueprint • Dependency Graph • Retry Management • State Machine**
        """
    )

    gr.Markdown(
        """
        Select a blueprint to inspect its DAG, execution order,
        node states, failures, retries and generated graph.
        """
    )

    with gr.Row():

        blueprint_dropdown = gr.Dropdown(
            choices=blueprints,
            label="Select Blueprint",
            value=blueprints[0] if blueprints else None
        )

        analyze_button = gr.Button(
            "Analyze Blueprint",
            variant="primary"
        )

    status_output = gr.Textbox(
        label="Blueprint Status",
        lines=2
    )

    gr.Markdown("## Task Nodes")

    node_table = gr.Dataframe(
        headers=[
            "Node",
            "Type",
            "Depends On",
            "Initial Status",
            "Failure",
            "Max Retries"
        ],
        label="Node Information",
        interactive=False
    )

    gr.Markdown("## Execution Order")

    execution_order_output = gr.Textbox(
        label="Topological Execution Order",
        lines=2
    )

    gr.Markdown("## Final Node States")

    state_table = gr.Dataframe(
        headers=[
            "Node",
            "Final State"
        ],
        label="Node State",
        interactive=False
    )

    gr.Markdown("## Failure Information")

    failure_table = gr.Dataframe(
        label="Detected Failures",
        interactive=False
    )

    gr.Markdown("## Retry Information")

    retry_table = gr.Dataframe(
        label="Retry Status",
        interactive=False
    )

    gr.Markdown("## State History")

    history_table = gr.Dataframe(
        label="State Machine History",
        interactive=False
    )

    gr.Markdown("## DAG Visualization")

    graph_image = gr.Image(
        label="Blueprint DAG",
        type="filepath"
    )

    analyze_button.click(
        fn=analyze_blueprint,
        inputs=blueprint_dropdown,
        outputs=[
            status_output,
            node_table,
            execution_order_output,
            state_table,
            failure_table,
            graph_image
        ]
    )


if __name__ == "__main__":
    app.launch()
    
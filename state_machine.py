from enum import Enum


class NodeState(Enum):

    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    BLOCKED = "BLOCKED"
    ABORTED = "ABORTED"


class StateMachine:

    def __init__(self, node_id):

        self.node_id = node_id

        self.state = NodeState.PENDING

        self.history = [
            NodeState.PENDING.value
        ]

    def transition(self, new_state):

        allowed_transitions = {

            NodeState.PENDING: [
                NodeState.READY,
                NodeState.BLOCKED
            ],

            NodeState.READY: [
                NodeState.RUNNING,
                NodeState.BLOCKED
            ],

            NodeState.RUNNING: [
                NodeState.SUCCESS,
                NodeState.FAILED
            ],

            NodeState.FAILED: [
                NodeState.RETRYING,
                NodeState.ABORTED,
                NodeState.BLOCKED
            ],

            NodeState.RETRYING: [
                NodeState.RUNNING,
                NodeState.FAILED
            ],

            NodeState.SUCCESS: [],

            NodeState.BLOCKED: [],

            NodeState.ABORTED: []
        }

        current_state = self.state

        if new_state not in allowed_transitions[
            current_state
        ]:

            raise ValueError(
                f"Invalid state transition: "
                f"{current_state.value} -> "
                f"{new_state.value}"
            )

        self.state = new_state

        self.history.append(
            new_state.value
        )

    def get_state(self):

        return self.state.value

    def get_history(self):

        return self.history


def success_flow():

    print("\n")
    print("=" * 60)
    print("SUCCESS STATE FLOW")
    print("=" * 60)

    machine = StateMachine("T1")

    print(
        f"T1 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.READY
    )

    print(
        f"T1 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.RUNNING
    )

    print(
        f"T1 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.SUCCESS
    )

    print(
        f"T1 -> {machine.get_state()}"
    )

    print("\nState history:")

    print(
        " -> ".join(
            machine.get_history()
        )
    )


def retry_flow():

    print("\n")
    print("=" * 60)
    print("RETRY STATE FLOW")
    print("=" * 60)

    machine = StateMachine("T2")

    print(
        f"T2 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.READY
    )

    print(
        f"T2 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.RUNNING
    )

    print(
        f"T2 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.FAILED
    )

    print(
        f"T2 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.RETRYING
    )

    print(
        f"T2 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.RUNNING
    )

    print(
        f"T2 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.SUCCESS
    )

    print(
        f"T2 -> {machine.get_state()}"
    )

    print("\nState history:")

    print(
        " -> ".join(
            machine.get_history()
        )
    )


def blocked_flow():

    print("\n")
    print("=" * 60)
    print("BLOCKED STATE FLOW")
    print("=" * 60)

    machine = StateMachine("T3")

    print(
        f"T3 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.BLOCKED
    )

    print(
        f"T3 -> {machine.get_state()}"
    )

    print("\nState history:")

    print(
        " -> ".join(
            machine.get_history()
        )
    )


def terminal_failure_flow():

    print("\n")
    print("=" * 60)
    print("TERMINAL FAILURE FLOW")
    print("=" * 60)

    machine = StateMachine("T4")

    print(
        f"T4 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.READY
    )

    print(
        f"T4 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.RUNNING
    )

    print(
        f"T4 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.FAILED
    )

    print(
        f"T4 -> {machine.get_state()}"
    )

    machine.transition(
        NodeState.ABORTED
    )

    print(
        f"T4 -> {machine.get_state()}"
    )

    print("\nState history:")

    print(
        " -> ".join(
            machine.get_history()
        )
    )


def main():

    print("=" * 60)
    print("DAG NODE STATE MACHINE")
    print("=" * 60)

    print(
        "\nAvailable states:"
    )

    for state in NodeState:

        print(
            f"- {state.value}"
        )

    success_flow()

    retry_flow()

    blocked_flow()

    terminal_failure_flow()


if __name__ == "__main__":

    main()	
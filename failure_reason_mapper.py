import json
from pathlib import Path


FAILURE_MAPPING = {
    "timeout": {
        "category": "temporary",
        "action": "RETRY",
        "retryable": True,
        "regenerate": False,
        "description": "Temporary timeout occurred."
    },

    "network_error": {
        "category": "temporary",
        "action": "RETRY",
        "retryable": True,
        "regenerate": False,
        "description": "Network communication failed."
    },

    "temporary_server_error": {
        "category": "temporary",
        "action": "RETRY",
        "retryable": True,
        "regenerate": False,
        "description": "Temporary server error occurred."
    },

    "rate_limit": {
        "category": "temporary",
        "action": "WAIT_AND_RETRY",
        "retryable": True,
        "regenerate": False,
        "description": "API rate limit was reached."
    },

    "quality_failure": {
        "category": "quality",
        "action": "SELECTIVE_REGENERATION",
        "retryable": True,
        "regenerate": True,
        "description": "Generated output did not satisfy quality requirements."
    },

    "authentication_error": {
        "category": "terminal",
        "action": "STOP",
        "retryable": False,
        "regenerate": False,
        "description": "Authentication or API credentials are invalid."
    },

    "invalid_input": {
        "category": "input",
        "action": "FIX_INPUT",
        "retryable": False,
        "regenerate": False,
        "description": "Input data is invalid."
    },

    "unsupported_model": {
        "category": "configuration",
        "action": "CHANGE_MODEL",
        "retryable": False,
        "regenerate": False,
        "description": "Requested model is not supported."
    },

    "invalid_configuration": {
        "category": "configuration",
        "action": "FIX_CONFIGURATION",
        "retryable": False,
        "regenerate": False,
        "description": "Execution configuration is invalid."
    },

    "missing_dependency": {
        "category": "dependency",
        "action": "FIX_DEPENDENCY",
        "retryable": False,
        "regenerate": False,
        "description": "A required dependency is missing."
    }
}


def map_failure_reason(reason):
    return FAILURE_MAPPING.get(
        reason,
        {
            "category": "unknown",
            "action": "STOP",
            "retryable": False,
            "regenerate": False,
            "description": "Unknown failure reason."
        }
    )


def print_mapping(reason):
    result = map_failure_reason(reason)

    print(f"\nFailure reason: {reason}")
    print(f"Category: {result['category']}")
    print(f"Action: {result['action']}")
    print(f"Retryable: {result['retryable']}")
    print(f"Regenerate: {result['regenerate']}")
    print(f"Description: {result['description']}")


def analyze_all_failures():
    results = {}

    for reason in FAILURE_MAPPING:
        results[reason] = map_failure_reason(reason)

    return results


def save_results(results):
    output_dir = Path("output/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "failure_reason_mapping.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    print(f"\nResults saved to: {output_file}")


def main():
    print("FAILURE REASON MAPPING")
    print("=" * 60)

    for reason in FAILURE_MAPPING:
        print_mapping(reason)

    results = analyze_all_failures()
    save_results(results)


if __name__ == "__main__":
    main()
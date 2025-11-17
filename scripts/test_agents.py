import os
import inspect
from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.ai.agents import AgentsClient
from azure.core.exceptions import ResourceNotFoundError


def get_client(endpoint: str) -> AgentsClient:
    try:
        credential = DefaultAzureCredential(exclude_cli_credential=False)
        return AgentsClient(endpoint=endpoint, credential=credential)
    except Exception as exc:
        print(f"[WARN] DefaultAzureCredential failed: {exc}")
        print("[INFO] Falling back to AzureCliCredential...")
        return AgentsClient(endpoint=endpoint, credential=AzureCliCredential())


def get_agent(client: AgentsClient, agent_id: str, agent_name: str):
    """
    Mimic _get_agent_definition from semantic_kernel_orchestrator.py
    """
    print(f"Current cached id for {agent_name} is {agent_id}")
    get_fn = getattr(client.agents, "get_agent", None) or getattr(client.agents, "get", None)
    if get_fn is None:
        raise AttributeError("AgentsClient does not expose get or get_agent")

    try:
        result = get_fn(agent_id)
        return result if not inspect.isawaitable(result) else asyncio.run(result)
    except ResourceNotFoundError:
        print(f"[WARN] Agent id {agent_id} not found; listing by name...")

    matches = [agent for agent in client.list_agents() if agent.name == agent_name]
    if not matches:
        print(f"[ERROR] No assistant named {agent_name} found.")
        return None

    refreshed = matches[0]
    print(f"[INFO] Refreshed agent id for {agent_name}: {refreshed.id}")
    return refreshed


def main() -> None:
    endpoint = os.environ.get("AGENTS_PROJECT_ENDPOINT")
    if not endpoint:
        raise RuntimeError("Set AGENTS_PROJECT_ENDPOINT (full project URL) in .env.local")

    agent_ids = {
        "TRIAGE_AGENT_ID": os.environ.get("TRIAGE_AGENT_ID"),
        "HEAD_SUPPORT_AGENT_ID": os.environ.get("HEAD_SUPPORT_AGENT_ID"),
        "ORDER_STATUS_AGENT_ID": os.environ.get("ORDER_STATUS_AGENT_ID"),
        "ORDER_CANCEL_AGENT_ID": os.environ.get("ORDER_CANCEL_AGENT_ID"),
        "ORDER_REFUND_AGENT_ID": os.environ.get("ORDER_REFUND_AGENT_ID"),
        "TRANSLATION_AGENT_ID": os.environ.get("TRANSLATION_AGENT_ID"),
    }

    print("Validating agents at", endpoint)
    client = get_client(endpoint)

    for key, agent_id in agent_ids.items():
        if not agent_id:
            print(f"[WARN] Missing env var for {key}")
            continue
        agent_name = key.replace("_ID", "").title().replace("_", "")
        get_agent(client, agent_id, agent_name)


if __name__ == "__main__":
    main()

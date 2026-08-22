def handler(variable):
    """
    variable: string or dict containing bug details.
              Expected keys: description, stepsToReproduce, environment
    """
    import json
    
    # Parse input
    try:
        bug_data = variable if isinstance(variable, dict) else json.loads(variable)
    except Exception:
        bug_data = {}

    description = bug_data.get("description", "").strip()
    steps = bug_data.get("stepsToReproduce", "").strip()
    environment = bug_data.get("environment", "").strip()
    session_id = bug_data.get("sessionId", "test-session-001")
    agent_id = bug_data.get("agentId", "test-agent")
    agent_alias = bug_data.get("agentAlias", "test-alias")

    # Create the payload that your Lambda expects (flat structure)
    payload = {
        "messageVersion": "1.0",
        "function": "create_bug_report",
        "actionGroup": "bug-report-actions",
        "sessionId": session_id,
        "agent": {
            "id": agent_id,
            "alias": agent_alias
        },
        "parameters": [
            {"name": "description", "value": description},
            {"name": "stepsToReproduce", "value": steps},
            {"name": "environment", "value": environment}
        ]
    }
    
    # Return wrapped in "data" because Lambda node uses $.data
    return {
        "data": payload
    }

# The handler function is called with the variable input

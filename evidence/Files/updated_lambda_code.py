import json
import os
import uuid
from datetime import datetime, timezone
import boto3

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

def lambda_handler(event, _):
    print("=== RAW EVENT ===")
    print(json.dumps(event, indent=2, default=str))
    
    # Extract the actual data from the nested structure
    actual_event = None
    
    # Method 1: Extract from the node.inputs structure
    if 'node' in event and 'inputs' in event.get('node', {}):
        for input_item in event['node']['inputs']:
            if input_item.get('name') == 'codeHookInput':
                value = input_item.get('value', {})
                # The value contains {"data": {...}}
                if isinstance(value, dict) and 'data' in value:
                    actual_event = value['data']
                else:
                    actual_event = value
                break
    
    # Method 2: If not found, try the fields structure
    if not actual_event and 'fields' in event:
        for field in event.get('fields', []):
            if 'content' in field and 'document' in field['content']:
                doc = field['content']['document']
                if 'data' in doc:
                    actual_event = doc['data']
                else:
                    actual_event = doc
                break
    
    # Method 3: If still not found, try direct
    if not actual_event:
        if 'messageVersion' in event:
            actual_event = event
        else:
            return _resp(event, {"error": "Could not extract event data"})
    
    print("=== EXTRACTED EVENT ===")
    print(json.dumps(actual_event, indent=2, default=str))
    
    # Validate the event
    if actual_event.get("messageVersion") != "1.0" or actual_event.get("function") != "create_bug_report":
        print(f"❌ Validation failed. messageVersion: {actual_event.get('messageVersion')}, function: {actual_event.get('function')}")
        return _resp(actual_event, {"error": "unsupported"})
    
    # Extract parameters
    params = actual_event.get("parameters") or []
    body = {}
    for p in params:
        if isinstance(p, dict) and p.get("name") is not None:
            body[p.get("name")] = p.get("value", "")
    
    print("=== PARSED PARAMETERS ===")
    print(json.dumps(body, indent=2))
    
    description = (body.get("description") or "").strip()
    steps = (body.get("stepsToReproduce") or "").strip()
    environment = (body.get("environment") or "").strip()
    
    # Validate required fields
    if not description:
        print("❌ Missing description")
        return _resp(actual_event, {"error": "missing", "field": "description"})
    
    # Create bug ticket in DynamoDB
    ticket_id = str(uuid.uuid4())
    item = {
        "ticketId": ticket_id,
        "description": description,
        "stepsToReproduce": steps,
        "environment": environment,
        "status": "OPEN",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sessionId": actual_event.get("sessionId", ""),
        "agentId": actual_event.get("agent", {}).get("id", ""),
    }
    
    print("=== CREATING TICKET ===")
    print(json.dumps(item, indent=2))
    
    table.put_item(Item=item)
    
    print(f"✅ Success! Ticket created: {ticket_id}")
    
    return _resp(actual_event, {
        "ticketId": ticket_id,
        "status": "OPEN",
        "message": "Bug report created successfully"
    })


def _resp(event, obj):
    return {
        "messageVersion": "1.0",
        "response": {
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(obj)
                    }
                }
            }
        }
    }
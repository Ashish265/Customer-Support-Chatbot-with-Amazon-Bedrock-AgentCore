# Customer Support Chatbot with Amazon Bedrock AgentCore

This project implements a customer support chatbot using an Amazon Bedrock Flow and the AgentCore managed harness. Incoming messages are classified and routed to a dedicated bug-report, platform-question, or other-request path.

## End-to-End Implementation Write-Up

### 1. Overview

The Customer Support Chatbot automates the initial triage of customer inquiries. It classifies user inputs, routes them to the appropriate handling logic, and either answers questions directly or creates support tickets for bugs. The system uses a flow-based architecture with conditional routing and prompt-driven responses.

### 2. System Components

#### 2.1 Flow Input

- **Purpose**: Accepts user input as text.
- **Output**: Passes the raw input to the classification stage.
- **Data type**: String containing the user message and optional document reference.

#### 2.2 Classifier Prompt

- **Purpose**: Uses a large language model (LLM) to classify the user’s intent.
- **Input**: User message and optional document reference.
- **Output**: One classification label: `BUG_REPORT`, `PLATFORM_QUESTION`, or `OTHER`.
- **Implementation**: The prompt instructs the model to choose exactly one predefined category and return only that label.

#### 2.3 Routing Condition

The Condition node evaluates the classifier output:

- `status == "PLATFORM_QUESTION"` routes to `Platform_Questions_Prompt`.
- `status == "BUG_REPORT"` routes to `BUG_REPORT_DETAILS_CLASSIFIER`.
- No matching condition routes to `Other Responses` as the fallback.

### 3. Branch 1: Platform Questions

#### 3.1 Platform Questions Prompt

- **Purpose**: Answers common questions about the online shop, including orders, shipping, returns, payments, products, accounts, support, and privacy from the FAQ provided in prompt.
- **Input**: The customer’s question.
- **Output**: A concise answer generated using only the embedded FAQ.
- **Flow**: Covered questions receive an FAQ answer. Questions not covered by the FAQ are redirected to human support at `1-800-123-4567`.

### 4. Branch 2: Bug Reports

#### 4.1 Bug Report Details Classifier

- **Purpose**: Determines whether the customer has provided enough information to create a ticket.
- **Input**: Customer message and optional document reference.
- **Output**: `READY_FOR_REPORT` or `MISSING_DETAILS`.

#### 4.2 Bug Report Status Condition

- `status == "READY_FOR_REPORT"` routes to `Create_Ticket`.
- `status != "READY_FOR_REPORT"` routes to `Follow_Up_Question`.

#### 4.3 Create Ticket

- **Purpose**: Creates a formal support ticket in the backend system.
- **Input**: The customer’s bug description, reproduction steps, and environment details.
- **Condition**: Runs only when all required details are available and the status is `READY_FOR_REPORT`.
- **Output**: A ticket confirmation containing the created ticket information.

The AgentCore managed harness invokes the Lambda tool through the AgentCore Gateway. The tool stores the completed report in the `bug-report-tool-stack-bug-reports` DynamoDB table.

#### 4.4 Inline Code Node

- **Purpose**: Converts the structured text returned by the `Create_Ticket` prompt into an object and builds the payload expected by the ticket-creation tool.
- **Input**: The response from the `Create_Ticket` prompt.
- **Output**: A `data` object containing the Bedrock action-group payload and the required `description`, `stepsToReproduce`, and `environment` fields.
- **Flow**: Runs after `Create_Ticket` and prepares the prompt response for the Lambda node.

Evidence:

- [Inline Code response conversion](evidence/images/Bug%20_Report_Path/4-Inline_code_to_convert_model_response_to_object.png)
- [Inline Code source](evidence/Files/inline_code.py)

#### 4.5 Lambda Ticket-Creation Node

- **Purpose**: Sends the object produced by the Inline Code node to the backend ticket-creation tool.
- **Input**: The parsed bug-report object.
- **Action**: Invokes the Lambda function through the AgentCore Gateway.
- **Output**: Creates a ticket in the `bug-report-tool-stack-bug-reports` DynamoDB table and returns the ticket confirmation to the customer.

The Lambda code was updated to handle the Inline Code node output. It unwraps the `data` payload from the Gateway input, validates the `messageVersion` and `create_bug_report` action, extracts `description`, `stepsToReproduce`, and `environment`, and creates the ticket in DynamoDB. It returns the new ticket ID and `OPEN` status to the flow.

Evidence:

- [Lambda node storing the ticket](evidence/images/Bug%20_Report_Path/6-Lambda_node_to_invoke_lamba_function_to_store_ticket.png)
- [Updated Lambda source](evidence/Files/updated_lambda_code.py)

#### 4.6 Follow-Up Question

- **Purpose**: Requests one missing detail needed to complete the bug report.
- **Trigger**: The status is `MISSING_DETAILS`.
- **Output**: A short, customer-facing clarifying question.
- **Flow**: After the customer replies, the bug-report details are evaluated again until the report is complete.

### 5. Fallback: Other Responses

- **Purpose**: Handles unrecognized, unrelated, unclear, or unsupported requests.
- **Output**: A polite response directing the customer to the human support phone line at `1-800-123-4567`.
- **Flow**: The fallback branch terminates at its dedicated Output node.

## Implementation Summary

### Classification and Routing

The classifier returns exactly one of these labels so that Bedrock Flow Condition nodes can route messages deterministically:

- `BUG_REPORT` - a broken, failing, crashing, or unexpected behavior.
- `PLATFORM_QUESTION` - a question about the shop, its features, policies, orders, payments, shipping, returns, or account.
- `OTHER` - an unrelated, unclear, or unsupported request.

The flow has a separate branch and Output node for each category. Evidence:

- [Full flow diagram](evidence/images/Classification_and_Routing/1-Flow_diagram.png)
- [Classifier prompt](evidence/images/Classification_and_Routing/2%20-classifier_prompt.png)
- [Condition node routing expressions](evidence/images/Classification_and_Routing/3-condition_node_exp_routing.png)
- [Classifier prompt source](evidence/Files/prompts/classifier_prompt.txt)

### Bug Report Path

The bug-report route uses the AgentCore managed harness. Its prompts require the assistant to collect all of the following before creating a ticket:

- Bug description
- Steps to reproduce
- Environment details, such as device, browser, or operating system

The harness invokes the Lambda tool through the AgentCore Gateway. The tool persists completed reports in the `bug-report-tool-stack-bug-reports` DynamoDB table. Evidence:

Deploy the tool stack with CloudFormation before configuring the Gateway:

```bash
aws cloudformation deploy \
	--template-file cloudformation-tool.yaml \
	--stack-name bug-report-tool-stack \
	--capabilities CAPABILITY_NAMED_IAM \
	--region us-east-1
```

- [Bug-report completeness classifier](evidence/Files/prompts/BUG_REPORT_DETAILS_CLASSIFIER.txt)
- [Ticket extraction prompt](evidence/Files/prompts/Create_Ticket.txt)
- [Follow-up question prompt](evidence/Files/prompts/Follow_Up_Question.txt)
- [Lambda tool invocation](evidence/images/Bug%20_Report_Path/6-Lambda_node_to_invoke_lamba_function_to_store_ticket.png)
- [Bug report DynamoDB records](evidence/images/Bug%20_Report_Path/11%20-Dyanmo_DB_Records.png)
- [Created record details](evidence/images/Bug%20_Report_Path/12%20-RECORD_DB_DETAIL.png)

The path distinguishes complete reports with `READY_FOR_REPORT` from incomplete reports with `MISSING_DETAILS`, then asks for one missing detail at a time.

### Platform Question and Other Request Paths

The platform-question path embeds the online shop FAQ in its prompt and answers only from that content. Covered questions receive a direct FAQ answer. Unsupported questions are redirected to human support at `1-800-123-4567`.

The other-request path also directs the customer to the human support phone line. Evidence:

- [Embedded FAQ prompt](evidence/images/Platform_and_other_path/1-Platform_Questions_Prompt.png)
- [Covered platform question response](evidence/images/Platform_and_other_path/2-Platform%2B_question_response.png)
- [Uncovered platform question response](evidence/images/Platform_and_other_path/5-Uncovered_Response.png)
- [Other-request prompt](evidence/images/Platform_and_other_path/3-OtherResponses_prompt.png)
- [Other-request response](evidence/images/Platform_and_other_path/4-OtherResponses.png)
- [FAQ prompt source](evidence/Files/prompts/Platform_Questions_Prompt.txt)
- [Other-request prompt source](evidence/Files/prompts/OtherResponses.txt)

## Testing and Evaluation

The automated test suite includes:

- Complete bug reports that should create tickets
- Incomplete bug reports that should request missing details
- A covered FAQ question
- An uncovered platform question
- An other-request message

Test definitions and flow output:

- [Automated test cases](evidence/Files/tests.json)
- [Flow test results](evidence/Files/flow-tests.jsonl)
- [Evaluation result JSONL](evaluation_result/c663988c-a8af-4fa8-8710-6fbbe708c22b_output.jsonl)
- [S3 upload evidence](evidence/images/Testing_Evaluation/test_file_upload_s3.png)
- [Evaluation job results](evidence/images/Testing_Evaluation/Evaluation_result_file_screenshot.png)
- [Correctness score evidence](evidence/images/Testing_Evaluation/Screen_shot_correctness.png)

Run the evaluation dataset generator from the `project/starter` directory:

```bash
python3 generate-eval-dataset.py \
	--tests-json tests.json \
	--flow-id KO9XI109RY \
	--flow-alias-id BL2Y7RY77O \
	--out-jsonl flow-tests.jsonl \
	--region us-east-1 \
	--enable-trace
```

Upload the generated dataset to the evaluation input location:

```bash
aws s3 cp flow-tests.jsonl s3://test-flows121/flow-tests.jsonl --region us-east-1
```

Use `s3://test-flows121/flow-tests.jsonl` as the evaluation input file and `s3://output-results121/evaluation-results/` as the evaluation output prefix.

The evaluation used Bedrock LLM-as-a-judge metrics. The flow produced an average correctness score of `0.8571` and an average helpfulness score of `0.9047` across 7 records. The flow output also shows successful ticket creation with `OPEN` status and generated ticket IDs for complete bug reports.

## Observation

The results show that 6 of 7 test cases received a correctness score of `1.0`. Complete bug reports, the covered FAQ question, the uncovered platform question, and the other-request path behaved as expected. The single correctness failure was the incomplete shipping-address bug report: the assistant asked for the missing reproduction steps, while the reference response was the classifier label `MISSING_DETAILS`. This indicates a difference between the internal classification value used for routing and the customer-facing follow-up response expected from the completed flow. The follow-up question is appropriate for the conversation, but future evaluation references should account for the final customer-facing behavior rather than requiring the internal label as the response.

The AgentCore agent class was not available for this implementation. As a result, the flow uses an additional classifier for bug-report detail validation, followed by an Inline Code node and a Lambda node to transform the ticket data and create the ticket in the backend.

Guardrail response testing is pending. The evaluation results and observations will be updated after the flow responses have been tested with the created guardrails.

Guardrail implementation evidence:

- [Guardrail creation](evidence/images/guardrail/Guardrail_creation.png)
- [Guardrail check](evidence/images/guardrail/guardrail_check.png)

## Repository Layout

| Directory | Contents |
| --- | --- |
| `project/starter/` | Flow resources, Lambda code, FAQ, test suite, and evaluation dataset generator |
| `evidence/Files/` | Prompt configurations, test definitions, and flow test output |
| `evidence/images/` | Screenshots documenting the flow, prompts, paths, database record, and evaluation |
| `evaluation_result/` | Bedrock Evaluation JSONL output |

For setup and deployment instructions, see [project/README.md](project/README.md).

# Customer Support Chatbot with Amazon Bedrock AgentCore

This project implements a customer support chatbot using an Amazon Bedrock Flow and the AgentCore managed harness. Incoming messages are classified and routed to a dedicated bug-report, platform-question, or other-request path.

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

The evaluation used Bedrock LLM-as-a-judge metrics. The recorded correctness score is `1.0` for the evaluated records, indicating that the flow responses matched the expected behavior. The flow output also shows successful ticket creation with `OPEN` status and generated ticket IDs for complete bug reports.

## Repository Layout

| Directory | Contents |
| --- | --- |
| `project/starter/` | Flow resources, Lambda code, FAQ, test suite, and evaluation dataset generator |
| `evidence/Files/` | Prompt configurations, test definitions, and flow test output |
| `evidence/images/` | Screenshots documenting the flow, prompts, paths, database record, and evaluation |
| `evaluation_result/` | Bedrock Evaluation JSONL output |

For setup and deployment instructions, see [project/README.md](project/README.md).

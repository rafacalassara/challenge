# InfinitePay Agent Swarm

A multi-agent FastAPI service that routes customer queries to specialized agents using CrewAI. It includes a functional RAG pipeline, support utilities, escalation to humans via Slack, and safety guardrails.

## Key Features

- Specialized agents: Manager, Knowledge (RAG + Web), Support (diagnostics + ticket), General (final response), Escalation (Slack).
- Dynamic planning: a Manager agent plans steps and dispatches to the right team.
- RAG pipeline with ChromaDB + SentenceTransformers and web scraping fallback.
- Guardrails to block internal/unsafe prompts and sanitize outputs.
- Fully dockerized API with tests.

## Architecture and Design

- Flow orchestration: `src/flows/main_flow.py`
  - `InfinitePayFlow` uses `@start`, `@router`, `@listen` to orchestrate:
    - `initialize_request()` resets timing/steps.
    - `agent_manager_plan()` calls the Manager agent to produce a `PlannedSteps` plan (via Pydantic `response_format`).
    - `execute_next_step_func()` iterates through steps, invokes the proper agent, aggregates results.
    - `apply_personality_layer()` asks the General agent to compose the final friendly response.
    - Guardrails are enforced at planning and output layers via `src/guardrails/policy.py`.
- State: `src/flows/state.py` defines `InfinitePayState` with request data, step routing, processing metadata, and conversation context.
- Agents: `src/agents/`
  - `manager_agent.py`: builds a dynamic prompt from a live catalog (`get_agent_catalog()`) of teams and tools, ensuring the plan uses valid team names and required schema.
  - `knowledge_agent.py`: uses `InfinitePayRAGTool` and `WebSearchTool` to answer product/policy/rates questions with sources.
  - `support_agent.py`: uses `UserInfo`, `AccountStatus`, `TransactionHistory`, `Ticket` for troubleshooting and ticket creation.
  - `general_agent.py`: composes the final response in a friendly tone (no tools).
  - `escalation_agent.py`: triggers a human via Slack (`SlackNotifyTool`) when policies require.
- Tools: `src/tools/`
  - `rag_tools.py` (RAG), `search_tools.py` (web), `support_tools.py` (mocked support ops), `communication_tools.py` (Slack).
- Guardrails: `src/guardrails/policy.py`
  - `check_user_message_guardrails()` blocks internal/secret-extraction attempts.
  - `sanitize_output()` redacts likely secrets and long digit sequences.

Design choices:
- Dynamic agent catalog injected into the Manager prompt keeps planning aligned with actual tool capabilities.
- Flow and state are minimalistic to keep it testable and robust; agents can run sync/async with graceful fallback.
- Prompts are cookbook-style: identity, tools, guardrails, strategy, and output format for clarity and control.

## RAG Pipeline

- Implementation: `src/tools/rag_tools.py` (`InfinitePayRAGTool`)
  - Vector store: ChromaDB `PersistentClient(path="./data/vector_store")`, collection `infinitepay_kb`.
  - Embeddings: `SentenceTransformer('all-MiniLM-L6-v2')`.
  - Ingestion: `_index_infinitepay_data()` scrapes a curated set of InfinitePay URLs. If scraping is unavailable, it indexes fallback static docs.
  - Storage: documents are chunked (~700 chars), stored with metadata (source URLs).
  - Retrieval: encodes the query, executes nearest-neighbor `query`, returns a concise context summary.
  - Robustness: if dependencies or store are unavailable, it degrades to a safe “no info found” message; exceptions are handled gracefully.

## How LLM Tools Are Leveraged

- CrewAI Agents: Each agent uses `llm="openai/gpt-4.1-mini"` with small `max_iter` and explicit prompts.
- Tools: CrewAI `BaseTool` implementations encapsulate RAG, web search, support utilities, and Slack integration.
- Structured responses: Manager returns `PlannedSteps` (Pydantic) to ensure valid routing and schema compliance.

## API

- FastAPI app: `src/api/main.py`
  - `POST /process` → body: `{"message": str, "user_id": str}`; returns `{"response": str, "processing_time": float}`
  - `GET /health` → basic health check
  - `GET /flow/plot` → generates an HTML visualization with `Flow.plot(...)`
- Models: `src/api/models.py` (`MessageRequest`, `MessageResponse`)
- CORS: permissive for simplicity during development.

Example request:
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the fees of the Maquininha Smart?", "user_id": "client789"}'
```

## Configuration

- Environment variables (optional but recommended): `src/config/settings.py`
  - `OPENAI_API_KEY` for LLM calls
  - `SLACK_WEBHOOK_URL` and optionally `SLACK_CHANNEL` for escalation
  - `.env` is supported (loaded by Pydantic settings)
- Data directory:
  - Vector store persists at `./data/vector_store`. Ensure the process can write to `./data/`.

## Running Locally

Prerequisites:
- Python 3.12
- `pip install -r requirements.txt`

Run:
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Set environment (example):
```bash
# .env
OPENAI_API_KEY=sk-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#support-escalations
```

Open:
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Running with Docker

Build and run:
```bash
docker compose up --build
```

What it does:
- Builds from `Dockerfile` (Python 3.12-slim).
- Exposes port `8000`.
- Mounts `./src` and `./data` for live development and vector store persistence.
- Loads variables from `.env`.

## Testing

- Test suite: `tests/` with unit and API tests.
  - Agents: description/catalog correctness, prompts, tool wiring.
  - Tools: RAG behavior (results/no-results/exception), support tools outputs, Slack presence.
  - Flow: planning, execution routing, personality layer.
  - API: health, `/process` end-to-end with monkeypatched flow.
- Run:
```bash
pytest -q
```

Representative tests:
- `tests/test_agents/test_manager_agent.py` validates dynamic catalog and manager prompt schema.
- `tests/test_tools/test_rag_tool.py` checks RAG index/use/fallback paths.
- `tests/test_flows/test_main_flow_unit.py` ensures proper step mapping and finalization.
- `tests/test_api/test_main_api.py` exercises endpoints with a monkeypatched flow.

## Bonus Criteria Addressed

- Fourth custom agent: `ESCALATION` with `SlackNotifyTool` (`src/agents/escalation_agent.py`, `src/tools/communication_tools.py`).
- Guardrails: implemented in `src/guardrails/policy.py` and enforced in `InfinitePayFlow`.
- Redirect mechanism: when required by policy or user request, the Escalation agent notifies a human via Slack.

## Project Structure

- `src/api/` FastAPI app and schemas
- `src/agents/` Manager, Knowledge, Support, General, Escalation
- `src/tools/` RAG, Search, Support, Communication (Slack)
- `src/flows/` Flow orchestration and state
- `src/guardrails/` Safety policy and sanitization
- `tests/` Unit and API tests
- `Dockerfile`, `docker-compose.yml`, `requirements.txt`

## Notes and Limitations

- LLM access requires a valid `OPENAI_API_KEY`. Tests are designed to run without external services by monkeypatching.
- RAG indexing tries to scrape; in restricted environments it falls back to static docs.
- The Slack integration requires a valid webhook to actually deliver messages.


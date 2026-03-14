# Technical Report

## 1. Problem Identification

### Description of the organization

The project models a school IT support environment where students, faculty, vendors, and other requestors submit help desk tickets for technical issues. The system is designed as an academic demo that simulates the kind of support workflow a school technology team would use to intake, review, route, and resolve requests.

### Description of the operational or security problem

School IT teams often receive repetitive support requests covering account access, password resets, software problems, hardware failures, printer issues, network problems, and security concerns. In a manual workflow, staff must read each ticket, determine its category and priority, decide which department should handle it, and identify whether more information is needed before work can begin.

This creates two operational problems:

- Manual triage takes staff time away from actual issue resolution.
- Low detail tickets cause repeated follow up and slower routing.

The project addresses that problem by combining structured ticket intake, manual review tools, AI assisted triage, and metrics over persisted ticket data.

### Why this problem matters

Triage quality affects the speed and consistency of the entire support process. If a ticket is misclassified or sent to the wrong team, the request can bounce between staff members before reaching the correct owner. If the original request lacks enough detail, technicians must ask more questions before they can act. Both issues increase queue time and reduce the usefulness of the ticketing process.

### Impact of the problem if not solved

If this problem is not improved, likely outcomes include slower routing, more duplicated review effort, inconsistent prioritization, and delayed responses to time sensitive issues such as account lockouts or security related incidents. In a school context, those delays can interfere with learning, classroom operations, and access to institutional systems.

## 2. Proposed Technology Innovation

### Description of the automation solution

The solution is an AI supported IT ticket triage demo built with NiceGUI, PostgreSQL, pgvector, and OpenAI. The application provides:

- A ticket intake page for request submission
- A manual service page for staff review and manual triage
- An AI processing page that runs retrieval assisted AI triage
- A metrics page that summarizes routing, confidence, latency, and review needed outcomes

When AI triage is triggered, the system builds an embedding query from the ticket, retrieves relevant knowledge base chunks and similar historical tickets from PostgreSQL/pgvector, sends a structured triage request to OpenAI, and stores the resulting category, priority, department, summary, recommended action, confidence, missing information field, reasoning, and retrieval trace on the ticket record.

### Why AI is appropriate for this problem

AI is appropriate here because first pass ticket triage is largely a language understanding task. The model is not being used to solve the underlying IT incident directly. Instead, it is used to interpret ticket text, classify the issue, recommend the next team or action, and identify missing details. That is a strong fit for an LLM, especially when the prompt is constrained by schema validation and supplemented with retrieved context from local knowledge base chunks and similar tickets.

### How automation improves the current process

Automation improves the process by reducing repeated reading and routing work for staff. The system can produce a structured first pass triage result quickly and consistently, preserve the reasoning trail, and surface low confidence or incomplete tickets for human review. This does not eliminate human oversight, but it shortens the path from intake to initial action.

## 3. System Architecture

### High Level Architecture

```text
Requestor / Staff User
        |
        v
NiceGUI Web App
  - /request
  - /manual
  - /ai-process
  - /metrics
        |
        v
Service Layer (TicketService)
        |
        +--> PostgreSQL + pgvector
        |     - ticket
        |     - kb_chunk
        |     - ticket_embedding
        |
        +--> OpenAI API
              - embeddings
              - Responses API structured triage
        |
        v
Persisted ticket results, retrieval trace, and metrics dashboard
```

### Data input

The system accepts ticket data from the request form and also loads seeded demo data from `data/MOCK_DATA.json`. It seeds static knowledge base documents during startup and can regenerate ticket embeddings so vector retrieval stays aligned with the active embedding model.

### Processing steps

The implemented AI triage flow is:

1. A ticket is selected for AI triage.
2. The service layer builds query text from the ticket title, description, and requestor role.
3. The system generates an OpenAI embedding for that query.
4. PostgreSQL/pgvector retrieves the top knowledge base matches and similar ticket matches.
5. The application builds a prompt containing the ticket plus retrieved context.
6. OpenAI returns strict JSON schema triage output through the Responses API.
7. The system persists the AI result, retrieval trace, processing time, and refreshed ticket embedding.
8. The metrics page reads stored ticket data and derives review, confidence, and routing summaries.

### AI component

The AI component consists of two OpenAI backed functions:

- Text embeddings for retrieval
- Structured triage generation using strict JSON schema output

The repository documents `text-embedding-3-small` as the embedding model and uses an environment configured OpenAI chat model for triage through the Responses API. The README recommends `gpt-4.1-nano` as a default chat model.

### Output

The main outputs are updated ticket records with triage fields, a persisted retrieval trace, and a metrics dashboard showing triage volume, department routing, confidence distribution, latency, and tickets needing review.

## 4. Implementation

### Python libraries used

The project uses the following key Python libraries and framework components:

- `nicegui` for the web UI
- `sqlalchemy` for ORM/database access
- `alembic` and `alembic-postgresql-enum` for schema migrations
- `asyncpg` for asynchronous PostgreSQL connectivity
- `pydantic` and `pydantic-settings` for validation and configuration
- `openai` for embeddings and structured LLM calls
- `httpx` and `uvicorn[standard]` for runtime support
- `loguru` for application logging
- `pywebview` as an installed dependency for desktop/webview support

### AI models or APIs used

The repository uses OpenAI for:

- Embeddings with `text-embedding-3-small`
- Structured triage generation through the OpenAI Responses API using strict JSON schema

The triage model itself is configurable through environment settings rather than being hardcoded in the service layer.

### Data sources

The project uses several data sources:

- User submitted ticket form data
- Demo ticket records from `data/MOCK_DATA.json`
- Static KB documents seeded from `src/db/seed.py`
- Archived CSV source data in `data/archive/` used by `scripts/generate_mock_tickets.py` to produce reproducible mock tickets
- PostgreSQL tables for persisted ticket, KB chunk, and ticket embedding records

### Key components of the code

Important code areas include:

- `src/main.py` for startup tasks, page registration, migrations, and seeding
- `src/pages/` for the UI pages
- `src/services/ticket_service.py` for orchestration of CRUD, manual triage, AI triage, seeding, and embedding refresh
- `src/repositories/` for database access patterns
- `src/llm/openai_client.py` for OpenAI embedding and structured response handling
- `src/llm/prompt.py` and `src/llm/retrieval.py` for prompt construction and retrieval trace building
- `src/models/` and `src/schemas/` for the persistent and validated data shapes

## 5. Demonstration of Automation

### What tasks are automated

The system automates several first pass support tasks:

- Validation and normalization of submitted ticket data
- Generation of embeddings for ticket and knowledge base text
- Retrieval of top related KB chunks and similar historical tickets
- Structured AI classification into category, priority, and department
- Generation of an AI summary, recommended action, missing information note, and reasoning
- Persistence of the AI trace and processing time data
- Aggregation of operational metrics such as triage counts, confidence, review needed flags, and latency

### What manual tasks were replaced

The application does not remove human review entirely, but it replaces much of the repetitive first pass triage work that staff would otherwise perform by hand, including:

- Reading each new ticket to determine likely issue type
- Assigning an initial category and priority
- Routing the issue to the likely support department
- Drafting an initial summary and next action
- Spotting whether the original ticket is too vague to act on immediately

### Expected efficiency gains

The repository does not include measured benchmark data, so the gains should be described qualitatively. Expected improvements include faster initial routing, reduced repeated triage effort, more consistent ticket categorization, better visibility into low confidence cases, and less time spent on tickets that only need a routine first pass classification.

## 6. Ethical and Security Considerations

### Key risks

This project raises several important ethical and security concerns:

- **Bias in AI:** Demo data and seeded educational ticket examples may overrepresent certain issue types or wording patterns, which can bias classifications or routing suggestions.
- **Privacy issues:** Tickets contain requester names, email addresses, and free text descriptions that may include sensitive details.
- **Data security:** The application stores ticket data in PostgreSQL and sends selected ticket content to OpenAI for embeddings and triage.
- **Model reliability:** AI outputs can still be wrong, incomplete, or overconfident, especially when ticket detail is limited.

### Implemented mitigations visible in the repository

The current codebase already includes several useful controls:

- Strict JSON schema output for triage responses to reduce malformed or inconsistent model output
- A retry path if the first structured response is invalid
- Persisted `ai_confidence` and `ai_missing_information` fields so uncertainty is made visible
- Metrics logic that flags low confidence or missing information tickets for human review
- Local retrieval over PostgreSQL/pgvector so KB and similar ticket context stay in the project database rather than in a separate external retrieval service
- Explicit status transitions and service layer orchestration instead of allowing AI output to silently bypass the ticket workflow

### Remaining gaps or limitations

The repository does not show a complete production security posture. Gaps that would need attention before real deployment include:

- A documented data retention policy for tickets and AI traces
- Role based access controls and stronger authentication around staff actions
- Encryption, secret management, and audit control details beyond local configuration
- Formal evaluation for triage fairness, accuracy, and failure rates
- Human approval rules for security sensitive or high impact ticket categories

## 7. Lessons Learned

### Technical challenges

Several practical challenges are visible from the implementation:

- Coordinating async database work, startup migrations, seeding, and UI driven actions cleanly
- Keeping embeddings synchronized with the active embedding model so retrieval remains valid
- Handling structured LLM output safely when responses may still be invalid on the first attempt
- Maintaining consistent problem framing across prompts, docs, seed content, and report language

### What worked well

The project shows that a narrow AI assisted workflow can be made more reliable by combining local retrieval, strict schemas, service layer orchestration, and persisted review metadata. The architecture is also modular enough that the UI, service logic, repositories, and LLM integration are separated into understandable components.

### What would you improve in the future

Future improvements could include formal accuracy evaluation, stronger access control, richer knowledge base content, better reporting around false positives and false negatives, and controlled human approval workflows for sensitive tickets. If this were extended beyond a demo, the next step would be moving from qualitative expectations to measured operational outcomes.

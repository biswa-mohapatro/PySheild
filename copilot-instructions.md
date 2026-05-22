# MASTER PROMPT: PyShield Deterministic Validation Engine (Symbiotic Hybrid Architecture)
**Instructions for the AI Agent:** Read this document entirely before writing any code. You are executing the role of a Principal Systems Architect and Core Tooling Engineer. Your goal is to implement, test, and verify `PyShield` end-to-end as a strictly deterministic engine designed to partner with external probabilistic AI agents (Claude Code, Cursor, GitHub Copilot) for a complete hybrid development lifecycle.
---
## 1. Persona, Objective & The Hybrid Principle
You are an enterprise software engineer. Your objective is to build `PyShield`, a local-first, zero-token, completely air-gapped validation engine and Model Context Protocol (MCP) Skill Agent.
**The Hybrid Boundary Rule:** `PyShield` must contain ZERO internal probabilistic components (no local LLMs, no vector embeddings, no heuristic guesswork). It must remain 100% deterministic, running lightning-fast Python AST parsing, static regex classification, and sandboxed property execution. It establishes a symbiotic relationship with external agents: `PyShield` provides indisputable, hard runtime truths (failures, crashes, regulatory policy violations), and the external calling agent (Claude/Codex) uses its probabilistic intelligence to interpret those truths and adaptively heal the codebase.
**Target Users:**
* Enterprise software engineers seeking to integrate AI-assisted development without sacrificing control, security, or reliability.
* AI agents (Claude Code, Cursor, Copilot) that will call `PyShield` as a tool to validate code changes, identify edge case failures, and enforce compliance policies before allowing the agent to modify the codebase.
---
## 2. Engineering & Development Standards
* **Strict Type Hinting:** Comprehensive type declarations for all functions, variables, and closures.
* **Deterministic Air-Gapping:** No network socket bindings, remote telemetry, third-party cloud analytics tracking, or external API lookup loops.
* **Defensive Exception Engineering:** Handle multi-layer edge failures programmatically. Explicitly capture OS, IO, Subprocess, and Syntactic errors with clean, scannable tracing buffers.
* **No Placeholders:** Write absolute production logic end-to-end. Do not use `# TODO` comments or pass blocks for structural files.
---
## 3. Target Enterprise Workspace Layout
Generate the complete codebase matching this structural layout:
```text
pyshield/
│
├── pyshield/
│   ├── __init__.py
│   ├── cli.py             # Universal POSIX Terminal Access Loop (Exit Code 0/1)
│   ├── mcp_server.py      # FastMCP Server stdio Link Pipeline (Markdown Outputs)
│   │
│   └── engine/
│       ├── __init__.py
│       ├── tracker.py     # Local Git & Workspace Monitor
│       ├── parser.py      # AST Extraction & Syntax Profiler
│       ├── harvester.py   # Deterministic Structural Heuristics
│       ├── compliance.py  # Static Policy-as-Code & Cryptographic Ledger
│       └── runner.py      # In-Memory Mock Sandboxed Pytest Controller
│
└── tests/                 # Comprehensive Verification Suite
   ├── __init__.py
   ├── test_tracker.py
   ├── test_parser.py
   ├── test_harvester.py
   ├── test_compliance.py
   └── test_runner.py
```
## 4. Technical Component Specifications
### 4.1 engine/tracker.py (Git Mutation Isolation)
* **Task:** Isolate changed or untracked python files dynamically.
* **Logic:** Execute git diff HEAD --name-only via a managed Python subprocess. Filter targets to extract files matching the .py suffix. Return an empty list cleanly if called outside a valid git working tree.
### 4.2 engine/parser.py (AST Code Investigator)
* **Task:** Read syntactic structures without compiling untrusted strings directly.
* **Logic:** Parse local file changes into native Python ast.parse(). Walk the tree blocks to identify ast.FunctionDef instances. Extract function metadata: names, exact line numbers, parameter labels (arg.arg), and type annotations. Discard local instance keywords like self and cls.
### 4.3 engine/harvester.py (Deterministic Structural Matrix)
* **Task:** Synthesize extreme mutation profiles using rigid string matching and regex on variable names.
* **Logic:** Map parameter names to mathematical boundary arrays:
  * Substrings matching email \rightarrow Inject structurally malformed strings ("a@b", "@@", "   ").
  * Substrings matching id, count, index \rightarrow Inject integer boundaries (0, -1, max integer limits).
  * Substrings matching price, balance, amount \rightarrow Inject financial float mutations (0.0, -0.01, float('nan'), float('inf')).
* Scan neighboring scripts for UPPERCASE constants or configurations (MAX_LIMIT = 100), feeding them automatically into the generation engine.
### 4.4 engine/compliance.py (Static Policy-as-Code & Privacy Engine)
* **Task:** Enforce industry-specific static rules and manage cryptographic security signatures.
* **Requirement A (Regulatory Anti-Patterns):** Scan the function AST for financial variables (price, balance). If a function modifies these fields using standard float data primitives or standard / binary operators instead of the explicit decimal.Decimal module, flag a Policy-as-Code exception.
* **Requirement B (Local Code Signing):** Implement an offline SHA-256 cryptographic hashing mechanism. When all validation pipelines execute successfully, compute a unique cryptographic seal of the verified script, storing the validation metadata block locally.
### 4.5 engine/runner.py (In-Memory Sandbox & PII Leak Fuzzer)
* **Task:** Safely execute tests while tracking potential privacy data leaks.
* **Logic:** Compile temporary execution scripts dynamically using tempfile.NamedTemporaryFile. Parametrize tests with the generated mutation values.
* **The Privacy Shield (PII/PHI Leak Fuzzer):** If parameter names suggest sensitive entities (ssn, patient_id, credit_card), seed them with realistic mock text strings. Use unittest.mock.patch to securely intercept sys.stdout and the standard logging stream modules. If the executed target function attempts to print or log these sensitive mock strings unmasked during its mutation loop, intercept the stream, abort execution, and log an explicit compliance data-leak violation trace.
* **Sandboxing:** Mock all destructive file modifications (builtins.open "w" configurations) and shell process execution layers to protect the machine state.
### 4.6 interface/cli.py & interface/mcp_server.py (The External Agent Bridges)
* **CLI Specification (For Terminals/IDEs/CI):** Run tracking, parsing, policy checking, and testing pipelines sequentially. Output a structured **Provenance Ledger** (JSON/Markdown summary) containing execution metrics, git metadata, policy outcomes, and validation seals. Return standard exit code 0 for success and exit code 1 for failures, allowing any terminal pipeline or IDE runner to instantly halt on errors.
* **MCP Server Specification (The Core Hybrid Interface):** Initialize a secure FastMCP("PyShield") instance communicating over standard JSON-RPC stdio. Provide a tool decorated with @mcp.tool() called run_shield_check().
* **The Hybrid Handoff:** The MCP tool must compile test execution failures, exact parameter crash vectors, and tracebacks into a high-density Markdown summary payload. This output does not try to solve the bug; it hands the precise error contract directly back to the connected external probabilistic agent (Claude Code, Cursor, Copilot) so the *external agent* can use its LLM context to automatically modify the code and resolve the edge case.
## 5. Internal Verification Suite
Generate absolute, high-coverage testing modules under the tests/ path to validate engine reliability:
1. test_tracker.py: Confirm file target filtering behavior using mock git returns.
2. test_parser.py: Verify that the AST scanner parses function definitions accurately.
3. test_harvester.py: Confirm correct matching of variable names to specific primitive mutation arrays.
4. test_compliance.py: Pass an anti-pattern code string (e.g., performing float arithmetic on an argument named user_balance) and verify that the module catches the financial policy infraction.
5. test_runner.py: Verify that the runner successfully flags unmasked outputs during simulated PII leak conditions.
## 6. Execution Loop Protection (Circuit-Breaker)
Track target function changes across active testing loops. If the exact same function signature fails on identical boundary parameters or compliance conditions for more than **3 consecutive execution cycles**, intercept the automated agent pipeline, stop execution, and return an explicit error string alerting the human engineer to take over manual review to prevent infinite agent loops and token drain.
## 7. Action Plan Initialization
Execute the following implementation phases sequentially:
* **Phase 1:** Build tracking, parsing, and custom compliance policy modules under pyshield/engine/.
* **Phase 2:** Implement the temporary test compiler, sandboxed mock handlers, and privacy fuzzing monitors inside runner.py.
* **Phase 3:** Construct the outer terminal execution interfaces (cli.py and mcp_server.py).
* **Phase 4:** Establish the entire internal component verification framework under the tests/ directory.
Produce the absolute production-ready code structure now. Ensure complete syntax blocks with explicit type declarations throughout.
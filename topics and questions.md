1. Architecture & System Design
Your architecture treats “structured JSON output” as a contract. Why did you choose schema validation + scoring after generation instead of a stricter constrained-decoding / tool-call contract, and what failure classes does that leave open?
The core loop runs case-by-case and aggregates into a single report. What was the design tradeoff in not modeling this as a pipeline with explicit stages (prompt compose → inference → parse → validate → score → persist), and where do you expect stage-level observability to matter?
You have three adapters (mock/openai/azure) behind a ModelAdapter protocol. What invariants do you require across adapters to keep results comparable, and where do you explicitly allow divergence?
Why is the evaluation “unit of truth” a JSONL dataset with input/expected rather than a more formal test spec (e.g., including per-case scoring rules, tolerances, or schema variants)?
The report includes meta, summary, and per-row results. What is the intended consumer: humans, CI gates, dashboards, or other systems—and how did that influence the chosen structure?
You include both absolute quality gates and baseline regression gates. Why are both needed, and which one is authoritative when they disagree (e.g., absolute threshold passes but baseline regression fails)?
Baselines are “summary-only” or embedded in full reports. Why permit both shapes, and what’s the long-term governance for baseline schema evolution?
run_eval reads prompt text from disk and concatenates with input. What’s the reasoning for “prompt as a file” vs. a prompt registry (IDs, versions, metadata, approvals), and how would you scale prompt lifecycle management?
The design assumes deterministic evaluation. What are your explicit sources of nondeterminism today (clock, model behavior, dependency versions, environment), and how do you bound them?
Your mock adapter is deterministic and doubles as a CI contract. What are the risks of “mock as truth,” and how do you prevent optimizing for mock behavior instead of real model behavior?
How do you reason about schema validity vs. semantic correctness? Give an example where schema-valid output is harmful and how the harness should catch it.
Why is schema validation based on JSON Schema Draft 2020-12, and what are the compatibility implications if a team uses other schema dialects or tooling?
The harness currently models a single prompt+schema per run. What’s your design for multi-prompt evaluation, prompt A/B comparisons, or prompt ensembles in one run?
How would you extend the system to support multiple tasks/types (not just “task extraction”) without turning the harness into a monolith of task-specific scoring logic?
What is your approach to “evaluation drift” (dataset representativeness changes over time) vs. “model drift” vs. “prompt drift,” and where would you encode controls for each?
If the dataset contains PII, what is your architecture-level stance on data minimization, redaction, and preventing outputs from being written to reports?
How do you ensure that results produced on developer machines are comparable to CI results, given OS/tooling differences and optional real-model runs?
What is your threat model for the evaluation harness itself (e.g., malicious dataset lines, prompt injection inside dataset text, dependency compromise), and where is it enforced?
Why is report persistence local-file-based rather than pluggable storage (blob store, database, experiment tracker), and what operational constraints drove that choice?
If this harness became a shared internal platform, what are the first 2–3 architectural seams you would formalize (APIs, plugin points, config model)?
2. Technology & Tooling Choices
Why package this as an installable Python project with a console script instead of a pure “repo script” tool, and what tradeoffs does that create for adoption and versioning?
Why require Python 3.11+ specifically, and what’s the compatibility story for enterprise environments pinned to older versions?
Why use jsonschema for validation instead of faster validators or alternatives, and at what scale does validation become a bottleneck?
Why choose Ruff + Pyright (basic mode) rather than MyPy or stricter Pyright settings, and what kinds of bugs are you intentionally not paying for?
You depend on the OpenAI Python SDK and use the Responses API. Why is that the correct abstraction for both OpenAI and Azure “OpenAI-compatible” endpoints, and what provider-specific edge cases do you accept?
The adapter forces JSON output via a “json_object” response format. Why is that sufficient, and how do you handle partial JSON, truncated outputs, or provider behavior differences?
Why keep dependencies minimally pinned (e.g., >=) rather than lockfiles or hashes, and how do you defend reproducibility over time?
Why implement Windows PowerShell helper scripts in addition to cross-platform CI on Linux, and what’s the operational cost of maintaining two “developer experiences”?
Why upload reports as CI artifacts, and what’s the retention/privacy posture for those artifacts in a real organization?
What’s your stance on packaging metadata and supply-chain signals (SBOM, provenance), given this is intended to be “production-minded”?
Why does the mock quality gate in CI use a relatively low F1 threshold while also applying baseline regression—what was the intended balance?
Why keep cost tracking as an optional field (cost_usd) rather than a first-class metric with a defined computation model?
3. Code Structure & Implementation Patterns
ModelResult includes output, raw_text, latency_ms, usage, cost_usd. Why is this the right boundary object, and what would you add/remove if you needed auditability?
In run_eval, parse errors are encoded by injecting _parse_error into output. Why is that the best representation vs. a separate error channel, and what does that do to schema validation semantics?
exact_match is raw dict equality. Why is that acceptable given ordering, optional fields, and floating-point values, and what errors does it create in practice?
f1_for_titles only considers normalized task titles. Why ignore assignee/due date/confidence, and how does that affect incentive alignment (what the model optimizes for)?
The title normalization lowercases and strips, then uses set overlap. Why a set (dedup) rather than multiset, and what cases does that mis-score?
Schema validation errors are sorted using a json_path attribute fallback. How stable is that across jsonschema versions, and what’s your plan for deterministic error ordering long-term?
The dataset loader defaults missing IDs to case-{idx}. What are the consequences for reproducible diffing when cases get inserted/reordered?
normalize_usage attempts model_dump, then __dict__, then str(). What are the risks of silently stringifying provider objects (lossy data, PII leakage), and how do you bound it?
The adapter composes the prompt as prompt + "\n\nInput:\n" + text. Why not pass structured input to the model as JSON (or separate fields), and what prompt-injection risks does this introduce?
The runner computes rates with denom = total if total > 0 else 1. Why this choice, and what’s the expected behavior of the summary in empty-dataset scenarios?
You compute parse_error_count but do not gate on it explicitly. Why not, and what failure modes could slip through when schema is permissive?
If a provider returns valid JSON that violates the schema, you still compute EM/F1 against expected. Why is that the correct scoring order, and should invalid outputs be scored as hard-zero?
4. DevSecOps & Supply Chain Controls
Secrets for the Azure gate are optional and the job skips when missing. Why is “skip” the right behavior instead of “required on protected branches,” and how do you prevent false confidence?
What are your controls to prevent accidental leakage of API keys via exception traces, report artifacts, or debug logs?
How do you validate that evaluation datasets and prompts don’t contain sensitive data (PII/PHI) before they enter CI artifacts?
Where do you enforce dependency hygiene (pinning strategy, vulnerability scanning, pip supply chain), and what’s the expected workflow when a critical CVE drops?
What’s your plan for SBOM/provenance (SLSA-style attestations) if this becomes a shared internal tool used to gate releases?
How do you prevent prompt/dataset tampering (e.g., PR changes that quietly lower quality) beyond baseline regression—code owners, required reviewers, signed commits?
What is your approach to test isolation for adapter env requirements—how do you ensure no accidental calls to real endpoints in CI?
Do you treat reports as build artifacts with retention policies? Who can access them, and what’s your data classification stance?
How would you handle multi-tenant usage (different teams, different secrets, different datasets) in CI without secrets sprawl?
What threat model assumptions are you making about prompt injection embedded in dataset text, and do you need sanitization or containment?
How do you ensure the “mock adapter” can’t be exploited to mask regressions (e.g., gaming title normalization to inflate F1)?
What are your branch protections and quality gate enforcement rules—are they documented and auditable?
5. Reliability & Testing Strategy
The tests focus on shape, gates, and a few metric behaviors. What is your confidence boundary: what classes of regression are you intentionally not testing?
How do you prevent flakiness when using real model endpoints (timeouts, rate limits, transient errors), and what retry/backoff policy should live in the adapter?
What is your “golden signal” for the harness itself—latency, pass rate, parse error rate, schema-valid rate—and how do you detect harness regressions vs. model regressions?
The mock adapter is deterministic; real adapters are not. How do you design tests that remain stable but still validate real-provider integration?
How do you handle partial failures across cases (e.g., one case errors out)? Should the run fail fast, or produce a partial report with error rows?
How would you add property-based tests for schema validation and scoring to reduce blind spots?
How do you validate that schema evolution doesn’t invalidate historical baselines or silently change the meaning of “schema_valid_rate”?
What’s your strategy for test data management: expanding the dataset, labeling edge cases, preventing overfitting, and keeping runtime reasonable?
Do you need deterministic time control for latency metrics in tests, and what would you assert if latency becomes non-trivial?
Where do you draw the line between “unit tests for harness logic” and “integration tests for model behavior,” and how are those scheduled (PR vs nightly)?
How do you design rollback for baseline updates (analogous to snapshot tests), and how do you ensure reviewers understand the behavioral delta?
What are the failure modes of exact_match and why isn’t it replaced with a more semantic comparator for structured outputs?
6. Observability & Telemetry
Today the primary telemetry is the JSON report. What is your plan for logging/tracing across adapter calls without leaking prompt contents or PII?
How would you instrument parse errors and schema violations to provide actionable diagnostics (e.g., top failing schema paths, most common error messages)?
How do you want to trend results over time (F1, schema rate, latency), and where would you store/run those trends (CI artifacts vs a metrics system)?
Usage normalization is provider-dependent. What minimal usage fields do you consider required (prompt tokens, completion tokens, total tokens), and how do you reconcile provider differences?
The report includes avg_latency_ms only. What other latency stats matter (p95/p99, outliers), and why are they absent?
How would you add correlation IDs (run ID already exists) across pipeline steps and external calls for debugging production incidents?
What’s your approach to redacting raw_text and inputs in reports while still enabling debugging?
How do you detect and alert on harness-level anomalies (e.g., sudden parse_error_count spike) separate from model quality changes?
If the harness is used across teams, how do you segment and attribute runs (team/app/model/prompt version) in telemetry?
What would you expose as a minimal “evaluation contract” for downstream systems (dashboards, release gates)?
7. Progressive Delivery & Deployment Model
How do you connect this harness to a release pipeline so that prompt/model changes are gated the same way as code changes?
What is your model for canarying prompt updates: per-user rollout, per-tenant rollout, or per-feature flag, and how would the harness simulate or validate that?
Baseline regression is a strong gate—how do you decide when baseline updates are allowed, and what approvals are required?
What is your rollback strategy when a deployed prompt/model regresses in production but still passes harness thresholds due to dataset gaps?
How do you handle multiple environments (dev/stage/prod) with different models, deployments, or safety policies while keeping evaluation comparable?
Would you ever allow “soft gates” (warnings) vs hard CI failures, and what criteria govern that decision?
How do you prevent “threshold erosion” over time (teams lowering minimums to ship), and what governance enforces quality floors?
How do you ensure evaluation results remain meaningful when upstream context changes (RAG corpus changes, tool availability changes)?
If adapters evolve (new provider, new API), how do you stage and validate adapter changes without invalidating historical comparisons?
8. Governance & Risk (AI-specific if relevant)
What is your governance model for prompts as production artifacts (review, approvals, traceability, versioning, and ownership)?
How do you ensure the dataset represents real user distribution and failure modes rather than a curated “happy path” set?
If the expected outputs encode business rules, how are those rules reviewed, tested, and kept in sync with product requirements?
How do you address fairness/bias risks in extraction tasks (names, roles, language variants), and how would you represent those concerns in the dataset metadata?
What is your stance on storing model outputs (raw_text, structured JSON) from real endpoints—retention, access control, and data classification?
How do you handle prompt injection risks when user-provided text is embedded into the prompt—do you need delimiter strategies, structured input, or model-side policies?
When schema changes, who decides backward compatibility requirements, and how do you migrate baselines and expectations safely?
What is your approach to “evaluation tampering” (changing dataset/expected to make metrics look good) and what controls prevent it?
How do you define “success” beyond F1—e.g., safety compliance, policy adherence, refusal behavior—and where would those evaluators live?
If this harness is used for regulated domains, what audit artifacts are missing (model cards, prompt change logs, evaluation sign-offs, incident postmortems)?
9. Scalability & Performance
Scenario: dataset grows from 12 cases to 50k. What breaks first (runtime, memory, provider quotas), and what is your scaling plan (batching, concurrency, caching)?
Scenario: Azure endpoint starts returning intermittent 429s. How should the adapter handle backoff, jitter, and max retry budgets to keep evaluation reliable but bounded?
Scenario: schema validation becomes expensive with complex schemas. Would you precompile validators, parallelize validation, or sample cases—and what correctness tradeoffs do you accept?
Scenario: you need per-case timeouts and circuit breaking. Where do you implement it (runner vs adapter), and how do you report partial results?
Scenario: you want to run evaluations across multiple models/prompts in a matrix. How do you avoid combinatorial explosion and keep comparisons statistically meaningful?
Scenario: model outputs are huge and often invalid JSON. How do you prevent report bloat and still preserve enough evidence to debug?
Scenario: multiple teams run this in CI simultaneously. How do you avoid rate-limit contention and manage shared quotas?
Scenario: you need deterministic replay of a past run. What artifacts must be recorded (prompt hash, dependency versions, adapter config), and which are currently missing?
Scenario: you need to shard evaluation across workers and merge results. What invariants must hold for summary correctness and baseline regression checks?
Scenario: you want near-real-time evaluation in a PR with strict time limits. What optimizations (case prioritization, early stopping) are acceptable without hiding regressions?
10. Cost & Operational Tradeoffs
How do you compute and validate cost_usd across providers given different pricing models, and why is it currently optional rather than enforced?
What cost controls do you want in CI for real-model runs (budget caps, max tokens, run frequency), and where do you encode them?
Baseline regression encourages stability but can block improvements that temporarily dip metrics. How do you balance shipping velocity vs quality enforcement?
What is your stance on storing and uploading reports as artifacts given potential sensitive content—what is the operational risk vs debugging value?
How do you decide the minimum viable dataset size and composition to justify gating production releases?
What’s the operational burden of maintaining the mock adapter’s heuristics as the dataset evolves, and when do you retire it?
How do you handle multi-region endpoints and latency/cost tradeoffs when evaluating globally deployed systems?
If you add more metrics (safety, compliance), how do you prevent evaluation cost from scaling faster than product iteration?
11. Consulting & Leadership Framing
Explain this harness to a CTO in 90 seconds: what risk it reduces, what it costs, and how it changes engineering behavior.
If a PM asks “why did my feature fail CI,” how do you communicate baseline regression vs absolute quality thresholds without eroding trust?
You claim “production-minded, minimal.” Where is the minimum line, and what features are explicitly out of scope—even if stakeholders request them?
How do you convince skeptical engineers that evaluation gates should block merges like unit tests do?
Describe how you’d roll this out across 20 teams with different maturity levels without creating a platform tax.
If leadership wants a single metric for “AI quality,” what do you propose, what do you refuse, and why?
How would you run a post-incident review where a model regression escaped despite the harness—what artifacts and questions do you bring?
How do you define ownership boundaries between product teams (prompts/datasets) and platform teams (harness/adapters)?
What is your governance story for baseline updates—who approves, what evidence is required, and how do you prevent gaming?
If legal asks for an audit trail of prompt and evaluation changes for the last 6 months, what can you produce today and what’s missing?
12. Hard Panel Questions
Your baseline file shows low exact_match_rate but CI gates still pass. Why is exact match even in the system if it’s not a meaningful quality signal, and what would you do about it?
f1_for_titles ignores assignee/due date/confidence—so a model could “cheat” by outputting correct titles with nonsense owners/dates. Why is that acceptable for a production gate?
You treat parse errors as structured output by placing _parse_error in JSON. Isn’t that masking a contract violation? Defend this design choice under adversarial review.
The real-model gate can silently skip when secrets aren’t present. How do you prevent an organization from thinking it has “real-model coverage” when it doesn’t?
Dependency versions are loose (>=). How do you claim reproducibility and regression protection when the runtime can change underneath you?
The mock adapter uses heuristic extraction and deterministic confidence. How do you justify using those confidence values in expected outputs as if they were ground truth?
Your schema is permissive (confidence is any number). Why didn’t you constrain it (0..1) and enforce stronger semantics at the schema level?
If a dataset line is maliciously crafted to cause pathological runtime or memory blowups, what protections exist today, and where should they live?
The report includes raw_text for real adapters. How do you prevent accidental storage of policy-violating or sensitive content, and what’s your deletion strategy?
If a candidate told you “this is production-ready,” what is the strongest argument against that claim based on what’s present, and what evidence would change your mind?
Learning Gap Signals
Must deeply understand to answer well:

JSON Schema validation semantics and failure modes
Evaluation design for structured outputs (metric choice, incentives, brittleness)
CI gating patterns (absolute thresholds vs baseline regression)
Provider integration realities (429s, timeouts, nondeterminism, output truncation)
Reproducibility controls (dependency locking, artifacting, run metadata)
Prompt lifecycle management (versioning, governance, review workflows)
Data handling governance (PII risk, artifact retention, auditability)
Areas that appear weak or under-explained:

Real-model run reliability strategy (retries/backoff, timeouts, partial failure policy)
Cost accounting model (cost_usd is present but not implemented as a metric)
Observability beyond “write a JSON report” (no metrics/tracing/log strategy)
Strong semantic scoring (current scoring is narrow and gameable)
Areas that could trigger skepticism:

“Production-minded” claim vs missing explicit SLOs/rollbacks/threat model
Skippable real-model CI gate can create false assurance
Loose dependency constraints undermine long-term determinism
Metrics can pass while extracting wrong assignees/dates/confidence
Missing artifacts likely to be asked for:

ADRs (metric rationale, adapter design choices, baseline governance)
Threat model and data classification policy (especially around prompts/datasets/reports)
SLOs/SLIs for evaluation and for the AI feature being gated
Rollback strategy for prompt/model/baseline changes
Dependency lock strategy and/or SBOM/provenance signals
Documented policy for dataset curation, representativeness, and drift management
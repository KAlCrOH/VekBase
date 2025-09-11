# AGENTS

Blueprint for integrating autonomous / semi-autonomous agents around the RAG core.

## Roles
| Agent | Responsibility | Input | Output |
|-------|----------------|-------|--------|
| RetrievalOrchestrator | Current orchestrator wrapper | query | bundle_id, contexts |
| ValidationAgent (planned) | Sanity-check model output vs. contexts | bundle (prompt, contexts, completion) | validation_report |
| SafetyAgent (planned) | Scan for PII / disallowed content | completion | redaction_actions |
| ReRankAgent (planned) | Apply cross-encoder rerank | initial contexts | reordered contexts + scores |
| IngestQualityAgent (planned) | Detect low-quality or duplicate chunks | new chunks | quality_flags |
| DriftMonitorAgent (planned) | Statistical drift on embedding vectors | embedding batches | drift_alerts |

## Interaction Pattern
1. User query -> RetrievalOrchestrator -> initial bundle
2. (Optional) ReRankAgent improves ordering
3. LLM generation
4. ValidationAgent compares completion to contexts
5. SafetyAgent redacts / flags
6. Bundle finalization (hashing + signatures)

## Message Bus (Future)
| Event | Emitted By | Consumed By |
|-------|------------|-------------|
| bundle.created | Orchestrator | Validation, Safety |
| bundle.validated | ValidationAgent | Safety, Audit Dashboard |
| drift.metrics | DriftMonitorAgent | Alerting |

Transport options: simple in-process dispatcher -> Redis Streams -> Kafka (scaling phase).

## Minimal Agent Interface (Proposed)
```python
class Agent(Protocol):
    name: str
    def handle(self, event: dict) -> Optional[dict]: ...
```

## Evaluation Strategy
- Track agent added latency
- Maintain allowlist of permissible agent modifications (e.g., cannot drop contexts without reason code)

## Roadmap
1. Define event schema (pydantic models)
2. Implement in-process dispatcher
3. Add ValidationAgent MVP (exact substring coverage metric)
4. Integrate SafetyAgent (regex PII patterns)
5. Externalize events (Redis) when throughput > threshold

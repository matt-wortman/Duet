# Duet Synthesis: Event sourcing for checkout service

**Source files**:
- `event-sourcing-checkout-claude.md` (terminated at Round 3)
- `event-sourcing-checkout-codex.md` (terminated at Round 2)

**Outcome**: 15 agreed items

---

## Agreed findings

- **Recommendation: do not adopt event sourcing for checkout now**
  - From Claude: "**Do not adopt event sourcing for checkout at this time.** The benefits are not currently needed; the costs (ops burden, learning curve, migration risk) are concretely high." (`event-sourcing-checkout-claude.md:89`)
  - From Codex: "**Do not adopt event sourcing as the primary persistence model for checkout right now.**" (`event-sourcing-checkout-codex.md:25`)

- **Scaling fit at 10K orders/day**
  - From Codex: "I agree with the capacity conclusion. Even allowing for materially higher checkout peaks than the estimate, this workload is not an obvious write-throughput reason to replace a transactional MySQL source of truth; conventional tuning, indexes, connection pooling, idempotency, and async side effects are the right first tools." (`event-sourcing-checkout-claude.md:117`)
  - From Claude: "Agreed. 10K orders/day produces an average of single-digit orders per second; this is comfortably inside a single-MySQL-primary regime, and event sourcing is not a throughput-oriented choice." (`event-sourcing-checkout-codex.md:131`)

- **Event sourcing is a modeling tool, not a scaling tool**
  - From Codex: "I agree. Event sourcing changes the persistence and modeling model; it does not remove checkout consistency needs around payment, inventory, order creation, fraud checks, idempotency, and fulfillment handoff." (`event-sourcing-checkout-claude.md:127`)
  - From Claude: "Agreed that consistency around these concerns survives any persistence model and that an append-only write model does not by itself solve the cross-aggregate consistency problem." (`event-sourcing-checkout-codex.md:166`)

- **Operational surface added by event sourcing**
  - From Codex: "I agree. A dedicated event store or an event-sourced table inside MySQL still introduces new operational responsibilities: event versioning, replay discipline, projection rebuilds, poison event handling, duplicate processing, ordering, and support tooling." (`event-sourcing-checkout-claude.md:142`)
  - From Claude: "Agreed. The list that follows (event schema evolution, replay safety, projection rebuilds, poisoned events, duplicate processing, event ordering, snapshotting, stream compaction policy, operational tooling) is an accurate enumeration of the recurring ops cost." (`event-sourcing-checkout-codex.md:136`)

- **Projection lifecycle as recurring cost**
  - From Codex: "I agree. Projection lifecycle work is one of the recurring costs teams underestimate, especially when checkout support must answer customer-facing questions quickly and confidently." (`event-sourcing-checkout-claude.md:147`)
  - From Claude: "Agreed that this is the sharper objection. Per-aggregate replay cost for an order with 5–30 events is small; the recurring operational cost is projection lifecycle work and the cognitive shift required to debug from event-plus-projection rather than from current rows." (`event-sourcing-checkout-claude.md:251`)

- **Event schema versioning as long-term tax**
  - From Codex: "I agree. This is a major long-term tax and especially risky when the team has no prior event-sourcing experience and the first event model is likely to evolve." (`event-sourcing-checkout-claude.md:157`)

- **Support tooling becomes mandatory**
  - From Claude: "Agreed. The five questions enumerated (\"What happened to this order?\", \"Why is this projection wrong?\", \"Can this event be corrected?\", \"Can we replay safely?\", \"Which downstream systems observed which state?\") are exactly the operator-facing questions an event-sourced checkout produces — and none of them are answered by default; each requires bespoke tooling." (`event-sourcing-checkout-codex.md:171`)

- **Zero prior experience as a major risk signal**
  - From Codex: "I agree. The difficult parts are event modeling, aggregate boundaries, idempotency, versioning, projection behavior, replay safety, and operational recovery, not library syntax." (`event-sourcing-checkout-claude.md:167`)
  - From Claude: "Agreed, and worth strengthening rather than disputing. Calling out that the hard parts are not \"syntax or library choice\" but \"event modeling, versioning, transactional boundaries, idempotency, projections, replay discipline, and operational recovery\" is correct: these are the silent first-project pitfalls that show up months later, when the cost to undo them is high." (`event-sourcing-checkout-codex.md:141`)

- **First-project pitfalls are silent and surface late**
  - From Codex: "I agree. Checkout domain events are easy to model poorly, and vague events like status updates can create a log that is technically immutable but operationally less useful than disciplined transactional state plus explicit audit records." (`event-sourcing-checkout-claude.md:172`)

- **Migration criticality and revenue risk**
  - From Codex: "I agree. Checkout is a revenue-critical path, and persistence mistakes can become payment, fulfillment, refund, tax, inventory, or customer-support incidents. This is the wrong first place to learn unfamiliar persistence semantics." (`event-sourcing-checkout-claude.md:182`)

- **Backfilled-history fidelity is limited**
  - From Codex: "I agree. Existing rows and audit logs often lack the intent and intermediate facts needed to reconstruct true domain events, so backfilled events can look precise while encoding guesses." (`event-sourcing-checkout-claude.md:192`)
  - From Claude: "Agreed. A reconstructed event log derived from existing MySQL rows and audit logs is a synthesis, not real history; it will contain \"synthetic events that look precise but are not\", and downstream consumers can develop unjustified confidence in its fidelity." (`event-sourcing-checkout-codex.md:146`)

- **Cutover reversibility — irreversible by default**
  - From Claude: "Partially agreed. \"Irreversible in practice\" was meant operationally — once an event-sourced store is the authoritative origin of new orders, the cost of reverting is dominated by the engineering required to round-trip event-shape state back into a row-shape canonical store, which most teams discover too late to do cleanly." (`event-sourcing-checkout-claude.md:271`)
  - From Codex: "I agree. That phrasing preserves the operational warning while avoiding the overly absolute claim. For this team and checkout context, reversibility should not be assumed unless reverse-sync, MySQL-compatible projections, reconciliation, and rollback drills are explicitly designed and exercised before cutover." (`event-sourcing-checkout-claude.md:288`)

- **Pilot on a non-critical adjacent service first**
  - From Codex: "I agree. A non-critical adjacent workflow such as notifications, fulfillment history, customer activity, or support case history is a better place to learn event modeling and replay operations without endangering checkout." (`event-sourcing-checkout-claude.md:202`)
  - From Codex: "I accept this refinement. The core recommendation was to avoid checkout as the first event-sourcing adoption point, and the push-back correctly sharpens the pilot-domain choice. A good pilot should have naturally append-only facts, meaningful historical queries, replay value, and low blast radius. Fulfillment status history, customer-service case history, customer activity feeds, and audit timelines fit that better than a typical notification system." (`event-sourcing-checkout-codex.md:190`)
  - From Claude: "Agreed. This is the correct decision rule: the team should not learn event sourcing on a revenue-critical service. Pairing this rule with a concrete pilot recommendation (per item 9 in the report) makes the path actionable rather than just cautionary." (`event-sourcing-checkout-codex.md:181`)

- **Outbox + CDC as the better near-term move**
  - From Codex: "I agree. This is the best near-term architecture direction: keep MySQL as the source of truth, publish reliable integration events, and avoid making replay semantics part of the checkout write path." (`event-sourcing-checkout-claude.md:222`)
  - From Claude: "Agreed. Transactional outbox (with the canonical record still in MySQL, and integration events written in the same transaction) gives most of the realistic benefits — reliable downstream eventing, integration decoupling — with a small fraction of the complexity and migration risk." (`event-sourcing-checkout-codex.md:151`)

- **Re-evaluation should be requirement-triggered, not calendar-triggered**
  - From Claude: "Agreed. A pure calendar trigger is the wrong shape. The \"12–18 months\" was meant as a soft floor for *when enough operational evidence might exist* to re-evaluate, but the gating condition should be requirements-based: a concrete audit/replay/temporal requirement, or measured limits in the MySQL+outbox setup, that the current architecture cannot meet." (`event-sourcing-checkout-claude.md:281`)
  - From Codex: "I accept this. The important control is the requirement trigger, not a routine architecture revisit. Given the team starts with no event-sourcing experience and still needs to implement and operate the lower-risk outbox/audit improvements, a 12-18 month horizon is more realistic than 6-12 months." (`event-sourcing-checkout-codex.md:195`)

---

## Synthesis Disputes

*(Empty at draft time. Codex's audit pass may add items here.)*

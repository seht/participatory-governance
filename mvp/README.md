# PPG MVP — Architecture Documents

This folder contains the engineering specification for building a Minimum Viable Product of
Programmable Participatory Governance (PPG), derived from the formal research paper in `papers/thesis/`.

---

## Core Design Principles

1. **Vote anonymity by protocol, not by policy.** The system cannot link a vote choice to a
   citizen identity — not even an administrator with full database access. This is enforced by
   nullifier-based ZK proofs (Semaphore), not by access controls.

2. **Keys never leave the citizen's device.** Government ID verification produces an on-chain
   *commitment* only. The citizen's Semaphore identity secret, signing keys, and any credential
   material is generated and stored client-side. No server ever sees it.

3. **All public financial flows are public records.** The Financial Transparency Ledger is
   append-only at the database level and mirrored on-chain. No row is ever deleted or updated.

4. **PostgreSQL is the right datastore.** The governance pipeline requires ACID transactions
   (one vote per nullifier, atomic state transitions). PostgreSQL with JSONB handles both the
   structured guarantees and flexible proposal/deliberation content. The `JSONB` type gives
   document-store flexibility for proposal content without sacrificing transactional integrity.
   Ledger tables enforce append-only by revoking `DELETE`/`UPDATE` from the application database
   role at the DB level — no application-layer discipline required.

5. **Use existing audited primitives.** Do not build ZK circuits, governor logic, or identity
   protocols from scratch. The ecosystem already has them.

---

## Technology Choices

### Smart Contracts: Ethereum L2 (Base) + OpenZeppelin + Semaphore

**Why Ethereum L2 over Cardano (Tier 1–2)?**

OpenZeppelin Governor is a battle-tested, audited implementation of the propose → vote →
timelock → execute state machine. That is months of work already done. Base (Coinbase L2,
OP Stack) gives sub-cent transaction costs and ~2s block times on a live mainnet with
existing tooling. The Solidity ecosystem (Hardhat, Foundry, The Graph, wagmi, OpenZeppelin)
is the thickest available for fast iteration.

Cardano's eUTXO model is architecturally closer to the paper's formal methods approach —
eUTXO contracts are easier to formally verify than EVM contracts — and Aiken (the modern
Cardano contract language) is ergonomic. The recommendation: Ethereum L2 for Tier 1–2,
evaluate Cardano as the formal verification track for Tier 3 national deployment.

| Layer | Technology | Rationale |
|---|---|---|
| L2 chain | Base (OP Stack) | EVM-compatible, sub-cent gas, Coinbase sequencer |
| Governor | OpenZeppelin Governor v5 | Audited propose→vote→execute state machine |
| Anonymous voting | Semaphore v4 | Nullifier-based ZK group membership, PSE/EF |
| Indexing | The Graph (subgraph) | Replaces custom event-query layer |
| ZK circuits | circom + snarkjs | Client-side proof generation for votes |

### Backend API: Node.js + TypeScript + Fastify

Fastify over Express: schema-first request validation, better TypeScript integration,
lower overhead. The API layer is thin — it indexes chain state, serves proposal content,
and manages the off-chain deliberation record. It does not process votes (those go directly
to the contract).

### Decentralised Data Layer (no single DB is the source of truth)

| Data | Source of truth | Technology |
|---|---|---|
| Nullifier registry | On-chain (Semaphore contract) | Semaphore v4 |
| Vote tallies | On-chain (Governor events) | The Graph subgraph |
| Financial Ledger records | On-chain writes, permanent archival | Tableland + Arweave |
| Proposal content + deliberation | Content-addressed off-chain, CID on-chain | IPFS / Filecoin |
| Local query cache | Rebuildable cache only, not source of truth | PostgreSQL 16 (optional) |

**Tableland** is the decisive choice for the Financial Transparency Ledger. Every `INSERT` is
an L2 transaction — the table state is fully determined by the chain. No operator can alter or
delete rows. The ledger is SQL-queryable without trusting any server.

**PostgreSQL** exists only as a performance cache for complex frontend queries. If it is
destroyed, the full state is reconstructable from chain events + IPFS content. The application
database role has no `DELETE` or `UPDATE` privileges on any table — enforced at the Postgres
role level, not application code.

### Frontend: Next.js + wagmi/viem + @semaphore-protocol/identity

Semaphore's JS SDK handles identity generation and client-side proof generation entirely
in the browser. No server contact for identity operations.

### Identity: Semaphore v4 (PSE / Ethereum Foundation)

See `identity.md` for full specification.

---

## Document Map

| File | Contents |
|---|---|
| `README.md` | This file — rationale and tech stack |
| `architecture.md` | Component diagram, data flow, on/off-chain partition |
| `contracts.md` | Smart contract interfaces and constructor parameters |
| `governance-pipeline.md` | State machine, quorum formula, legitimacy score |
| `identity.md` | Identity progression (Tier 1–3), Semaphore flows, social-graph Sybil resistance |
| `financial-ledger.md` | Tableland schema, write authorization, API endpoints |
| `security.md` | Threat model and write-access enforcement |
| `tiers.md` | Three-tier release plan (local → regional → national) |
| `running-costs.md` | Full cost model: gas, infrastructure, audits, per-tier budgets |

---

## What This MVP Does NOT Include (by design)

- ZK identity proofs in Tier 1 (authentication only; ZK added in Tier 2)
- National-scale deployment (Tier 3)
- Cardano implementation
- UI/UX design (separate design sprint)
- Smart contract formal verification (Tier 3 research track)

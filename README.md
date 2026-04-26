# Programmable Participatory Governance (PPG)

A formal research and engineering project producing a governance framework, academic thesis,
and MVP architecture specification for transparent, accountable, and privacy-preserving
participatory governance.

The core design commitment: all governance actions and financial flows are public records by
default. All citizen identity data and vote choices are private by protocol — not by policy.

---

## Repository Structure

```
papers/thesis/  Research thesis (LaTeX) — authoritative source of truth
mvp/            MVP engineering specification — contracts, architecture, pipeline, identity
simulations/    Agent-based simulation code and generated figures
```

---

## Research Paper (`papers/thesis/`)

A formal thesis covering:

- Empirical problem analysis (corruption, participation collapse, administrative opacity)
- Full PPG framework: Transparency Default, Financial Transparency Ledger, Civic Participation
  Mandate, Constrained Administrative Authority, Merit-and-Mandate accountability
- Formal state-machine model with dynamic quorum and legitimacy score
- Hybrid identity model (Semaphore, ZK proofs, Soulbound Tokens)
- Five-layer decentralised reference architecture
- Agent-based simulation results across three behavioural archetypes
- Game-theoretic proof of manipulation deterrence; repeated-game collusion containment proposition
- Epistemic necessity of participatory input (formal proposition connecting Hayek/Sowell to Hurwicz/Maskin)
- Comparative analysis of PPG vs. civic technology platforms (vTaiwan, Decidim, Better Reykjavik) and DAO governance
- Three-tier implementation pathway: Local → Regional → National
- Political economy grounding: Hayek, Sowell, Herman/Chomsky, Hirschman, Scott

**Build:**

```bash
cd papers/thesis
pdflatex -interaction=nonstopmode -output-directory=paper paper.tex
pdflatex -interaction=nonstopmode -output-directory=paper paper.tex   # second pass for refs
# Output: papers/thesis/paper/paper.pdf
```

**Regenerate simulation figures:**

```bash
python3 -m venv .venv
.venv/bin/pip install numpy matplotlib
.venv/bin/python simulations/generate_simulations.py
```

---

## MVP Architecture (`mvp/`)

Engineering specification for building PPG. Derived from the research paper.
No single server is the source of truth for any governance-critical data.

| File | Contents |
|---|---|
| `README.md` | Technology rationale and stack overview |
| `architecture.md` | Component diagram, data flows, on/off-chain partition, Paymaster spec, subgraph manifest |
| `tiers.md` | Three-tier release plan (Local → Regional → National), identity migration |
| `financial-ledger.md` | Tableland schema, API spec, append-only enforcement |
| `governance-pipeline.md` | State machine, OZ Governor mapping, quorum equations, legitimacy score |
| `identity.md` | Semaphore anonymous voting, nullifiers, key sovereignty, revocation |
| `contracts.md` | Solidity interface specs — PPGToken, PPGGovernor, LedgerController, Semaphore |
| `security.md` | Threat model, Tableland write policy, ZK proof verification, key management |
| `running-costs.md` | Gas cost model, audit budgets, tier-by-tier annual cost forecast |

**Core technology choices:**

| Layer | Technology |
|---|---|
| L2 chain | Base (OP Stack) |
| Governor | OpenZeppelin Governor v5 |
| Anonymous voting | Semaphore v4 (PSE / Ethereum Foundation) |
| Ledger storage | Tableland (on-chain SQL) + Arweave (permanent archive) |
| Proposal content | IPFS / Filecoin |
| Indexing | The Graph |
| Backend | Node.js 22 + Fastify + TypeScript |
| Query cache | PostgreSQL 16 (rebuildable from chain — not source of truth) |
| Frontend | Next.js 15, wagmi v2, viem v2 |
| Contracts | Foundry |

---

## Privacy Model

Vote records on-chain contain only `(nullifier_hash, proposal_id, vote_choice)`.
`nullifier_hash = hash(identity.nullifier || proposalId)`. The identity secret never leaves
the citizen's device. No server, no chain query, and no administrator action can
reconstruct the citizen ↔ vote link. This is a cryptographic guarantee, not a policy.

---

## Git

```
Repository: git@github.com:seht/participatory-governance.git
Branch:     main
```


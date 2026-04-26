# PPG MVP — Three-Tier Release Plan

Derived from paper Chapter 14 (Implementation Pathway). Each tier builds on the previous.
No tier requires the next to be useful in production.

---

## Tier 1 — Local Deployment (MVP)

**Goal:** Prove the core transparency and governance primitives work in a bounded real-world
context. Generate evidence. Build public trust. Keep scope minimal.

**Target contexts:** Municipal budget committee, community land trust, cooperative enterprise,
neighbourhood assembly.

**Scale:** ~100–10,000 participants.

### What is built in Tier 1

| Component | Scope |
|---|---|
| Financial Transparency Ledger | Full. Tableland + Arweave. Public, append-only, queryable. |
| Governance pipeline | Simplified: `DRAFT → DELIBERATION → VOTING → EXECUTED`. Veto deferred. |
| Identity | Wallet-based authentication. One wallet per citizen, no ZK. Civic mandate tracked off-chain. |
| Proposal content | IPFS storage. CID anchored on-chain via Governor. |
| Vote anonymity | Standard Governor votes (pseudonymous — wallet address). Semaphore deferred to Tier 2. |
| Interface | Read-only public dashboard for ledger + proposals. Voting via wallet connect. |

### What is explicitly NOT in Tier 1

- Anonymous voting (Semaphore / ZK) — deferred to Tier 2
- Constitutional validator
- Veto mechanism
- Regional/national identity integration
- Merit-and-Mandate enforcement
- Constrained Administrative Authority enforcement

### Tier 1 Success Criteria

- Financial Ledger records 100% of financial flows within 24h of authorisation
- At least one proposal completes the full pipeline to execution
- At least 30% of eligible participants vote on at least one proposal
- No data loss events (chain + IPFS as source of truth validated)
- Independent audit of smart contracts completed

### Tier 1 Contract Deployment

- Base Sepolia testnet → Base mainnet
- Contracts: `PPGGovernor`, `PPGTimelockController`, `PPGToken` (ERC20Votes)
- Tableland: `financial_ledger_{chainId}_{tableId}` table
- The Graph: deploy subgraph, verify event indexing

---

## Tier 2 — Regional Deployment

**Goal:** Add anonymous voting, connect multiple Tier 1 instances, integrate with existing
institutional identity where available (national ID, residence registry).

**Scale:** ~10,000–1,000,000 participants.

### What is added in Tier 2

| Component | Change |
|---|---|
| Anonymous voting | Semaphore v4 integrated. Nullifier-based ZK. Votes are anonymous by protocol. |
| Identity | Government ID verification by trusted issuer → Semaphore commitment only. Private key stays client-side. |
| Veto mechanism | Implemented. Threshold-based petition triggers re-vote. |
| Constitutional validator | Off-chain legal review step before voting opens. Hash recorded on-chain. |
| Cross-instance governance | Composable proposal-bridging: Tier 1 instances can escalate proposals to Tier 2. |
| Civic Participation Mandate | Notification cycle, blank-vote, grace period enforced on-chain. |
| Constrained Administrative Authority | Scope registry deployed. Out-of-scope actions require public deliberation. |

### Tier 2 Identity Transition

The Tier 1 PPGToken is not replaced — it is repurposed. In Tier 2, PPGToken balance
still determines `proposalThreshold` (who can propose). Voting weight, however, shifts
from token balance to Semaphore group membership (1 vote per valid ZK proof).

**Migration steps for each citizen:**

1. Citizen generates a Semaphore identity in their browser (`new Identity()`)
2. Citizen presents eligibility credential to the trusted issuer (same municipal registry
   used in Tier 1)
3. Issuer calls `SemaphoreGroup.addMember(groupId, identity.commitment)` on-chain
4. Citizen can now cast anonymous votes via `castVoteAnonymous()` using ZK proofs

**Coexistence during rollout:** Both vote paths are active simultaneously during the
transition period:
- `castVote()` (Tier 1, token-weighted, pseudonymous) remains callable
- `castVoteAnonymous()` (Tier 2, Semaphore, anonymous) is added
- The quorum and pass condition count all votes from both paths together
- Citizens who have not yet enrolled in Semaphore can still vote pseudonymously

**After full migration:** `castVote()` is disabled via a governance proposal that also
sets `semaphoreOnly = true` on the Governor. This requires a passed proposal — no
operator can unilaterally flip it.

**Token state:** PPGToken remains in the non-transferable soulbound state. The token
now serves only as proposer eligibility proof. MINTER_ROLE and TRANSFER_ADMIN_ROLE
remain with the TimelockController (governance-controlled).

**Citizens who do not migrate** remain unable to vote (not enrolled in the Semaphore
group) once `semaphoreOnly` is enabled. The issuer maintains the enrollment service
for a minimum of 90 days after the cutover to allow late registrations.

### Tier 2 Success Criteria

- Vote anonymity verified by independent ZK circuit audit
- Zero cases of identity linkage to vote choice (by design, not by policy)
- Veto mechanism triggered and resolved at least once in production
- At least two Tier 1 instances interoperating via proposal bridge

---

## Tier 3 — National Deployment

**Goal:** Full PPG deployment at national scale. Formal verification. Cardano evaluation.
Maximum decentralisation and resilience.

**Scale:** 1,000,000+ participants.

### What is added in Tier 3

| Component | Change |
|---|---|
| ZK identity | Full ZK circuit for eligibility verification. No trusted issuer for issuance — citizen self-proves eligibility from government credential. |
| Formal verification | Smart contracts machine-checked against the formal model (paper §5). Candidate platform: Cardano (eUTXO + Aiken) or EVM + Certora. |
| Merit-and-Mandate | On-chain professional credential registry. Dual accountability enforced. |
| Layer 2 performance | Benchmarked at national election scale. ZK rollup preferred over optimistic for finality. |
| Cross-jurisdictional | Governance message standards for interoperability across national PPG deployments. |
| Sybil resistance | Social-graph Sybil resistance at $10^7$ scale — validator set, empirical testing. |

### Cardano Evaluation (Tier 3 track)

Cardano's eUTXO model provides deterministic script execution — each transaction's script
sees only its own inputs, making formal verification tractable. The paper's state machine
maps cleanly to eUTXO because governance state transitions are naturally input-output
transformations. Aiken (typed functional language, Plutus backend) has tooling approaching
the Solidity ecosystem for developer ergonomics.

Decision gate: after Tier 2 production, evaluate whether to migrate to Cardano for Tier 3
or continue on Ethereum L2 with formal verification via Certora/Halmos. Decision criteria:
ZK identity circuit performance, smart contract audit cost, validator set availability.

---

## Cross-Tier Invariants

These properties must hold at every tier:

1. **Keys never leave the citizen's device.** No server ever handles signing material.
2. **Financial Ledger is public and append-only.** Enforced at the chain level (Tableland),
   not application level.
3. **Vote anonymity is a protocol property.** In Tier 1, pseudonymous (wallet); in Tier 2+,
   cryptographically anonymous (Semaphore). The system never records identity ↔ vote linkage.
4. **Source of truth is chain + content-addressed storage.** The PostgreSQL cache is always
   rebuildable. No governance state is stored exclusively in the cache.
5. **All components are independently deployable.** Financial Ledger can run without the
   governance pipeline. Identity module can run without Semaphore (Tier 1). No required coupling.

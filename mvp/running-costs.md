# PPG MVP — Running Cost Forecast

Covers on-chain gas, infrastructure, one-time deployment, and audit costs across all
three tiers. All figures are approximate and based on April 2026 market conditions.

---

## Assumptions

| Parameter | Value | Notes |
|---|---|---|
| ETH price | $3,000 | Adjust multiplier proportionally |
| Base L2 gas price — baseline | 0.001 gwei | Typical idle-network price on Base |
| Base L2 gas price — high | 0.01 gwei | Sustained congestion; rare on Base |
| Exchange: gwei → USD | `gas_units × gwei × 3×10⁻⁶` | At $3,000/ETH |
| Gas sponsorship | Paymaster (ERC-4337) | Institution pre-funds; citizens pay $0 |
| Citizen vote gas if self-paid | included for reference | Paymaster recommended for civic UX |

**Why L2 is non-negotiable:** Semaphore ZK proof verification costs ~400,000 gas. On
Ethereum mainnet at a typical 30 gwei, that is 0.012 ETH per vote = **$36 per vote**.
Completely unacceptable for civic governance. On Base L2 at 0.001 gwei, the same operation
costs **$0.0012 per vote** — a 30,000× reduction. The L2 choice is load-bearing for the
entire economic model.

---

## Gas Cost per Operation

| Operation | Gas estimate | Baseline ($) | High ($) |
|---|---|---|---|
| `PPGToken.mint()` | 110,000 | 0.00033 | 0.0033 |
| `PPGGovernor.propose()` | 260,000 | 0.00078 | 0.0078 |
| `PPGGovernor.castVote()` (Tier 1, standard) | 85,000 | 0.00026 | 0.0026 |
| `PPGGovernor.castVoteAnonymous()` (Tier 2, Semaphore) | 400,000 | 0.0012 | 0.012 |
| `PPGGovernor.queue()` | 120,000 | 0.00036 | 0.0036 |
| `PPGGovernor.execute()` (base, excl. payload) | 200,000 | 0.00060 | 0.0060 |
| `PPGGovernor.setConstitutionalValidation()` | 60,000 | 0.00018 | 0.0018 |
| `PPGGovernor.signVetoPetition()` | 90,000 | 0.00027 | 0.0027 |
| Tableland `INSERT` (ledger record) | 105,000 | 0.00032 | 0.0032 |
| `SemaphoreGroup.addMember()` (enrollment) | 130,000 | 0.00039 | 0.0039 |
| Paymaster overhead per sponsored tx | +80,000 | +0.00024 | +0.0024 |

---

## One-Time Deployment Costs

### Contract Deployment Gas

| Contract | Gas estimate | Baseline ($) | High ($) |
|---|---|---|---|
| `PPGToken` | 1,200,000 | 3.60 | 36 |
| `PPGTimelockController` | 1,100,000 | 3.30 | 33 |
| `PPGGovernor` | 3,600,000 | 10.80 | 108 |
| `LedgerController` | 900,000 | 2.70 | 27 |
| Tableland table creation | 500,000 | 1.50 | 15 |
| Gnosis Safe (LedgerWriter multisig) | 400,000 | 1.20 | 12 |
| **Total deployment** | **7,700,000** | **$23** | **$231** |

Deployment is a one-time cost. Even at the high-congestion scenario it is negligible.

### Smart Contract Audits (one-time, external)

These are the dominant one-time costs. Prices are market rates for specialist firms
(OpenZeppelin, Trail of Bits, Spearbit, Cantina).

| Scope | Tier | Estimated cost |
|---|---|---|
| PPGToken + PPGGovernor + PPGTimelockController + LedgerController | Tier 1 | $15,000 – $50,000 |
| Semaphore integration + castVoteAnonymous + veto mechanism | Tier 2 | $30,000 – $100,000 |
| ZK circuit audit (circom + Groth16 setup) | Tier 2 | $20,000 – $60,000 |
| Formal verification (Certora or equivalent) | Tier 3 | $80,000 – $300,000 |

**Recommendation:** For Tier 1, budget $20,000–$40,000 for a focused audit of the three
core contracts. The Governor and Timelock are largely OZ boilerplate; the custom logic
(dynamic quorum, impact parsing from description string) is the primary audit target.
PSE may provide discounted or sponsored audit support given Semaphore is their project.

---

## Annual Recurring Costs: Tier 1

**Target scale:** 100 – 10,000 participants; 12 proposals/year; 60% average turnout.
Example: 1,000 participants, 600 votes per proposal.

### On-Chain Gas (institution pays all via Paymaster)

| Event | Quantity/year | Per-tx gas + Paymaster | Annual baseline | Annual high |
|---|---|---|---|---|
| Token minting (one-off, amortised over 3 years) | 333 | 190,000 | $0.19 | $1.90 |
| `propose()` | 12 | 340,000 | $0.012 | $0.12 |
| `castVote()` Tier 1 standard | 7,200 (12×600) | 165,000 | $3.56 | $35.64 |
| `queue()` + `execute()` | 24 | 320,000 | $0.23 | $2.30 |
| Ledger `INSERT` | 500 | 185,000 | $0.28 | $2.77 |
| Group `addMember()` (new enrollments) | 100 | 210,000 | $0.063 | $0.63 |
| **Total on-chain gas** | | | **~$4.30** | **~$43** |

On-chain gas at Tier 1 is negligible even in the high-congestion scenario. The
Paymaster pre-fund needed to cover Tier 1 for a year: **$50–200** (including buffer).

### Infrastructure

| Service | Provider examples | Monthly | Annual |
|---|---|---|---|
| The Graph (subgraph) | Hosted service free tier | $0 | $0 |
| IPFS pinning (proposals + deliberation) | Pinata free (1GB), or web3.storage | $0 – $10 | $0 – $120 |
| Arweave permanent archival | ~$5/GB one-time | ~$1 one-time | $1 |
| PostgreSQL (cache) | Railway / Render free tier | $0 – $7 | $0 – $84 |
| Node.js API | Railway / Render free → starter | $0 – $10 | $0 – $120 |
| Next.js frontend | Vercel Hobby (free) | $0 | $0 |
| Domain + Cloudflare | Any registrar | ~$2 | ~$25 |
| **Total infrastructure** | | **$2 – $29/mo** | **$25 – $350/yr** |

### Tier 1 Total Cost Summary

| Category | Year 1 | Year 2+ |
|---|---|---|
| Contract deployment | $25 – $230 | — |
| Smart contract audit | $15,000 – $50,000 | — |
| On-chain gas (Paymaster fund) | $50 – $200 | $50 – $200 |
| Infrastructure | $25 – $350 | $25 – $350 |
| **Total** | **$15,100 – $50,780** | **$75 – $550** |

Year 1 cost is dominated by audit. Year 2+ is essentially just hosting.

---

## Annual Recurring Costs: Tier 2

**Target scale:** 10,000 – 1,000,000 participants. Example: 100,000 participants,
50 proposals/year, 30% turnout (30,000 votes/proposal).

### On-Chain Gas

| Event | Quantity/year | Per-tx gas + Paymaster | Annual baseline | Annual high |
|---|---|---|---|---|
| `propose()` | 50 | 340,000 | $0.051 | $0.51 |
| `castVoteAnonymous()` Semaphore | 1,500,000 (50×30k) | 480,000 | **$2,160** | **$21,600** |
| `queue()` + `execute()` | 100 | 320,000 | $0.096 | $0.96 |
| `setConstitutionalValidation()` | 50 | 140,000 | $0.021 | $0.21 |
| `signVetoPetition()` | 500 | 170,000 | $0.255 | $2.55 |
| Ledger `INSERT` | 1,000 | 185,000 | $0.555 | $5.55 |
| `addMember()` (enrollment) | 5,000 | 210,000 | $3.15 | $31.50 |
| **Total on-chain gas** | | | **~$2,164** | **~$21,641** |

> **ZK vote gas is the dominant cost at Tier 2.** At 30,000 anonymous votes per proposal,
> 50 proposals/year, the Paymaster fund needs **$2,200 – $22,000/year** at current prices.

### Infrastructure

| Service | Provider | Monthly | Annual |
|---|---|---|---|
| The Graph (self-hosted graph node) | 4 vCPU, 16GB RAM VPS | $80 – $200 | $960 – $2,400 |
| IPFS pinning (higher volume) | Pinata Growth plan | $20 – $50 | $240 – $600 |
| Arweave archival | ~$5/GB, ~2GB/year | $10 one-time | $10 |
| PostgreSQL managed | Supabase Pro / Railway Pro | $25 – $100 | $300 – $1,200 |
| Node.js API (2× instances for HA) | Railway / Render starter | $20 – $60 | $240 – $720 |
| Next.js frontend | Vercel Pro | $20 | $240 |
| CDN / DDoS protection | Cloudflare Pro | $20 | $240 |
| **Total infrastructure** | | **$185 – $450/mo** | **$2,220 – $5,410/yr** |

### Tier 2 Total Cost Summary

| Category | Year 1 | Year 2+ |
|---|---|---|
| Contract deployment (incremental) | $5 – $50 | — |
| Audit: Semaphore integration + ZK circuit | $50,000 – $160,000 | — |
| On-chain gas (Paymaster fund) | $2,200 – $22,000 | $2,200 – $22,000 |
| Infrastructure | $2,220 – $5,410 | $2,220 – $5,410 |
| **Total** | **$54,425 – $187,460** | **$4,420 – $27,410** |

---

## Annual Recurring Costs: Tier 3

**Target scale:** 1,000,000+ participants. Example: 2,000,000 participants,
200 proposals/year, 40% turnout (800,000 votes/proposal).

### The vote-batching optimisation becomes mandatory at this scale

Individual per-vote on-chain transactions at 400,000 gas each would cost:
800,000 votes × 200 proposals × $0.0012 = **$192,000,000/year** — clearly infeasible.

**ZK vote batching** (recursive proof aggregation): Multiple votes are aggregated into a
single on-chain proof submission. Plonky2 / Groth16 recursion can batch 1,000–10,000 votes
into one proof. At 1,000-vote batches:
- 800,000 votes = 800 batch submissions per proposal
- Each batch: ~1,500,000 gas (proof + verifier overhead) + 80k Paymaster = 1,580,000 gas
- 800 batches × 200 proposals × 1,580,000 gas × $0.000003 = **$758/year at baseline**
- At high congestion (0.01 gwei): **$7,584/year**

Vote batching reduces the Tier 3 on-chain gas from an unworkable $192M to a manageable
$760 – $7,600/year. Batching is a Tier 3 implementation requirement, not an optimisation.

### On-Chain Gas (with 1,000-vote batching)

| Event | Quantity/year | Gas | Annual baseline | Annual high |
|---|---|---|---|---|
| ZK vote batches | 160,000 (800 × 200) | 1,580,000 | $720 | $7,200 |
| `propose()` | 200 | 340,000 | $0.20 | $2.04 |
| `queue()` + `execute()` | 400 | 320,000 | $0.38 | $3.84 |
| `setConstitutionalValidation()` | 200 | 140,000 | $0.084 | $0.84 |
| Ledger `INSERT` | 10,000 | 185,000 | $5.55 | $55.50 |
| `addMember()` (enrollment) | 100,000 | 210,000 | $63 | $630 |
| `signVetoPetition()` | 20,000 | 170,000 | $10.20 | $102 |
| **Total on-chain gas** | | | **~$800** | **~$8,000** |

### Infrastructure

| Service | Spec | Monthly | Annual |
|---|---|---|---|
| The Graph (cluster) | 3-node graph node cluster | $600 – $2,000 | $7,200 – $24,000 |
| IPFS / Filecoin (high volume) | Filecoin storage deal + pinning | $100 – $400 | $1,200 – $4,800 |
| Arweave archival | ~$5/GB, ~10GB/year | $50 one-time | $50 |
| PostgreSQL (managed, HA) | AWS RDS Multi-AZ or Supabase Enterprise | $300 – $1,000 | $3,600 – $12,000 |
| Node.js API (load balanced) | 4–8 instances | $200 – $800 | $2,400 – $9,600 |
| ZK batch prover (worker nodes) | 4 vCPU workers for proof aggregation | $200 – $600 | $2,400 – $7,200 |
| Next.js frontend (enterprise CDN) | Vercel Enterprise or self-hosted | $200 – $500 | $2,400 – $6,000 |
| DDoS / WAF | Cloudflare Business | $200 | $2,400 |
| **Total infrastructure** | | **$1,800 – $5,500/mo** | **$21,650 – $66,050/yr** |

### Tier 3 Total Cost Summary

| Category | Year 1 | Year 2+ |
|---|---|---|
| Contract deployment (incremental) | $50 – $500 | — |
| Formal verification + audit | $100,000 – $500,000 | — |
| On-chain gas | $800 – $8,000 | $800 – $8,000 |
| Infrastructure | $21,650 – $66,050 | $21,650 – $66,050 |
| **Total** | **$122,500 – $574,550** | **$22,450 – $74,050** |

---

## Cross-Tier Summary

| Tier | Scale | Year 1 total | Ongoing annual | Per-participant/year (ongoing) |
|---|---|---|---|---|
| 1 — Local | 1,000 participants | $15,100 – $50,780 | $75 – $550 | $0.08 – $0.55 |
| 2 — Regional | 100,000 participants | $54,425 – $187,460 | $4,420 – $27,410 | $0.04 – $0.27 |
| 3 — National | 2,000,000 participants | $122,500 – $574,550 | $22,450 – $74,050 | $0.011 – $0.037 |

**Economies of scale are significant.** Per-participant cost falls by roughly 20× from
Tier 1 to Tier 3, driven primarily by fixed infrastructure costs spreading across a larger
base and the vote-batching optimisation eliminating per-vote gas overhead.

---

## Ethereum L2 vs L1: Why the Choice is Determinative

| Scenario | Gas price | Cost per ZK vote | Tier 2 annual vote gas |
|---|---|---|---|
| Ethereum mainnet | 30 gwei (typical) | **$36.00** | **$54,000,000/yr** |
| Ethereum mainnet | 5 gwei (low) | $6.00 | $9,000,000/yr |
| Base L2 | 0.01 gwei (high) | $0.012 | $18,000/yr |
| Base L2 | 0.001 gwei (baseline) | $0.0012 | **$1,800/yr** |
| Base L2 + vote batching | 0.001 gwei | ~$0.000001/vote | ~$150/yr |

Ethereum L1 makes anonymous civic voting economically impossible at any meaningful scale.
Base L2 (OP Stack) reduces per-vote gas cost by 3,000–30,000× compared to L1. This is
not a performance optimisation — it is what makes the system viable as civic infrastructure
rather than a toy demo.

The L2 is not a tradeoff against security: Base inherits Ethereum L1 finality (fraud proofs
write dispute windows to mainnet). The governance state is as secure as Ethereum; only the
per-transaction cost structure differs.

---

## Budget Planning by Deployment Stage

### Tier 1 Pilot (recommended budget)

```
Pre-launch (one-time):
  Smart contract audit:       $20,000 – $40,000
  Contract deployment + setup: $500 (includes Paymaster pre-fund)
  Total pre-launch:           $20,500 – $40,500

Year 1 operating:
  Paymaster top-up:           $200
  Infrastructure:             $350
  Total year 1 operating:     $550

Grant target (Tier 1):        $25,000 – $50,000
```

A $25,000 grant covers full Tier 1 launch including audit, with operating costs for 3+ years.

### Tier 2 (recommended budget)

```
Incremental audit (Semaphore + ZK circuit):  $50,000 – $160,000
Infrastructure scaling:                       $2,500 – $6,000/year
Paymaster fund:                               $5,000 – $25,000/year
Total year 1 (Tier 2 incremental):           $57,500 – $191,000

Grant target (Tier 2):  $100,000 – $250,000
```

### Tier 3 (recommended budget)

```
Formal verification + audit:   $100,000 – $500,000
Infrastructure:                $25,000 – $70,000/year
ZK batch prover workers:       included in infrastructure
Total year 1 (Tier 3):         $125,000 – $575,000

Grant target (Tier 3):  $500,000 – $2,000,000
(Government contract, EU Horizon, or Catalyst Fund at this scale)
```

---

## Cost Reduction Strategies

| Strategy | Applicable tier | Saving |
|---|---|---|
| **Vote batching** (Plonky2 recursion) | Tier 3 mandatory, Tier 2 optional | 99% reduction in vote gas |
| **PSE-sponsored Semaphore audit** | Tier 2 | Potentially $0 for ZK circuit review |
| **Base Ecosystem Fund** | All tiers | Covers deployment + operating costs |
| **Optimism RetroPGF** | After launch | Retroactive public goods funding |
| **Self-hosted Graph Node** | Tier 2+ | $0 vs $200/mo hosted |
| **Gitcoin Grants quadratic** | Tier 1 | Community funding amplification |
| **IPFS free tier (web3.storage)** | Tier 1 | $0 for first 5GB/month |

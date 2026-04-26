# PPG MVP — Financial Transparency Ledger

Source: paper §4.3 (Financial Transparency Ledger specification).

The Financial Transparency Ledger is the first deployable component of PPG. It has no
dependency on the governance pipeline or the identity module. It can be deployed and
delivering value in Tier 1 before any other component is built.

---

## Core Requirement

Every public financial flow must be recorded as a public, append-only, machine-readable
record within 24 hours of the authorising transaction. No record is ever deleted or modified.
The ledger is a **permanent public audit trail**, not a reporting interface.

---

## Data Storage Architecture

```mermaid
architecture-beta
    service writer(internet)["Authorised Body (Gnosis Safe 3-of-5)"]

    group l2["Primary On-Chain Layer (Base L2)"]
        service tableland(server)["Tableland Registry Contract — append-only SQL via L2 txs, INSERT-only"]
    end

    group archive["Permanent Archive Layer"]
        service arweave(disk)["Arweave (pay-once, 200+ yr) — full ledger snapshots, cannot be deleted"]
    end

    group content["Content Store"]
        service ipfs(disk)["IPFS / Filecoin — receipts and supporting documents, CID in ledger row"]
    end

    group cache["Cache Layer (Rebuild-Only)"]
        service postgres(database)["PostgreSQL 16 — rebuildable from chain, read-only app role, NOT source of truth"]
    end

    writer:B --> T:tableland
    writer:B --> T:ipfs
    writer:B --> T:arweave
    tableland:B --> T:postgres
```

The Tableland table is the **primary queryable ledger**. Arweave is the permanent archive.
IPFS is the content store for full record bodies. All three are public. None require trusting
the deploying organisation.

---

## Tableland Schema

Table name: `ppg_ledger_{chainId}_{tableId}` (assigned by Tableland on creation)

```sql
CREATE TABLE ppg_ledger (
  id          INTEGER   PRIMARY KEY,         -- auto-increment, assigned by Tableland
  entity      TEXT      NOT NULL,            -- public body name (e.g. "City of X - Treasury")
  amount      TEXT      NOT NULL,            -- decimal string, e.g. "125000.00"
  currency    TEXT      NOT NULL DEFAULT 'USD',
  counterparty TEXT     NOT NULL,            -- vendor / recipient name
  classification TEXT   NOT NULL,            -- e.g. "PROCUREMENT", "SALARY", "GRANT", "TRANSFER"
  authorised_at TEXT    NOT NULL,            -- ISO 8601 UTC timestamp of authorising decision
  recorded_at TEXT      NOT NULL,            -- ISO 8601 UTC timestamp of this record insertion
  reference   TEXT      NOT NULL,            -- internal reference number / contract ID
  description TEXT,                          -- human-readable purpose
  ipfs_cid    TEXT,                          -- CID of full record body on IPFS
  proposal_id TEXT                           -- on-chain proposalId if spend was governance-approved
);
```

**Append-only enforcement:** Tableland table policies are set to allow `INSERT` only from
the authorised writer address. `UPDATE` and `DELETE` are not granted to any address.
This is enforced at the Tableland contract level, not application code.

**Authorised writer:** A multisig (Gnosis Safe, 3-of-5 signers) deployed by the governing
body. For Tier 1, this is the only write path. In Tier 2, the PPGGovernor contract can also
write records when a governance-approved spend is executed.

---

## Record Validation Rules

Before any INSERT, the API layer validates:

| Field | Rule |
|---|---|
| `entity` | Non-empty. Must match registered entity list (on-chain registry). |
| `amount` | Parseable as positive decimal. Non-zero. |
| `currency` | ISO 4217 three-letter code. |
| `counterparty` | Non-empty. |
| `classification` | Must be one of: `PROCUREMENT`, `SALARY`, `GRANT`, `TRANSFER`, `REFUND`, `OTHER`. |
| `authorised_at` | Valid ISO 8601 UTC. Must not be in the future. |
| `recorded_at` | Must be within 24h of `authorised_at`. |
| `reference` | Non-empty. Globally unique within the entity's records. |

---

## API Endpoints

The API layer is a **read cache** — it queries The Graph and PostgreSQL for performance.
The source of truth is always the Tableland chain state.

### Public (no auth required)

```
GET /ledger
  Query params: entity, classification, from_date, to_date, counterparty, limit, offset
  Returns: paginated list of ledger records
  Source: PostgreSQL cache (rebuilable from Tableland)

GET /ledger/:id
  Returns: single record with IPFS content URL
  Source: PostgreSQL cache

GET /ledger/export
  Query params: format=csv|json|jsonl, entity, from_date, to_date
  Returns: full dataset download
  Source: PostgreSQL cache

GET /ledger/stats
  Returns: total spend by entity, by classification, by period
  Source: PostgreSQL cache

GET /ledger/verify/:id
  Returns: Tableland query result for this record (direct chain query, not cache)
  Use: anyone can independently verify a record against chain state
```

### Write (authorised multisig signers only)

```
POST /ledger
  Body: { entity, amount, currency, counterparty, classification,
          authorised_at, reference, description, attachments[] }
  Action:
    1. Validate fields
    2. Upload attachments + record body to IPFS → get CID
    3. Mirror to Arweave
    4. Submit Tableland INSERT transaction (signed by multisig)
    5. Insert into PostgreSQL cache on tx confirmation
  Returns: { id, tableland_tx_hash, ipfs_cid }
```

---

## PostgreSQL Cache Schema

```sql
-- Application role: SELECT, INSERT only. No UPDATE, DELETE.

CREATE TABLE ledger_cache (
  id             BIGINT        PRIMARY KEY,
  entity         TEXT          NOT NULL,
  amount         NUMERIC(20,6) NOT NULL,
  currency       CHAR(3)       NOT NULL DEFAULT 'USD',
  counterparty   TEXT          NOT NULL,
  classification TEXT          NOT NULL,
  authorised_at  TIMESTAMPTZ   NOT NULL,
  recorded_at    TIMESTAMPTZ   NOT NULL,
  reference      TEXT          NOT NULL,
  description    TEXT,
  ipfs_cid       TEXT,
  proposal_id    TEXT,
  tableland_tx   TEXT          NOT NULL,  -- L2 tx hash confirming this record
  chain_block    BIGINT        NOT NULL,  -- L2 block number
  created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX ON ledger_cache (entity);
CREATE INDEX ON ledger_cache (classification);
CREATE INDEX ON ledger_cache (authorised_at);
CREATE INDEX ON ledger_cache (counterparty);
CREATE UNIQUE INDEX ON ledger_cache (reference, entity);
```

---

## Rebuild From Chain Procedure

```bash
# 1. Query Tableland for all rows in ppg_ledger_{chainId}_{tableId}
# 2. INSERT each row into ledger_cache with chain_block from tx receipt
# 3. Verify row count matches Tableland SELECT COUNT(*)
# 4. Done — cache is consistent with chain state
```

This can be automated as a background job that runs on startup and after any detected gap
in the cache vs chain row count.

---

## Public Dashboard Requirements (Tier 1 UI)

The public ledger dashboard must be accessible without authentication and without
JavaScript where possible (progressive enhancement).

Minimum views:
1. **Full ledger table** — sortable, filterable, paginated
2. **Record detail** — all fields + link to IPFS content + link to Arweave archive + Tableland verify link
3. **Summary statistics** — total spend, spend by entity, spend by classification, monthly trend
4. **Export** — CSV and JSON download of full dataset or filtered subset
5. **Verify** — link from any record to the Tableland direct chain query proving the record
   is exactly what the chain says it is

---

## Compliance Notes

The 24-hour recording requirement is derived from paper §4.3. For Tier 1 pilots, this is
a policy commitment by the participating body. In Tier 2, the governance contract enforces
it: spending proposals that pass governance trigger automatic Tableland writes, removing
any manual recording step.

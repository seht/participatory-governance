# PPG MVP — Smart Contract Interface Specifications

All contracts deployed on Base mainnet. Development and testing on Base Sepolia.
Build tool: Foundry (`forge build`, `forge test`, `forge script`).
Contract framework: OpenZeppelin Contracts v5, Semaphore v4.

---

## Contract Deployment Order

```
1. PPGToken               (ERC20Votes — governance weight token)
2. PPGTimelockController  (OZ TimelockController)
3. PPGGovernor            (OZ Governor + dynamic quorum + Semaphore votes)
4. SemaphoreGroupRegistry (Semaphore v4 — deployed by PSE, use existing instance)
5. LedgerWriter           (Gnosis Safe multisig — authorised Tableland writer)
```

---

## PPGToken

Governance weight token. Non-transferable in Tier 1 (Soulbound-lite: transfers disabled
except by admin to enforce one-citizen-one-token for small pilots).

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

interface IPPGToken {

    // ── Roles ────────────────────────────────────────────────────────────────
    function MINTER_ROLE() external view returns (bytes32);
    function TRANSFER_ADMIN_ROLE() external view returns (bytes32);

    // ── Minting ──────────────────────────────────────────────────────────────
    /// @notice Mint one governance token to an eligible citizen.
    ///         Callable only by MINTER_ROLE (the election authority multisig).
    /// @param  to      Citizen wallet address.
    /// @param  amount  Always 1e18 (1 token) in Tier 1.
    function mint(address to, uint256 amount) external;

    // ── Transfer restriction ─────────────────────────────────────────────────
    /// @notice In Tier 1, all transfers are disabled except by TRANSFER_ADMIN_ROLE.
    ///         This enforces one-citizen-one-token without ZK identity.
    ///         TRANSFER_ADMIN_ROLE MUST be held by the PPGTimelockController address,
    ///         not by an EOA. This ensures transfers can only be re-enabled through
    ///         a passed governance proposal, not by a single operator.
    function setTransfersEnabled(bool enabled) external;

    // ── Delegation (required for Governor) ───────────────────────────────────
    /// @notice Citizen must self-delegate to activate voting weight.
    ///         Called automatically on mint if autoDelegate is true.
    function delegate(address delegatee) external;

    // ── ERC20Votes snapshot ───────────────────────────────────────────────────
    /// @notice Returns voting weight at a historical block (used by Governor).
    function getPastVotes(address account, uint256 blockNumber)
        external view returns (uint256);

    function getPastTotalSupply(uint256 blockNumber)
        external view returns (uint256);
}
```

---

## PPGTimelockController

Standard OZ TimelockController. The Governor is the only proposer. Anyone can execute
after the delay.

```solidity
// Constructor parameters:
constructor(
    uint256 minDelay,       // 2 days (172800 seconds) — mandatory execution delay
    address[] proposers,    // [address(PPGGovernor)]
    address[] executors,    // [address(0)] — anyone can execute after delay
    address admin           // address(0) — no admin after deployment
)
```

`admin = address(0)` means no one can bypass the timelock after deployment.
The timelock itself is governed — the Governor can change `minDelay` via proposal.

---

## PPGGovernor

Extends OZ Governor with:
- Dynamic quorum ($Q(i) = Q_{\text{base}} + \alpha \cdot \sigma(i)$)
- Anonymous voting via Semaphore (Tier 2+)
- Per-proposal impact score (set by `IMPACT_ASSESSOR_ROLE`, not by the proposer)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IPPGGovernor {

    // ── Constitutional validation (Tier 2+ — VALIDATED state) ───────────────

    /// @notice Record the outcome of off-chain constitutional review for a proposal.
    ///         Callable only by VALIDATOR_ROLE (the constitutional review multisig).
    ///         In Tier 1 this function is absent — the VALIDATED state is skipped.
    ///         In Tier 2, the Governor gates the transition from DELIBERATION to VOTING:
    ///         voting can only open once constitutionallyValid(proposalId) == true.
    ///         If called with passed = false, the proposal is cancelled.
    ///
    ///         The reviewHash is keccak256(abi.encode(proposalId, reviewerAddress,
    ///         reviewTimestamp, outcome, ipfsCidOfReviewReport)). This binds the
    ///         on-chain record to the full off-chain review document on IPFS.
    ///
    /// @param  proposalId  The proposal under review.
    /// @param  reviewHash  Hash of the full review record (see above).
    /// @param  passed      True if the proposal passed constitutional validation.
    function setConstitutionalValidation(
        uint256 proposalId,
        bytes32 reviewHash,
        bool passed
    ) external;

    /// @notice Returns the constitutional review hash for a proposal (zero if not yet reviewed).
    function constitutionalReviewHash(uint256 proposalId) external view returns (bytes32);

    /// @notice Returns whether a proposal passed constitutional validation.
    function constitutionallyValid(uint256 proposalId) external view returns (bool);

    // ── Proposal submission ───────────────────────────────────────────────────

    /// @notice Submit a governance proposal.
    /// @param  targets       Contract addresses to call on execution.
    /// @param  values        ETH values for each call.
    /// @param  calldatas     Encoded function calls for each target.
    /// @param  description   Human-readable description. Must include IPFS CID.
    ///                       Format: "ipfs:CID | impact:NNN | title:..."
    ///                       NNN = impact score in basis points (0–10000).
    /// @return proposalId    Unique ID for this proposal.
    function propose(
        address[] calldata targets,
        uint256[] calldata values,
        bytes[] calldata calldatas,
        string calldata description
    ) external returns (uint256 proposalId);

    // ── Standard voting (Tier 1 — pseudonymous) ───────────────────────────────

    /// @notice Cast a vote. Voter address is recorded.
    /// @param  proposalId  Target proposal.
    /// @param  support     0=Against, 1=For, 2=Abstain.
    /// @return weight      Voting weight applied.
    function castVote(uint256 proposalId, uint8 support)
        external returns (uint256 weight);

    /// @notice Cast a vote with a reason string (stored as event).
    function castVoteWithReason(
        uint256 proposalId,
        uint8 support,
        string calldata reason
    ) external returns (uint256 weight);

    // ── Anonymous voting (Tier 2 — Semaphore) ────────────────────────────────

    /// @notice Cast a vote anonymously using a Semaphore ZK proof.
    ///         Voter identity is NOT recorded. Only the nullifier hash is stored.
    /// @param  proposalId      Target proposal (also used as Semaphore external nullifier).
    /// @param  support         0=Against, 1=For, 2=Abstain.
    /// @param  merkleTreeRoot  Current root of the eligible-citizens Semaphore group.
    /// @param  nullifierHash   hash(identity.nullifier || proposalId) — unique per voter per proposal.
    /// @param  proof           Groth16 ZK proof bytes (packed uint256[8]).
    function castVoteAnonymous(
        uint256 proposalId,
        uint8 support,
        uint256 merkleTreeRoot,
        uint256 nullifierHash,
        uint256[8] calldata proof
    ) external;

    // ── Execution ─────────────────────────────────────────────────────────────

    /// @notice Queue a passed proposal into the timelock.
    function queue(
        address[] calldata targets,
        uint256[] calldata values,
        bytes[] calldata calldatas,
        bytes32 descriptionHash
    ) external returns (uint256 proposalId);

    /// @notice Execute a queued proposal after the timelock delay.
    function execute(
        address[] calldata targets,
        uint256[] calldata values,
        bytes[] calldata calldatas,
        bytes32 descriptionHash
    ) external payable returns (uint256 proposalId);

    /// @notice Cancel a proposal (proposer or guardian only, before execution).
    function cancel(
        address[] calldata targets,
        uint256[] calldata values,
        bytes[] calldata calldatas,
        bytes32 descriptionHash
    ) external returns (uint256 proposalId);

    // ── Veto (Tier 2+) ────────────────────────────────────────────────────────

    /// @notice Sign a veto petition for an executed proposal.
    ///         If veto threshold reached, a re-vote is triggered automatically.
    /// @param  proposalId  The executed proposal to veto-petition.
    function signVetoPetition(uint256 proposalId) external;

    /// @notice Anonymously sign a veto petition (Semaphore proof).
    function signVetoPetitionAnonymous(
        uint256 proposalId,
        uint256 merkleTreeRoot,
        uint256 nullifierHash,
        uint256[8] calldata proof
    ) external;

    // ── Dynamic quorum & impact score ────────────────────────────────────────

    /// @notice Returns the base quorum (in token units) for a given timepoint.
    ///         This is a display-only value. The binding dynamic-quorum check
    ///         is performed in _quorumReached(proposalId) at execution time.
    function quorum(uint256 timepoint) external view returns (uint256);

    /// @notice Returns the impact score (basis points) for a proposal.
    ///         Defaults to 0 (base quorum only) until set by IMPACT_ASSESSOR_ROLE.
    function proposalImpact(uint256 proposalId) external view returns (uint256);

    /// @notice Set the impact score for a proposal.
    ///         Callable only by IMPACT_ASSESSOR_ROLE (governance council multisig).
    ///         Must be called before the voting period opens; reverts otherwise.
    ///         impactBps is in basis points (0 = no uplift, 10000 = max uplift).
    ///         Impact score can only raise quorum above the baseline — the formula
    ///         Q(i) = Qbase + α × σ(i) has a natural floor at Qbase.
    /// @param  proposalId  Target proposal.
    /// @param  impactBps   Impact score (0–10000 basis points).
    function setProposalImpact(uint256 proposalId, uint256 impactBps) external;

    function IMPACT_ASSESSOR_ROLE() external view returns (bytes32);

    // ── Governance parameters (adjustable via governance) ─────────────────────

    /// @notice Baseline quorum numerator in basis points (default: 400 = 4%).
    function quorumBaseNumerator() external view returns (uint256);

    /// @notice Quorum sensitivity parameter alpha in basis points (default: 1000 = 10%).
    function quorumAlpha() external view returns (uint256);

    /// @notice Approval threshold numerator in basis points (default: 5000 = 50%).
    function approvalThresholdNumerator() external view returns (uint256);

    /// @notice Veto threshold numerator in basis points (default: 1000 = 10%).
    function vetoThresholdNumerator() external view returns (uint256);

    // ── State inspection ──────────────────────────────────────────────────────

    function proposalSnapshot(uint256 proposalId) external view returns (uint256);
    function proposalDeadline(uint256 proposalId) external view returns (uint256);
    function proposalVotes(uint256 proposalId)
        external view returns (uint256 againstVotes, uint256 forVotes, uint256 abstainVotes);
    function state(uint256 proposalId) external view returns (ProposalState);

    enum ProposalState {
        Pending,     // DRAFT — within voting delay
        Active,      // VOTING — within voting period
        Canceled,
        Defeated,    // Failed quorum or approval threshold
        Succeeded,   // Passed, awaiting queue
        Queued,      // In timelock
        Expired,     // Queued but not executed in time
        Executed     // EXECUTED
    }

    /// @notice Tier 2+ constitutional validation state — tracked in a parallel mapping
    ///         alongside (not replacing) OZ ProposalState.
    ///         In Tier 1 this mapping is never written; all proposals are None.
    ///
    ///         Lifecycle:
    ///           propose() called              → state remains None
    ///           votingDelay expires (Tier 2)  → Governor sets AwaitingValidation automatically
    ///           setConstitutionalValidation(passed=true)  → Validated (voting can open)
    ///           setConstitutionalValidation(passed=false) → Failed (proposal is Canceled)
    ///
    ///         The Governor's _castVote() hook rejects votes when validationState is
    ///         AwaitingValidation or Failed, even if OZ ProposalState is Active.
    enum ValidationState {
        None,               // Tier 1 / not yet in deliberation
        AwaitingValidation, // Deliberation ended; constitutional review in progress
        Validated,          // Review passed; voting may open
        Failed              // Review failed; proposal cancelled
    }

    /// @notice Returns the Tier 2+ constitutional validation state for a proposal.
    function validationState(uint256 proposalId) external view returns (ValidationState);

    // ── Events ────────────────────────────────────────────────────────────────

    event ConstitutionalValidationRecorded(
        uint256 indexed proposalId,
        bytes32 reviewHash,
        bool passed
    );

    event ProposalCreated(
        uint256 indexed proposalId,
        address indexed proposer,
        string description,          // includes IPFS CID and impact score
        uint256 impactScore,
        uint256 startBlock,
        uint256 endBlock
    );

    event VoteCast(
        address indexed voter,       // address(0) for anonymous votes
        uint256 indexed proposalId,
        uint8 support,
        uint256 weight,
        string reason
    );

    event VoteCastAnonymous(
        uint256 indexed proposalId,
        uint8 support,
        uint256 nullifierHash        // NOT linked to voter identity
    );

    event ProposalImpactSet(
        uint256 indexed proposalId,
        uint256 impactBps,
        address assessor
    );

    event ValidationStateChanged(
        uint256 indexed proposalId,
        ValidationState newState
    );

    event VetoPetitionSigned(
        uint256 indexed proposalId,
        uint256 petitionCount,
        uint256 threshold
    );

    event ProposalVetoed(uint256 indexed proposalId);
}
```

---

## PPGSemaphoreGroupRegistry

Uses the existing Semaphore v4 contract deployed by PSE on Base. Do not redeploy.
The PPGGovernor stores the `groupId` of the eligible-citizens group and verifies proofs
against it.

```solidity
// Reference interface (Semaphore v4 — use deployed instance)
interface ISemaphore {
    function createGroup() external returns (uint256 groupId);
    function addMember(uint256 groupId, uint256 identityCommitment) external;
    function removeMember(
        uint256 groupId,
        uint256 identityCommitment,
        uint256[] calldata merkleProofSiblings
    ) external;
    function validateProof(
        uint256 groupId,
        SemaphoreProof calldata proof
    ) external;
    function verifyProof(
        uint256 groupId,
        SemaphoreProof calldata proof
    ) external view returns (bool);
}

struct SemaphoreProof {
    uint256 merkleTreeDepth;
    uint256 merkleTreeRoot;
    uint256 nullifier;
    uint256 message;        // vote choice encoded as uint256
    uint256 scope;          // proposalId
    uint256[8] points;      // Groth16 proof
}
```

---

## LedgerWriter (Gnosis Safe multisig)

Not a custom contract. Deploy a Gnosis Safe with the election authority signers.
This multisig is the only address authorised to write to the Tableland Financial Ledger table.

```
Signers:     3-of-5 from election/treasury authority
Chain:       Base mainnet
Contract:    Gnosis Safe v1.4 (use Safe{Wallet} interface for deployment)
```

For Tier 2, the PPGGovernor TimelockController is added as an additional authorised writer,
so governance-approved spends automatically write to the ledger on execution.

---

## Constructor Parameters Summary

```solidity
// PPGToken
PPGToken(
    string name = "PPG Governance Token",
    string symbol = "PPG",
    address admin           // election authority multisig
)

// Post-deployment role assignments (PPGGovernor)
// These roles are not set in the constructor — grant after deployment via AccessControl:
//
//   VALIDATOR_ROLE        → constitutional review multisig (Tier 2+ only)
//                           In Tier 1: leave ungranted — setConstitutionalValidation() is unused
//   IMPACT_ASSESSOR_ROLE  → governance council multisig
//                           In Tier 1: leave ungranted — proposalImpact defaults to 0 (base quorum)
//
// Both roles are grantable/revokable only by the PPGTimelockController address,
// so any role change requires a passed governance proposal.

// PPGTimelockController
PPGTimelockController(
    uint256 minDelay = 2 days,
    address[] proposers = [address(governor)],  // set after governor deploy
    address[] executors = [address(0)],          // anyone
    address admin = address(0)                   // no admin
)

// PPGGovernor
PPGGovernor(
    IVotes token = address(PPGToken),
    TimelockController timelock = address(PPGTimelockController),
    string name = "PPG Governor",
    uint48 votingDelay = 7 days,     // recommended for production; use 1 day for testnet/pilot only
    uint32 votingPeriod = 7 days,
    uint256 proposalThreshold = 1e18,
    uint256 quorumBaseNumerator = 400,   // 4%
    uint256 quorumAlpha = 1000,          // 10%
    ISemaphore semaphore = address(0),   // set to PSE Semaphore address in Tier 2
    uint256 semaphoreGroupId = 0         // set after group creation in Tier 2
)
```

---

## Security Notes

- **No upgrade proxies in Tier 1.** Contracts are immutable. Upgrades require a new deployment
  voted in by governance. This is the strongest trust model — no admin can silently change logic.
- **TimelockController admin is address(0).** After deployment, no one can bypass the timelock.
  Even the deployer has no special privileges.
- **PPGToken MINTER_ROLE held by multisig.** No single key can mint tokens.
- **Semaphore nullifier uniqueness.** The contract MUST revert on duplicate nullifier hash.
  This is the double-vote prevention mechanism. Do not add any exception.
- **No ETH stored in Governor.** Proposal execution values are forwarded to targets, not held.
- **Foundry testing requirement.** 100% branch coverage on quorum calculation, vote counting,
  and nullifier deduplication before mainnet deployment. Use `forge coverage`.

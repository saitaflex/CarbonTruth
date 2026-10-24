// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title CarbonTruth Verified Climate Claim (VCC) registry
/// @notice Mints a non-transferable-by-default climate credit only after the
///         off-chain oracle has reached consensus. Enforces the two integrity
///         invariants from the protocol:
///           1. Uniqueness  — one token per geo-temporal fingerprint, so a tonne
///                            can never be double-counted.
///           2. Retire-once — a credit moves active -> retired exactly once and
///                            can never be re-activated.
///         The evidence hash anchors the full verification bundle (satellite
///         scene IDs, model version/hash, fused estimate, confidence) so any
///         mint is reproducible and tamper-evident.
/// @dev    Deploy to any EVM testnet (e.g. Sepolia). Minimal + dependency-free
///         so it compiles in Remix with no imports. A production build would
///         extend ERC-721 and add role-based access / a validator set.
contract CarbonTruthVCC {
    address public immutable issuer;          // the verification authority
    uint16  public constant THETA_BPS = 9000; // confidence gate: 90.00%

    enum Status { None, Active, Retired }

    struct VCC {
        uint256 id;
        bytes32 fingerprint;   // keccak256(geohash || date || projectId || tonneIndex)
        bytes32 evidenceHash;  // keccak256 of the verification bundle
        uint256 tonnes;        // verified tCO2e (integer tonnes)
        uint16  confidenceBps; // consensus confidence, basis points (e.g. 9680 = 96.80%)
        string  projectId;
        uint64  vintage;       // observation date, unix seconds
        Status  status;
        address owner;
    }

    uint256 public nextId = 1;
    mapping(bytes32 => bool)    public fingerprintUsed;  // uniqueness guard
    mapping(uint256 => VCC)     public credits;
    mapping(bytes32 => uint256) public idOfFingerprint;

    event Minted(uint256 indexed id, bytes32 indexed fingerprint, uint256 tonnes,
                 uint16 confidenceBps, bytes32 evidenceHash, address owner);
    event Retired(uint256 indexed id, bytes32 indexed fingerprint, address by);

    modifier onlyIssuer() {
        require(msg.sender == issuer, "not issuer");
        _;
    }

    constructor() {
        issuer = msg.sender;
    }

    /// @notice Mint a VCC. Reverts on a reused fingerprint (double-count blocked)
    ///         or a confidence below the gate.
    function mint(
        bytes32 fingerprint,
        bytes32 evidenceHash,
        uint256 tonnes,
        uint16  confidenceBps,
        string calldata projectId,
        uint64  vintage,
        address to
    ) external onlyIssuer returns (uint256 id) {
        require(!fingerprintUsed[fingerprint], "duplicate fingerprint");
        require(confidenceBps >= THETA_BPS, "below confidence gate");
        require(tonnes > 0, "zero tonnes");

        id = nextId++;
        fingerprintUsed[fingerprint] = true;
        idOfFingerprint[fingerprint] = id;
        credits[id] = VCC({
            id: id,
            fingerprint: fingerprint,
            evidenceHash: evidenceHash,
            tonnes: tonnes,
            confidenceBps: confidenceBps,
            projectId: projectId,
            vintage: vintage,
            status: Status.Active,
            owner: to
        });
        emit Minted(id, fingerprint, tonnes, confidenceBps, evidenceHash, to);
    }

    /// @notice Retire a credit exactly once. The owner or issuer may retire.
    function retire(uint256 id) external {
        VCC storage c = credits[id];
        require(c.status == Status.Active, "not active");
        require(msg.sender == c.owner || msg.sender == issuer, "not permitted");
        c.status = Status.Retired;
        emit Retired(id, c.fingerprint, msg.sender);
    }

    /// @notice Helper so off-chain code and chain agree on the fingerprint rule.
    function computeFingerprint(
        string calldata geohash,
        string calldata date,
        string calldata projectId,
        uint256 tonneIndex
    ) external pure returns (bytes32) {
        return keccak256(abi.encodePacked(geohash, "|", date, "|", projectId, "|", tonneIndex));
    }

    function isRetired(uint256 id) external view returns (bool) {
        return credits[id].status == Status.Retired;
    }
}

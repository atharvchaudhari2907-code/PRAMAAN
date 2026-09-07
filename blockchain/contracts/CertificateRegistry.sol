// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CertificateRegistry
 * @dev Bureau of Indian Standards (BIS) Tamper-Evident Certification Registry.
 * Anchors cryptographic hashes of certificates, document dossiers, and IPFS CIDs.
 * Sensitive manufacturer documents are never stored on-chain; only immutable hashes.
 */
contract CertificateRegistry {
    address public owner;

    enum CertificateStatus {
        PENDING,
        ACTIVE,
        SUSPENDED,
        EXPIRED,
        REVOKED
    }

    struct CertificateRecord {
        string certificateId;
        bytes32 recordHash;
        bytes32 documentHash;
        string ipfsCid;
        string issuer;
        CertificateStatus status;
        uint256 issuedAt;
        uint256 blockNumber;
        bool exists;
    }

    mapping(string => CertificateRecord) private certificates;
    mapping(address => bool) public authorizedIssuers;

    event CertificateRegistered(
        string indexed certificateId,
        bytes32 indexed recordHash,
        bytes32 documentHash,
        string ipfsCid,
        string issuer,
        uint256 issuedAt,
        uint256 blockNumber
    );

    event CertificateStatusUpdated(
        string indexed certificateId,
        CertificateStatus oldStatus,
        CertificateStatus newStatus,
        uint256 updatedBlock
    );

    event IssuerAuthorized(address indexed issuer, bool status);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only registry owner can execute");
        _;
    }

    modifier onlyIssuer() {
        require(msg.sender == owner || authorizedIssuers[msg.sender], "Unauthorized: Caller is not a certified BIS issuer");
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedIssuers[msg.sender] = true;
    }

    function setAuthorizedIssuer(address issuer, bool authorized) external onlyOwner {
        require(issuer != address(0), "Invalid issuer address");
        authorizedIssuers[issuer] = authorized;
        emit IssuerAuthorized(issuer, authorized);
    }

    /**
     * @notice Registers a new certified product record in the immutable registry.
     */
    function registerCertificate(
        string calldata certId,
        bytes32 recordHash,
        bytes32 documentHash,
        string calldata ipfsCid,
        string calldata issuer
    ) external onlyIssuer {
        require(bytes(certId).length > 0, "Certificate ID cannot be empty");
        require(recordHash != bytes32(0), "Record hash cannot be null");
        require(!certificates[certId].exists, "Certificate already registered");

        certificates[certId] = CertificateRecord({
            certificateId: certId,
            recordHash: recordHash,
            documentHash: documentHash,
            ipfsCid: ipfsCid,
            issuer: issuer,
            status: CertificateStatus.ACTIVE,
            issuedAt: block.timestamp,
            blockNumber: block.number,
            exists: true
        });

        emit CertificateRegistered(
            certId,
            recordHash,
            documentHash,
            ipfsCid,
            issuer,
            block.timestamp,
            block.number
        );
    }

    /**
     * @notice Updates status of an existing certificate (e.g. SUSPENDED, EXPIRED, REVOKED).
     */
    function updateCertificateStatus(
        string calldata certId,
        CertificateStatus newStatus
    ) external onlyIssuer {
        require(certificates[certId].exists, "Certificate does not exist");
        CertificateStatus old = certificates[certId].status;
        certificates[certId].status = newStatus;

        emit CertificateStatusUpdated(certId, old, newStatus, block.number);
    }

    /**
     * @notice Retrieves the stored on-chain record for a certificate.
     */
    function getCertificate(
        string calldata certId
    )
        external
        view
        returns (
            bytes32 recordHash,
            bytes32 documentHash,
            string memory ipfsCid,
            string memory issuer,
            CertificateStatus status,
            uint256 issuedAt,
            uint256 blockNumber
        )
    {
        require(certificates[certId].exists, "Certificate not found");
        CertificateRecord storage cert = certificates[certId];
        return (
            cert.recordHash,
            cert.documentHash,
            cert.ipfsCid,
            cert.issuer,
            cert.status,
            cert.issuedAt,
            cert.blockNumber
        );
    }

    /**
     * @notice Verifies if a computed record hash exactly matches the on-chain anchored hash.
     */
    function verifyCertificate(
        string calldata certId,
        bytes32 recordHash
    ) external view returns (bool isValid, CertificateStatus currentStatus) {
        if (!certificates[certId].exists) {
            return (false, CertificateStatus.PENDING);
        }
        CertificateRecord storage cert = certificates[certId];
        bool matches = (cert.recordHash == recordHash);
        return (matches, cert.status);
    }
}

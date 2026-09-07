"""
Deployment and verification script for CertificateRegistry smart contract on Polygon Amoy or local EVM.
"""
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Standard pre-compiled ABI for CertificateRegistry
CERTIFICATE_REGISTRY_ABI = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "certificateId", "type": "string"},
            {"indexed": True, "name": "recordHash", "type": "bytes32"},
            {"indexed": False, "name": "documentHash", "type": "bytes32"},
            {"indexed": False, "name": "ipfsCid", "type": "string"},
            {"indexed": False, "name": "issuer", "type": "string"},
            {"indexed": False, "name": "issuedAt", "type": "uint256"},
            {"indexed": False, "name": "blockNumber", "type": "uint256"}
        ],
        "name": "CertificateRegistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "certificateId", "type": "string"},
            {"indexed": False, "name": "oldStatus", "type": "uint8"},
            {"indexed": False, "name": "newStatus", "type": "uint8"},
            {"indexed": False, "name": "updatedBlock", "type": "uint256"}
        ],
        "name": "CertificateStatusUpdated",
        "type": "event"
    },
    {
        "inputs": [
            {"name": "certId", "type": "string"},
            {"name": "recordHash", "type": "bytes32"},
            {"name": "documentHash", "type": "bytes32"},
            {"name": "ipfsCid", "type": "string"},
            {"name": "issuer", "type": "string"}
        ],
        "name": "registerCertificate",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "certId", "type": "string"},
            {"name": "newStatus", "type": "uint8"}
        ],
        "name": "updateCertificateStatus",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "certId", "type": "string"}],
        "name": "getCertificate",
        "outputs": [
            {"name": "recordHash", "type": "bytes32"},
            {"name": "documentHash", "type": "bytes32"},
            {"name": "ipfsCid", "type": "string"},
            {"name": "issuer", "type": "string"},
            {"name": "status", "type": "uint8"},
            {"name": "issuedAt", "type": "uint256"},
            {"name": "blockNumber", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "certId", "type": "string"},
            {"name": "recordHash", "type": "bytes32"}
        ],
        "name": "verifyCertificate",
        "outputs": [
            {"name": "isValid", "type": "bool"},
            {"name": "currentStatus", "type": "uint8"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


def export_abi():
    abi_path = Path(__file__).resolve().parent.parent / "CertificateRegistry.json"
    with open(abi_path, "w", encoding="utf-8") as f:
        json.dump({"abi": CERTIFICATE_REGISTRY_ABI}, f, indent=2)
    print(f"Exported ABI to {abi_path}")


if __name__ == "__main__":
    export_abi()

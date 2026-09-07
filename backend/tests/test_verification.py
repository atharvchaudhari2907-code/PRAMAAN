import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_trust_ledger_and_verification(client: AsyncClient):
    # 1. Create a Trust Ledger Record
    create_res = await client.post(
        "/api/trust-ledger/records",
        json={
            "product_name": "Premium Smart LED Lamp",
            "manufacturer": "Bharat Electronics Ltd",
            "model": "BEL-LED-09",
            "standard_id": "IS 16102 (Part 1) : 2012",
            "standard_title": "Self-Ballasted LED Lamps Safety Requirements",
            "standard_version": "2012",
            "certificate_id": "CM/L-87654321",
            "certification_status": "ACTIVE",
            "issuer": "Bureau of Indian Standards",
        },
    )
    assert create_res.status_code == 201
    ledger_data = create_res.json()
    assert ledger_data["certificate_id"] == "CM/L-87654321"
    assert ledger_data["record_hash"] is not None
    pub_id = ledger_data["public_product_id"]

    # 2. List Trust Ledger Records
    list_res = await client.get("/api/trust-ledger/records")
    assert list_res.status_code == 200
    records = list_res.json()
    assert any(r["certificate_id"] == "CM/L-87654321" for r in records)

    # 3. Lookup by Public Product ID
    get_res = await client.get(f"/api/trust-ledger/records/{pub_id}")
    assert get_res.status_code == 200
    assert get_res.json()["public_product_id"] == pub_id

    # 4. Verify Valid Hash
    valid_hash = ledger_data["record_hash"]
    verify_res = await client.post(
        "/api/verification/verify-hash",
        json={"sha256_hash": valid_hash},
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_verified"] is True
    assert verify_data["integrity_status"] == "VALID_RECORD"

    # 5. Verify Invalid / Unknown Hash
    fake_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    unknown_res = await client.post(
        "/api/verification/verify-hash",
        json={"sha256_hash": fake_hash},
    )
    assert unknown_res.status_code == 200
    unknown_data = unknown_res.json()
    assert unknown_data["is_verified"] is False
    assert unknown_data["integrity_status"] == "UNKNOWN_RECORD"

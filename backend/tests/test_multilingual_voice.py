import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.user import User
from app.services.voice_service import SUPPORTED_LANGUAGES, VoiceService


@pytest.mark.asyncio
async def test_supported_languages_coverage():
    """Verifies that all 12 specified Indian languages are present in the service definition."""
    required_codes = {"en", "hi", "mr", "bn", "gu", "ta", "te", "kn", "ml", "pa", "or", "as"}
    assert required_codes.issubset(set(SUPPORTED_LANGUAGES.keys()))
    assert len(SUPPORTED_LANGUAGES) >= 12


@pytest.mark.asyncio
async def test_voice_languages_endpoint(client: AsyncClient):
    """Verifies GET /api/applications/voice/languages returns the 12 languages."""
    res = await client.get("/api/applications/voice/languages")
    assert res.status_code == 200
    languages = res.json()
    assert "hi" in languages
    assert "mr" in languages
    assert "ta" in languages
    assert "bn" in languages
    assert "as" in languages
    assert len(languages) >= 12


@pytest.mark.asyncio
async def test_multilingual_voice_service_query(db_session: AsyncSession):
    """Verifies VoiceService processes queries and provides grounded responses."""
    user = User(
        email="voice_tester@acme.in",
        hashed_password="pw_hash_test",
        full_name="Voice User",
        role="manufacturer",
        company_name="Acme Audio",
    )
    db_session.add(user)
    await db_session.flush()

    app = Application(
        user_id=user.id,
        application_number="BIS-2026-770001",
        product_name="Electric Food Mixer",
        category="Kitchen Appliances",
        manufacturer="Acme Audio",
        model_number="MIX-2026",
        primary_standard_id="IS 302 (Part 1)",
        status=ApplicationStatus.DRAFT,
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)

    voice_service = VoiceService(db_session)

    # Test Hindi Query
    hi_result = await voice_service.process_voice_query(
        application_id=app.id,
        user_id=user.id,
        query_text="क्या मेरे आवेदन में कोई दस्तावेज बाकी हैं?",
        language_code="hi",
    )
    assert hi_result["language_code"] == "hi"
    assert hi_result["language_name"] == "Hindi (हिंदी)"
    assert len(hi_result["response"]) > 0

    # Test Marathi Query
    mr_result = await voice_service.process_voice_query(
        application_id=app.id,
        user_id=user.id,
        query_text="माझ्या उत्पादनाचे मानके कोणती आहेत?",
        language_code="mr",
    )
    assert mr_result["language_code"] == "mr"
    assert mr_result["language_name"] == "Marathi (मराठी)"
    assert len(mr_result["response"]) > 0

    # Test Tamil Query
    ta_result = await voice_service.process_voice_query(
        application_id=app.id,
        user_id=user.id,
        query_text="விண்ணப்ப நிலை என்ன?",
        language_code="ta",
    )
    assert ta_result["language_code"] == "ta"
    assert ta_result["language_name"] == "Tamil (தமிழ்)"
    assert len(ta_result["response"]) > 0

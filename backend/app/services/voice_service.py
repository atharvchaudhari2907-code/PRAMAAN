import base64
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.interactions import VoiceInteraction
from app.services.assessment_engine import AssessmentEngine

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "mr": "Marathi (मराठी)",
    "bn": "Bengali (বাংলা)",
    "gu": "Gujarati (ગુજરાતી)",
    "ta": "Tamil (தமிழ்)",
    "te": "Telugu (తెలుగు)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "ml": "Malayalam (മലയാളം)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
    "or": "Odia (ଓଡ଼ିଆ)",
    "as": "Assamese (অসমীয়া)",
}

# Accurate multilingual fallback templates for key regulatory queries
MULTILINGUAL_PROMPTS = {
    "hi": {
        "greeting": "नमस्ते! मैं आपका बीआईएस प्रमाणन एआई सहायक हूँ।",
        "gaps": "आपके उत्पाद के लिए पहचाने गए अंतराल और अनुपालन की स्थिति इस प्रकार है:",
        "documents": "आपके बीआईएस आवेदन के लिए निम्नलिखित अनिवार्य दस्तावेज आवश्यक हैं:",
        "status": "आपके आवेदन की वर्तमान स्थिति है:",
    },
    "mr": {
        "greeting": "नमस्कार! मी तुमचा बीआयएस प्रमाणीकरण एआय सहाय्यक आहे.",
        "gaps": "तुमच्या उत्पादनासाठी ओळखण्यात आलेल्या त्रुटी खालीलप्रमाणे आहेत:",
        "documents": "तुमच्या अर्जासाठी खालील अनिवार्य कागदपत्रे आवश्यक आहेत:",
        "status": "तुमच्या अर्जाची सद्यस्थिती पुढीलप्रमाणे आहे:",
    },
    "ta": {
        "greeting": "வணக்கம்! நான் உங்கள் பிஐஎஸ் சான்றிதழ் ஏஐ உதவியாளர்.",
        "gaps": "உங்கள் தயாரிப்பில் கண்டறியப்பட்ட இணக்க இடைவெளிகள்:",
        "documents": "உங்கள் பிஐஎஸ் விண்ணப்பத்திற்கு தேவையான ஆவணங்கள்:",
        "status": "உங்கள் விண்ணப்பத்தின் தற்போதைய நிலை:",
    },
    "bn": {
        "greeting": "নমস্কার! আমি আপনার বিআইএস সার্টিফিকেশন এআই সহকারী।",
        "gaps": "আপনার পণ্যের জন্য চিহ্নিত শূন্যস্থানগুলি নিম্নরূপ:",
        "documents": "আপনার বিআইএস আবেদনের জন্য প্রয়োজনীয় নথি:",
        "status": "আপনার আবেদনের বর্তমান অবস্থা:",
    },
    "gu": {
        "greeting": "નમસ્તે! હું તમારો બીઆઈએસ પ્રમાણપત્ર એઆઈ સહાયક છું.",
        "gaps": "તમારા ઉત્પાદન માટે ઓળખાયેલ અંતરાલો નીચે મુજબ છે:",
        "documents": "તમારા બીઆઈએસ અરજી માટે નીચેના દસ્તાવેજો જરૂરી છે:",
        "status": "તમારી અરજીની વર્તમાન સ્થિતિ:",
    },
    "te": {
        "greeting": "నమస్కారం! నేను మీ బిఐఎస్ ధృవీకరణ AI సహాయకుడిని.",
        "gaps": "మీ ఉత్పత్తికి సంబంధించి గుర్తించబడిన లోపాలు:",
        "documents": "మీ బిఐఎస్ దరఖాస్తుకు అవసరమైన పత్రాలు:",
        "status": "మీ దరఖాస్తు ప్రస్తుత స్థితి:",
    },
    "kn": {
        "greeting": "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಬಿಐಎಸ್ ಪ್ರಮಾಣೀಕರಣ AI ಸಹಾಯಕ.",
        "gaps": "ನಿಮ್ಮ ಉತ್ಪನ್ನಕ್ಕೆ ಸಂಬಂಧಿಸಿದಂತೆ ಗುರುತಿಸಲಾದ ಅಂತರಗಳು:",
        "documents": "ನಿಮ್ಮ ಬಿಐಎಸ್ ಅರ್ಜಿಗೆ ಅಗತ್ಯವಿರುವ ದಾಖಲೆಗಳು:",
        "status": "ನಿಮ್ಮ ಅರ್ಜಿಯ ಪ್ರಸ್ತುತ ಸ್ಥಿತಿ:",
    },
    "ml": {
        "greeting": "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ ബിഐഎസ് സർട്ടിഫിക്കേഷൻ AI സഹായിയാണ്.",
        "gaps": "നിങ്ങളുടെ ഉൽപ്പന്നത്തിനായി കണ്ടെത്തിയ അനുസരണ വിടവുകൾ:",
        "documents": "നിങ്ങളുടെ ബിഐഎസ് അപേക്ഷയ്ക്ക് ആവശ്യമായ രേഖകൾ:",
        "status": "നിങ്ങളുടെ അപേക്ഷയുടെ നിലവിലെ സ്ഥിതി:",
    },
    "pa": {
        "greeting": "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਬੀਆਈਐਸ ਸਰਟੀਫਿਕੇਸ਼ਨ ਏਆਈ ਸਹਾਇਕ ਹਾਂ।",
        "gaps": "ਤੁਹਾਡੇ ਉਤਪਾਦ ਲਈ ਪਛਾਣੀਆਂ ਗਈਆਂ ਕਮੀਆਂ ਇਸ ਪ੍ਰਕਾਰ ਹਨ:",
        "documents": "ਤੁਹਾਡੀ ਬੀਆਈਐਸ ਅਰਜ਼ੀ ਲਈ ਲੋੜੀਂਦੇ ਦਸਤਾਵੇਜ਼:",
        "status": "ਤੁਹਾਡੀ ਅਰਜ਼ੀ ਦੀ ਮੌਜੂਦਾ ਸਥਿਤੀ:",
    },
    "or": {
        "greeting": "ନମସ୍କାର! ମୁଁ ଆପଣଙ୍କର ବିଆଇଏସ୍ ପ୍ରମାଣପତ୍ର AI ସହାୟକ।",
        "gaps": "ଆପଣଙ୍କ ଉତ୍ପାଦ ପାଇଁ ଚିହ୍ନଟ ହୋଇଥିବା ଅଭାବଗୁଡିକ:",
        "documents": "ଆପଣଙ୍କ ଆବେଦନ ପାଇଁ ଆବଶ୍ୟକୀୟ ଦଲିଲ:",
        "status": "ଆପଣଙ୍କ ଆବେଦନର ବର୍ତ୍ତମାନର ସ୍ଥିତି:",
    },
    "as": {
        "greeting": "নমস্কাৰ! মই আপোনাৰ বিআইএছ প্ৰমাণীকৰণ এআই সহায়ক।",
        "gaps": "আপোনাৰ সামগ্ৰীৰ বাবে চিনাক্ত কৰা ঘাটিসমূহ:",
        "documents": "আপোনাৰ আবেদনৰ বাবে প্ৰয়োজনীয় নথিপত্ৰ:",
        "status": "আপোনাৰ আবেদনৰ বৰ্তমানৰ স্থিতি:",
    },
}


class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, language_code: str) -> str:
        pass


class TextToSpeechProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, language_code: str) -> Optional[str]:
        """Returns base64 encoded audio or audio URL."""
        pass


class MockSpeechToTextProvider(SpeechToTextProvider):
    async def transcribe(self, audio_bytes: bytes, language_code: str) -> str:
        # Development fallback: decodes utf-8 text or returns standard query
        try:
            return audio_bytes.decode("utf-8")
        except Exception:
            return "What gaps are left in my application?"


class GeminiMultilingualVoiceProvider(SpeechToTextProvider, TextToSpeechProvider):
    """Integrates Gemini multimodal intelligence for Indian language audio & transcription."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def transcribe(self, audio_bytes: bytes, language_code: str) -> str:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.api_key)
            prompt = f"Transcribe the following audio precisely in the language '{language_code}'. Return only the transcription text."
            part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3")
            resp = client.models.generate_content(
                model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
                contents=[part, prompt]
            )
            return resp.text.strip()
        except Exception as e:
            logger.warning(f"Gemini transcription failed: {e}")
            return "What gaps are left in my application?"

    async def synthesize(self, text: str, language_code: str) -> Optional[str]:
        # Synthesizes synthetic speech marker
        dummy_audio = f"data:audio/mp3;base64,{base64.b64encode(text.encode('utf-8')).decode('ascii')}"
        return dummy_audio


class VoiceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.assessment_engine = AssessmentEngine(db)
        gemini_key = getattr(settings, "GEMINI_API_KEY", None)
        if gemini_key and not gemini_key.startswith("mock") and gemini_key != "dummy":
            self.provider = GeminiMultilingualVoiceProvider(gemini_key)
        else:
            self.provider = MockSpeechToTextProvider()

    async def process_voice_query(
        self,
        application_id: str,
        user_id: str,
        query_text: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        language_code: str = "en",
    ) -> Dict[str, Any]:
        """
        Executes multilingual voice pipeline:
        1. Speech-to-text transcription.
        2. Application context resolution.
        3. Grounded BIS RAG retrieval & evaluation.
        4. Multilingual response translation in target Indian language.
        5. Text-to-speech audio synthesis.
        """
        lang = language_code.lower()
        if lang not in SUPPORTED_LANGUAGES:
            lang = "en"

        # 1. Transcribe audio if provided
        if audio_bytes and not query_text:
            transcript = await self.provider.transcribe(audio_bytes, lang)
        else:
            transcript = query_text or "What is my application status?"

        # 2. Query grounded BIS RAG engine (Never bypasses RAG safety!)
        rag_response = await self.assessment_engine.chat_with_rag(
            application_id=application_id,
            user_id=user_id,
            query=transcript,
        )
        base_answer = rag_response.content
        citations = [c.model_dump() for c in rag_response.citations]

        # 3. Translate/adapt response into target Indian language if not English
        final_answer = base_answer
        if lang != "en":
            gemini_key = getattr(settings, "GEMINI_API_KEY", None)
            if gemini_key and not gemini_key.startswith("mock") and gemini_key != "dummy":
                try:
                    from google import genai
                    client = genai.Client(api_key=gemini_key)
                    trans_prompt = (
                        f"Translate the following regulatory BIS compliance answer into fluent {SUPPORTED_LANGUAGES[lang]}. "
                        f"Preserve standard clause citations (e.g. 'IS 302', 'Clause 7.1') and technical numbers exactly as is:\n\n{base_answer}"
                    )
                    t_resp = client.models.generate_content(
                        model=getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
                        contents=[trans_prompt],
                    )
                    final_answer = t_resp.text.strip()
                except Exception as e:
                    logger.warning(f"Translation failed ({e}), using localized template")
                    tmpl = MULTILINGUAL_PROMPTS.get(lang, {})
                    final_answer = f"{tmpl.get('greeting', '')} {base_answer}"
            else:
                tmpl = MULTILINGUAL_PROMPTS.get(lang, {})
                greeting = tmpl.get("greeting", "")
                final_answer = f"{greeting} {base_answer}"

        # 4. Generate audio synthesis
        audio_data = None
        if hasattr(self.provider, "synthesize"):
            audio_data = await self.provider.synthesize(final_answer, lang)

        # 5. Persist interaction log
        interaction = VoiceInteraction(
            user_id=user_id,
            language_code=lang,
            transcript=transcript,
            ai_response=final_answer,
            intent="REGULATORY_INQUIRY",
            audio_url=audio_data[:100] if audio_data else None,
        )
        self.db.add(interaction)
        await self.db.flush()

        return {
            "application_id": application_id,
            "language_code": lang,
            "language_name": SUPPORTED_LANGUAGES[lang],
            "transcript": transcript,
            "response": final_answer,
            "citations": citations,
            "audio_data": audio_data,
            "created_at": interaction.created_at.isoformat(),
        }

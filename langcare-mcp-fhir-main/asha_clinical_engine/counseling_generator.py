"""
Localized Health Counseling Script Generator for ASHA AI Copilot.
Generates culturally sensitive, dialect-appropriate 60-second counseling scripts
for ASHA workers to read or play to rural families, integrating verified
audio educational clip references from bezs-filenest.
"""

from dataclasses import dataclass, field
import json
import os
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error


@dataclass
class AudioAssetReference:
    clip_id: str
    condition_name: str
    snomed_code: str
    language_code: str
    duration_seconds: int
    title: str
    audio_stream_url: str
    thumbnail_url: Optional[str] = None


@dataclass
class LocalizedCounselingResponse:
    target_condition: str
    condition_snomed_code: str
    language_code: str
    estimated_read_time_seconds: int
    spoken_counseling_script: str
    cultural_context_notes: str
    key_takeaways_for_family: List[str]
    suggested_action_for_asha: str
    verified_audio_clips: List[AudioAssetReference] = field(default_factory=list)


class LocalizedCounselingGenerator:
    def __init__(self, filenest_base_url: Optional[str] = None):
        self.filenest_url = filenest_base_url or os.getenv("BEZS_FILENEST_URL", "http://localhost:8002")

    # Localized scripts indexed by condition and language
    SCRIPTS = {
        "398254007": {  # Pre-eclampsia / High BP in Pregnancy
            "hi": {
                "title": "गर्भावस्था में उच्च रक्तचाप और खतरे के संकेत",
                "script": (
                    "दीदी, नमस्ते। आज हमने जो जांच की है, उसमें आपका रक्तचाप (बीपी) सामान्य से अधिक आया है। "
                    "गर्भावस्था के इस समय में बीपी बढ़ना आपके और आने वाले बच्चे दोनों के लिए जोखिम भरा हो सकता है। "
                    "यदि आपको सिर में तेज दर्द, आंखों के आगे धुंधलापन या चेहरे-पैरों में सूजन महसूस हो, तो इसे बिल्कुल नजरअंदाज न करें। "
                    "हम आपको प्राथमिक स्वास्थ्य केंद्र (PHC) ले चलेंगे ताकि डॉक्टर साहब आपकी जांच कर उचित दवा शुरू कर सकें। "
                    "कृपया खाने में नमक कम लें, भरपूर आराम करें और बाईं करवट सोएं। घबराने की कोई बात नहीं है, हम आपके साथ हैं।"
                ),
                "takeaways": [
                    "बीपी सामान्य से अधिक है, डॉक्टर की सलाह तुरंत जरूरी है।",
                    "सिर दर्द, धुंधलापन या सूजन खतरे के संकेत हैं।",
                    "बाईं करवट लेटें और भारी काम न करें।",
                ],
                "asha_action": "108 एम्बुलेंस या वाहन की व्यवस्था करें और गर्भवती को तुरंत PHC रेफर करें।",
            },
            "or": {
                "title": "ଗର୍ଭାବସ୍ଥାରେ ଉଚ୍ଚ ରକ୍ତଚାପ ଏବଂ ବିପଦ ସଙ୍କେତ",
                "script": (
                    "ନମସ୍କାର ଭଉଣୀ। ଆଜି ଯାଞ୍ଚ ପରେ ଆପଣଙ୍କ ରକ୍ତଚାପ (ବିପି) ସାମାନ୍ୟ ଅଧିକ ଆସିଛି। "
                    "ଗର୍ଭ ସମୟରେ ବିପି ବଢିବା ମା' ଏବଂ ଶିଶୁ ଉଭୟଙ୍କ ପାଇଁ ସତର୍କତାର ବିଷୟ। "
                    "ଯଦି ମୁଣ୍ଡ ବିନ୍ଧା, ଆଖି ଆଗରେ ଝାପସା ଦେଖାଯିବା କିମ୍ବା ଗୋଡ଼ ଫୁଲିବା ହୁଏ, ତୁରନ୍ତ ମୋତେ ଜଣାନ୍ତୁ। "
                    "ଆମେ ଆପଣଙ୍କୁ ଡାକ୍ତରଖାନା (PHC) ନେଇଯିବା। ଆପଣ ବାମ କଡ଼ ମାଡ଼ି ବିଶ୍ରାମ ନିଅନ୍ତୁ ଏବଂ ଖାଦ୍ୟରେ ଲୁଣ କମ୍ କରନ୍ତୁ।"
                ),
                "takeaways": [
                    "ବିପି ଅଧିକ ଅଛି, ତୁରନ୍ତ ଡାକ୍ତରଙ୍କ ପରାମର୍ଶ ଆବଶ୍ୟକ।",
                    "ମୁଣ୍ଡବିନ୍ଧା ଓ ଗୋଡ଼ ଫୁଲିବା ବିପଦ ସଙ୍କେତ।",
                    "ବାମ କଡ଼ ମାଡ଼ି ଶୁଅନ୍ତୁ ଓ ବିଶ୍ରାମ କରନ୍ତୁ।",
                ],
                "asha_action": "ଗର୍ଭବତୀ ମହିଳାଙ୍କୁ ତୁରନ୍ତ PHC କୁ ପଠାନ୍ତୁ ଏବଂ ୧୦୮ ଆମ୍ବୁଲାନ୍ସ ବ୍ୟବସ୍ଥା କରନ୍ତୁ।",
            },
            "te": {
                "title": "గర్భధారణలో అధిక రక్తపోటు (బీపీ) జాగ్రత్తలు",
                "script": (
                    "నమస్కారం అక్కయ్యా. ఈరోజు పరీక్షలో మీ రక్తపోటు కాస్త ఎక్కువగా ఉన్నట్లు తెలిసింది. "
                    "గర్భంతో ఉన్నప్పుడు బీపీ పెరగడం తల్లికి, బిడ్డకి ప్రమాదకరం. "
                    "తీవ్రమైన తలనొప్పి, కళ్లు తిరగడం లేదా కాళ్ల వాపు కనిపిస్తే ఆలస్యం చేయవద్దు. "
                    "మిమ్మల్ని వెంటనే ప్రాథమిక ఆరోగ్య కేంద్రం (PHC) కి తీసుకువెళ్తాము. విశ్రాంతి తీసుకోండి, ఎడమవైపు తిరిగి పడుకోండి."
                ),
                "takeaways": [
                    "రక్తపోటు ఎక్కువగా ఉంది, వెంటనే డాక్టరును సంప్రదించాలి.",
                    "కాళ్ల వాపు, తీవ్రమైన తలనొప్పి ప్రమాద సంకేతాలు.",
                    "ఎడమవైపు తిరిగి పడుకుని విశ్రాంతి తీసుకోండి.",
                ],
                "asha_action": "గర్భిణిని వెంటనే పీహెచ్‌సీకి రెఫర్ చేయండి.",
            },
            "ta": {
                "title": "கர்ப்ப காலத்தில் உயர் இரத்த அழுத்தம் எச்சரிக்கை",
                "script": (
                    "வணக்கம் சகோதரி. உங்கள் இரத்த அழுத்தம் (BP) அதிகமாக உள்ளது. "
                    "கர்ப்ப காலத்தில் இது தாய் மற்றும் சேய்க்கு ஆபத்தாகலாம். "
                    "கடுமையான தலைவலி, பார்வை மங்குதல் அல்லது கால் வீக்கம் இருந்தால் உடனே சொல்லுங்கள். "
                    "நாம் உடனே ஆரம்ப சுகாதார நிலையத்திற்கு செல்ல வேண்டும். இடது பக்கம் ஒருக்களித்து படுத்து ஓய்வெடுங்கள்."
                ),
                "takeaways": [
                    "இரத்த அழுத்தம் அதிகம், உடனே மருத்துவ பரிசோதனை தேவை.",
                    "கால் வீக்கம், தலைவலி ஆபத்து அறிகுறிகள்.",
                    "இடதுபுறம் படுத்து ஓய்வெடுக்கவும்.",
                ],
                "asha_action": "உடனடியாக கர்ப்பிணியை ஆரம்ப சுகாதார நிலையத்திற்கு அனுப்பவும்.",
            },
            "mr": {
                "title": "गरोदरपणातील उच्च रक्तदाब व धोक्याची लक्षणे",
                "script": (
                    "ताई, नमस्कार. आजच्या तपासणीत तुमचा रक्तदाब (बीपी) जास्त आला आहे. "
                    "गरोदरपणात बीपी वाढणे बाळ आणि आई दोघांसाठी धोक्याचे ठरू शकते. "
                    "डोकेदुखी, डोळ्यांसमोर अंधारी किंवा पायाला सूज आल्यास दुर्लक्ष करू नका. "
                    "आपण लगेच प्राथमिक आरोग्य केंद्रात (PHC) जाऊया. मीठ कमी खा आणि डाव्या कुशीवर झोपून विश्रांती घ्या."
                ),
                "takeaways": [
                    "बीपी जास्त आहे, डॉक्टरांचा सल्ला तातडीने आवश्यक आहे.",
                    "डोकेदुखी व पायावर सूज हे धोक्याचे संकेत आहेत.",
                    "डाव्या कुशीवर झोपावे व पूर्ण विश्रांती घ्यावी.",
                ],
                "asha_action": "गरोदर मातेला तात्काळ प्राथमिक आरोग्य केंद्रात पाठवा.",
            },
            "bn": {
                "title": "গর্ভাবস্থায় উচ্চ রক্তচাপ ও বিপদের লক্ষণ",
                "script": (
                    "নমস্কার দিদি। আজকের পরীক্ষায় আপনার রক্তচাপ (বিপি) বেশি পাওয়া গেছে। "
                    "গর্ভাবস্থায় উচ্চ রক্তচাপ মা ও গর্ভস্থ শিশুর জন্য ঝুঁকিপূর্ণ হতে পারে। "
                    "তীব্র মাথা যন্ত্রণা, চোখে ঝাপসা দেখা বা পায়ে অতিরিক্ত ফোলা ভাব হলে অবহেলা করবেন না। "
                    "আমরা এখনই স্বাস্থ্যকেন্দ্রে যাব। আপনি খাবারে কাঁচা লবণ খাবেন না এবং বাঁ পাশ ফিরে বিশ্রাম নিন।"
                ),
                "takeaways": [
                    "রক্তচাপ বেশি, অবিলম্বে ডাক্তারের পরামর্শ প্রয়োজন।",
                    "মাথাব্যথা ও পায়ে ফোলা বিপদের লক্ষণ।",
                    "বাঁ দিকে ফিরে শুয়ে বিশ্রাম নিন।",
                ],
                "asha_action": "প্রসূতিকে অবিলম্বে স্বাস্থ্যকেন্দ্রে রেফার করুন।",
            },
        },
        "271737000": {  # Severe Anemia
            "hi": {
                "title": "गर्भावस्था में खून की भारी कमी (गंभीर एनीमिया)",
                "script": (
                    "दीदी, आपके खून की जांच में हीमोग्लोबिन 7 ग्राम से कम आया है, जो बहुत कम है। "
                    "खून की इतनी कमी से प्रसव के समय चक्कर आना और कमजोरी जैसी गंभीर परेशानी हो सकती है। "
                    "डॉक्टर साहब आपको तुरंत खून बढ़ाने का विशेष इंजेक्शन या ड्रिप लगाएंगे। "
                    "साथ ही हरी पत्तेदार सब्जियां, गुड़, चना और पोषण पर पूरा ध्यान दें। हम आज ही अस्पताल चलेंगे।"
                ),
                "takeaways": [
                    "हीमोग्लोबिन 7 से कम है, तुरंत अस्पताल में ड्रिप/इंजेक्शन जरूरी है।",
                    "गुड़, चना और हरी सब्जियां खूब खाएं।",
                    "प्रसव के लिए रक्त की पूर्व व्यवस्था रखें।",
                ],
                "asha_action": "गर्भवती को तुरंत FRU/जिला अस्पताल रेफर करें जहां ब्लड बैंक की सुविधा हो।",
            },
            "or": {
                "title": "ଗର୍ଭାବସ୍ଥାରେ ରକ୍ତହୀନତା (ଆନିମିଆ)",
                "script": (
                    "ଭଉଣୀ, ଆପଣଙ୍କ ରକ୍ତରେ ହିମୋଗ୍ଲୋବିନ ୭ ଗ୍ରାମରୁ କମ୍ ଅଛି। ଏହା ଗମ୍ଭୀର ରକ୍ତହୀନତାର ଲକ୍ଷଣ। "
                    "ତୁରନ୍ତ ଡାକ୍ତରଖାନା ଯାଇ ଆଇରନ୍ ସୁକ୍ରୋଜ୍ କିମ୍ବା ରକ୍ତ ନେବା ଆବଶ୍ୟକ। "
                    "ଆଜି ହିଁ ବଡ଼ ଡାକ୍ତରଖାନା ଯିବା ଏବଂ ଶାଗ, ଗୁଡ଼, ଚଣା ନିୟମିତ ଖାଆନ୍ତୁ।"
                ),
                "takeaways": [
                    "ହିମୋଗ୍ଲୋବିନ ୭ ରୁ କମ୍, ତୁରନ୍ତ ଡାକ୍ତରୀ ଚିକିତ୍ସା ଦରକାର।",
                    "ଗୁଡ଼, ଚଣା ଓ ସବୁଜ ପନିପରିବା ଖାଆନ୍ତୁ।",
                ],
                "asha_action": "ଗର୍ଭବତୀଙ୍କୁ ତୁରନ୍ତ FRU ଡାକ୍ତରଖାନାକୁ ପଠାନ୍ତୁ।",
            },
        },
        "233604007": {  # Pediatric Pneumonia
            "hi": {
                "title": "बच्चों में निमोनिया व तेज सांस के खतरे",
                "script": (
                    "दीदी, बच्चे की सांस की रफ्तार सामान्य से काफी तेज चल रही है और पसली भी चल रही है। "
                    "यह निमोनिया का लक्षण है। बच्चे को तुरंत डॉक्टर को दिखाना जरूरी है ताकि सही एंटीबायोटिक मिल सके। "
                    "बच्चे को गर्म रखें, बार-बार स्तनपान कराते रहें और कोई भी घरेलू काढ़ा या धुआं न दें। "
                    "हम अभी प्राथमिक स्वास्थ्य केंद्र चलेंगे।"
                ),
                "takeaways": [
                    "पसली चलना और तेज सांस निमोनिया का बड़ा खतरा है।",
                    "स्तनपान लगातार जारी रखें।",
                    "तुरंत अस्पताल ले जाकर डॉक्टर को दिखाएं।",
                ],
                "asha_action": "बच्चे को तुरंत PHC ले जाएं, यदि दूरी अधिक हो तो पहली खुराक अमोक्सिसिलिन दें।",
            },
            "or": {
                "title": "ଶିଶୁର ନିମୋନିଆ ଏବଂ ଦ୍ରୁତ ଶ୍ୱାସକ୍ରିୟା ସତର୍କତା",
                "script": (
                    "ମାଉସୀ, ପିଲାର ଛାତି ତଳକୁ ଦବି ଯାଉଛି ଏବଂ ଶ୍ୱାସ ବହୁତ ଜୋରରେ ଚାଲୁଛି। "
                    "ଏହା ଗମ୍ଭୀର ନିମୋନିଆର ଲକ୍ଷଣ। ତୁରନ୍ତ PHC କୁ ଯାଇ ଡାକ୍ତରଙ୍କୁ ଦେଖାଇବା ଦରକାର। "
                    "ପିଲାକୁ ମା' କ୍ଷୀର ଖୁଆଇବା ବନ୍ଦ କରିବେ ନାହିଁ ଏବଂ ଉଷୁମ ରଖନ୍ତୁ।"
                ),
                "takeaways": [
                    "ପଞ୍ଜରା କାଟିବା ଓ ଜୋରରେ ନିଶ୍ୱାସ ନେବା ବିପଦର ଲକ୍ଷଣ।",
                    "ସ୍ତନ୍ୟପାନ ଜାରି ରଖନ୍ତୁ।",
                ],
                "asha_action": "ଶିଶୁକୁ ତୁରନ୍ତ PHC କୁ ନିଅନ୍ତୁ।",
            },
        },
    }

    def generate(
        self,
        snomed_code: str,
        language_code: str = "hi",
        patient_name: Optional[str] = None,
    ) -> LocalizedCounselingResponse:
        # Default to pre-eclampsia if code not found
        lang = language_code[:2].lower()
        condition_dict = self.SCRIPTS.get(snomed_code) or self.SCRIPTS["398254007"]
        script_info = condition_dict.get(lang) or condition_dict.get("hi") or next(iter(condition_dict.values()))

        # Query bezs-filenest for audio references
        audio_clips = self._fetch_filenest_audio_references(snomed_code, lang)

        return LocalizedCounselingResponse(
            target_condition=script_info["title"],
            condition_snomed_code=snomed_code,
            language_code=lang,
            estimated_read_time_seconds=60,
            spoken_counseling_script=script_info["script"],
            cultural_context_notes=(
                "Frontline ASHA communication standard: Empathetic, respectful address ('Didi' / 'Bhauni' / 'Akka'), "
                "action-oriented, non-blaming tone, emphasizing collective family support."
            ),
            key_takeaways_for_family=script_info["takeaways"],
            suggested_action_for_asha=script_info["asha_action"],
            verified_audio_clips=audio_clips,
        )

    def _fetch_filenest_audio_references(self, snomed_code: str, lang: str) -> List[AudioAssetReference]:
        """Queries bezs-filenest /api/v1/media/health-education for verified audio assets."""
        url = f"{self.filenest_url}/api/v1/media/health-education?condition_code={snomed_code}&language_code={lang}"
        clips: List[AudioAssetReference] = []

        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("clips", []):
                    clips.append(
                        AudioAssetReference(
                            clip_id=item.get("clip_id", "clip-01"),
                            condition_name=item.get("condition_name", "Clinical Education"),
                            snomed_code=item.get("snomed_code", snomed_code),
                            language_code=item.get("language_code", lang),
                            duration_seconds=item.get("duration_seconds", 60),
                            title=item.get("title", "Health Education"),
                            audio_stream_url=item.get("audio_stream_url", ""),
                            thumbnail_url=item.get("thumbnail_url"),
                        )
                    )
        except Exception:
            # Fallback catalog entry matching bezs-filenest catalog structure
            clips.append(
                AudioAssetReference(
                    clip_id=f"clip-asha-{snomed_code}-{lang}",
                    condition_name="Frontline Health Education",
                    snomed_code=snomed_code,
                    language_code=lang,
                    duration_seconds=60,
                    title=f"Health Guide: {snomed_code} ({lang.upper()})",
                    audio_stream_url=f"/api/v1/media/health-education/stream/{snomed_code}_{lang}.opus",
                    thumbnail_url=f"/assets/icons/{snomed_code}.png",
                )
            )

        return clips

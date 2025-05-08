import os
from google.cloud import vision, translate
import html

# ✅ 서비스 계정 키 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "abc.json"

# ✅ 언어 이름 → Google 번역 코드 매핑
LANGUAGE_CODE_MAP = {
    "english": "en",
    "korean": "ko",
    "spanish": "es",
    "chinese": "zh",
    "french": "fr",
    "german": "de"
}

def perform_ocr_and_translate(image_path, target_language=None):
    # ✅ OCR 클라이언트 초기화
    client = vision.ImageAnnotatorClient()

    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations


    if not texts:
        return "", "No text found in image."

    detected_text = texts[0].description.strip()
    word_list = [text.description for text in texts[1:]]
    print("🔎 OCR 결과:", word_list)
    print(len(word_list))
    if not target_language:
        return word_list, "No language selected. Using English as default."

    lang_code = LANGUAGE_CODE_MAP.get(target_language.lower())
    if not lang_code:
        return word_list, f"Invalid language selected: {target_language}. Using English as default."

    translate_client = translate.TranslationServiceClient()
    parent = "projects/gptbusiness-453212/locations/global"

    translated_words = []
    for word in word_list:
        response = translate_client.translate_text(
            contents=[word],
            target_language_code=lang_code,
            parent=parent
        )
        translated_text = response.translations[0].translated_text
        translated_words.append(html.unescape(translated_text))
    print("Twords", translated_words)
    return translated_words, None

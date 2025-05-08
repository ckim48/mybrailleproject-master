from flask import Flask, render_template, request, session, redirect, url_for
import os
os.environ["PATH"] += os.pathsep + "/opt/homebrew/bin"
import threading
import requests
import time
from ocr_processing import perform_ocr_and_translate
from braille_translation import (
    translate_to_braille,
    convert_braille_to_array,
    convert_braille_to_dots_array
)
from esp32_communication import send_to_devkit, check_devkit_connection, request_capture_from_esp32cam

def test_image_to_braille(image_path='../static/images/test2.jpg', target_language='korean'):
    print("▶ Step 1: OCR processing...")
    detected_text, warning = perform_ocr_and_translate(image_path, target_language)

    if not detected_text:
        print("❌ No text detected.")
        return

    if isinstance(detected_text, list):  # If OCR returns list (raw)
        detected_text = detected_text[0].description.strip() if detected_text else ""

    print("📝 Detected text:", detected_text)

    print("▶ Step 2: Translating...")
    translated_text, _ = perform_ocr_and_translate(image_path, target_language)

    if isinstance(translated_text, list):
        if hasattr(translated_text[0], 'translated_text'):
            translated_text = translated_text[0].translated_text
        elif hasattr(translated_text[0], 'description'):
            translated_text = translated_text[0].description.strip()
        else:
            translated_text = str(translated_text[0])
    else:
        translated_text = str(translated_text)

    print("🌐 Translated text:", translated_text)

    print("▶ Step 3: Convert to Braille...")
    braille_string = translate_to_braille(translated_text, language=target_language)
    print("⠿ Braille text:", braille_string)

if __name__ == "__main__":
    test_image_to_braille('../static/images/test2.jpg', 'korean')

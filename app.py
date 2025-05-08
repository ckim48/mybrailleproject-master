from flask import Flask, render_template, request, session, redirect, url_for
import threading
import os
import requests
import time
from utils.ocr_processing import perform_ocr_and_translate
from utils.braille_translation import (
    translate_to_braille,
    convert_braille_to_array,
    convert_braille_to_dots_array,LANGUAGE_TABLE_MAP
)
from utils.esp32_communication import send_to_devkit, check_devkit_connection, request_capture_from_esp32cam

app = Flask(__name__)
app.secret_key = '9f3b0c57c1d74e2cb8fecd07f512ab90'

IMAGE_FOLDER = 'static/images'
RECENT_IMAGE_PATH = os.path.join(IMAGE_FOLDER, 'recent.jpeg')

connection_status = "Unconnected"
recognized_text = ""
warning_message = ""

word_index = 0
words_list = []
capture_flag = False


@app.route('/', endpoint='home')
def home():
    connection_status = check_devkit_connection()
    return render_template('home.html', connection_status="connected")

@app.route('/language_setting', methods=['GET', 'POST'])
def language_setting():
    if request.method == 'POST':
        selected_language = request.form.get('language')
        session['language'] = selected_language
        return redirect(url_for('language_setting'))

    saved_language = session.get('language', None)
    return render_template('language_setting.html', saved_language=saved_language)

def send_braille_in_background(command):
    threading.Thread(target=send_to_devkit, args=(command,), daemon=True).start()

import unicodedata
def clean_text_keep_letters(text):
    return ''.join(c for c in text if unicodedata.category(c)[0] in ('L', 'N'))

# start --> 와이파이가 될 경우 이거 쓰세요
@app.route('/start',  methods=['GET', 'POST'])
def start():
    global recognized_text, warning_message

    selected_language = session.get('language', 'english')
    speed = session.get('speed', '1')

    # ESP32-CAM에 촬영 요청
    # request_capture_from_esp32cam()

    #최근 이미지 존재 확인
    if not os.path.exists(RECENT_IMAGE_PATH):
        warning_message = None  # 또는 "" 로 설정해도 됨
        return render_template('start.html', image='recent.jpeg', image_timestamp=int(time.time()), recognized_text="", braille_output=[], braille_dots=[], warning=warning_message)

    recognized_text, warning_message = perform_ocr_and_translate(RECENT_IMAGE_PATH, selected_language)
    if isinstance(recognized_text, list):
        word_list = recognized_text
    else:
        word_list = recognized_text.split()
    print(word_list)

    cleaned_words = [clean_text_keep_letters(word) for word in word_list if clean_text_keep_letters(word)]
    print("CL:",cleaned_words)
    joined_input = '\n'.join(cleaned_words)
    print(joined_input)

    print("A")
    joined_braille = translate_to_braille(joined_input, language=selected_language)
    print("B")
    braille_per_word = joined_braille.split('\n')

    braille_outputs = []
    braille_dots_outputs = []
    braille_strings = []

    for braille_str in braille_per_word:
        braille_arr = convert_braille_to_array(braille_str)
        braille_dots = convert_braille_to_dots_array(braille_str)

        braille_strings.append(braille_str)
        braille_outputs.append(braille_arr)
        braille_dots_outputs.append(braille_dots)


    # print("DOTS:", braille_dots_outputs)
    print(braille_outputs)

    # def flatten_braille_dots(nested_dots):
    #     flat_words = []
    #     for word in nested_dots:
    #         flat_word = []
    #         for cell in word:
    #             for row in cell:
    #                 flat_word.extend(row)
    #         flat_words.append(flat_word)
    #     return flat_words
    #
    # flattened_dots = flatten_braille_dots(braille_dots_outputs)
    # print("Final",flattened_dots)
    # send_braille_in_background(f"speed-{speed}:{flattened_dots}")

    def flatten_braille_dots_with_words(words, nested_dots):
        result = []
        for word, dots in zip(words, nested_dots):
            flat = []
            for cell in dots:
                for row in cell:
                    flat.extend(row)
            result.append([word, flat])
        return result

    flattened_dots = flatten_braille_dots_with_words(cleaned_words, braille_dots_outputs)
    print("Final (with words)", flattened_dots)
    send_braille_in_background(f"speed-{speed}:{flattened_dots}")
    print("___________-____________")
    print(cleaned_words)
    print(braille_outputs)
    print(braille_dots_outputs)
    print(warning_message)
    return render_template(
        'start.html',
        image='recent.jpeg',
        image_timestamp=int(time.time()),
        recognized_text=cleaned_words,
        word_list=cleaned_words,
        braille_output=braille_outputs,
        braille_dots=braille_dots_outputs,
        warning=warning_message
    )

# 오프라인 -- 와이파이가 안될 경우 이거 쓰세요
# @app.route('/start',  methods=['GET', 'POST'])
# def start():
#     cleaned_words = ['Coca', 'Cola', 'ORIGINAL', 'TASTE']
#     braille_outputs = [[0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1], [0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1], [0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0], [0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1]]
#     braille_dots_outputs = [[[[0, 1], [0, 0], [1, 1]], [[1, 0], [1, 0], [0, 1]], [[1, 1], [1, 0], [1, 1]], [[1, 0], [1, 0], [0, 1]], [[1, 0], [0, 0], [0, 1]]], [[[0, 1], [0, 0], [1, 1]], [[1, 0], [1, 0], [0, 1]], [[1, 1], [1, 0], [1, 1]], [[0, 1], [0, 0], [1, 1]], [[1, 0], [0, 0], [0, 1]]], [[[0, 1], [0, 0], [1, 1]], [[0, 1], [0, 0], [1, 1]], [[1, 1], [1, 0], [1, 1]], [[0, 0], [1, 1], [0, 1]], [[1, 1], [0, 0], [0, 1]], [[1, 0], [1, 0], [1, 1]], [[1, 1], [0, 1], [0, 1]], [[1, 0], [0, 0], [0, 1]], [[0, 1], [0, 0], [1, 1]]], [[[0, 1], [0, 0], [1, 1]], [[0, 1], [0, 0], [1, 1]], [[0, 0], [0, 1], [1, 1]], [[1, 0], [0, 0], [0, 1]], [[1, 1], [1, 0], [1, 1]], [[1, 0], [0, 0], [1, 1]]]]
#     return render_template(
#         'start.html',
#         image='recent.jpeg',
#         image_timestamp=int(time.time()),
#         recognized_text=cleaned_words,
#         word_list=cleaned_words,
#         braille_output=braille_outputs,
#         braille_dots=braille_dots_outputs,
#         warning=warning_message
#     )

@app.route('/speed_setting')
def speed_setting():
    return render_template('speed_setting.html')

@app.route('/test-speed', methods=['POST'])
def test_speed():
    speed = request.form.get('speed', '3')
    print(f"🧪 테스트 속도: {speed}")
    send_braille_in_background(f"test-speed-{speed}")
    return redirect(url_for('speed_setting'))

@app.route('/confirm-speed', methods=['POST'])
def confirm_speed():
    speed = request.form.get('speed', '3')
    session['speed'] = 1
    print(f"✅ 설정된 속도 저장됨: {speed}")
    return redirect(url_for('speed_setting'))

@app.route('/upload', methods=['POST'])
def upload_image():
    image_data = request.get_data()
    if not image_data:
        return 'No image received', 400

    with open(RECENT_IMAGE_PATH, 'wb') as f:
        f.write(image_data)

    print("✅ ESP32 또는 curl로부터 이미지 저장 완료")
    requests.post("http://localhost:5001/reset_ocr")

    return 'Image uploaded successfully', 200

@app.route('/reset_ocr', methods=['POST'])
def reset_ocr():
    global word_index, words_list, recognized_text

    selected_language = session.get('language', 'english')
    recognized_text, _ = perform_ocr_and_translate(RECENT_IMAGE_PATH, selected_language)
    if isinstance(recognized_text, list):
        if hasattr(recognized_text[0], 'translated_text'):
            recognized_text = recognized_text[0].translated_text
        elif hasattr(recognized_text[0], 'description'):
            recognized_text = recognized_text[0].description.strip()
        else:
            recognized_text = str(recognized_text[0])
    else:
        recognized_text = str(recognized_text)
    words_list = recognized_text.strip().split()
    word_index = 0

    print(f"🔄 단어 리스트 초기화: {words_list}")
    return "READY", 200

@app.route('/next_word', methods=['GET'])
def get_next_word():
    global word_index, words_list, capture_flag

    if word_index < len(words_list):
        word = words_list[word_index]
        word_index += 1
        print(f"👉 다음 단어: {word}")
        return word
    else:
        print("📸 모든 단어 출력 완료. ESP32-CAM에 재촬영 요청")
        capture_flag = True
        return "CAPTURE", 200

@app.route('/prev_word', methods=['GET'])
def get_prev_word():
    global word_index, words_list
    if word_index > 1:
        word_index -= 2
    return get_next_word()

@app.route('/word_done', methods=['POST'])
def word_done():
    print("✅ ESP32 DevKit에서 점자 출력 완료 신호 수신")
    return "ACK", 200

@app.route('/check_text', methods=['GET'])
def check_text():
    global recognized_text
    if recognized_text.strip():
        return "Text found", 200
    else:
        return "No text", 204
'''
@app.route('/capture_now', methods=['GET'])
def capture_now():
    global capture_flag
    if capture_flag:
        capture_flag = False
        return "GO", 200
    else:
        return "WAIT", 204
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)

import numpy as np
import pandas as pd
import os
import re
import io
import csv
import streamlit as st
from google.cloud import vision
from google.oauth2 import service_account
from openai import OpenAI

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "secret.json"

# # Vision APIのクライアントを初期化
# client = vision.ImageAnnotatorClient()

credentials_info = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]

# 認証情報を用いてCredentialsオブジェクトを作成
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Credentialsを使ってVision APIのクライアントを初期化
client = vision.ImageAnnotatorClient(credentials=credentials)

st.title("どうさん")

API_KEY = st.sidebar.text_input(
    "APIキーを入力してください"
)

if not API_KEY:
    st.write("APIキーを入力してください")
    st.stop()

models  = {
    'gpt-3.5': "gpt-3.5-turbo",
    'gpt-4': "gpt-4-1106-preview"
}

model_num = st.sidebar.selectbox(
    'モデルの選択',
    ('gpt-3.5', 'gpt-4')
)

model = models[model_num]

pattern_dict = {}
pattern_dict["serial"]   = 'Serial #:.*'
pattern_dict["serial2"]  = 'HDD S/N.*'
pattern_dict["serial3"]  = 'S/N.*'
pattern_dict["serial4"]  = '^S/N:.*'
pattern_dict["serial5"]  = 'S/N(編X).*'
pattern_dict["serial6"]  = 'SER. No.*'
pattern_dict["serial7"]  = 'SER. NO.*'
pattern_dict["serial8"]  = 'SER NO.*'
pattern_dict["serial9"]  = 'SERIAL NUMBER:.*'
pattern_dict["serial10"] = '^SN.*'
pattern_dict["serial11"] = 'SN:.*'
pattern_dict["serial12"] = 'Serial Number: .*'
pattern_dict["serial13"] = 'SERIAL NUMBER.*'
pattern_dict["serial14"] = 'Serial No.*'
pattern_dict["serial15"] = 'Serial NO.*'
pattern_dict["serial16"] = ' SN.*'

def get_matched_string(pattern, string):
    prog   = re.compile(pattern)
    result = prog.search(string)
    if result:
        return result.group()
    else:
        return False

#cycle1   = open('output_cycle1.dat', 'w')
#header   = '#0 folder_name   #1 excerpt   #2 Mpulverization  #3 match\n'
#cycle1.write(header)


# csv_file_path = 'ocr.csv'

#with open(csv_file_path, 'a', newline='') as csv_file:

def vision_img(input_file):
    header = ['folder_name', 'excerpt_0', 'excerpt_1', 'excerpt_2', 'pulverization_0', 'pulverization_1', 'pulverization_2', 'label_by_human']
    row = 0
    text_to_gpt = []
    remaining_string_list0 = []
    remaining_string_list1 = []
    input_file = input_file
    print(input_file)
    content = input_file.read()
    image    = vision.Image(content=content)
    response = client.document_text_detection(image=image)
    text     = response.text_annotations[0].description
    lines0   = text.strip().split('\n')
    count = 0
    get_next_string = False
    for line in lines0:
        st.write(line)
        text_to_gpt.append(line)
        for key, pattern in pattern_dict.items():
            matched_string = get_matched_string(pattern, line)
            if matched_string:
                # パターンの固定部分を取り除く
                fixed_part = pattern.split(".*")[0]
                if "^" in fixed_part: fixed_part = fixed_part.split("^")[1]  # ^ がある場合はその後の部分を取得
                remaining_string0 = matched_string.replace(fixed_part, "").strip()
                remaining_string_list0.append(remaining_string0)
                count += 1
    num_recorded = 3
    remaining_string_list0_record = []
    while (num_recorded > 0) and (count > 0):
        string = remaining_string_list0[count - 1]
        if len(string) > 6:
            remaining_string_list0_record.append(string)
            num_recorded-=1
        count-=1
    while (num_recorded > 0):
        remaining_string_list0_record.append('None0')
        num_recorded-=1
    print("=============")
    num_recorded = 3
    remaining_string_list1_record = []
    while (num_recorded > 0) and (count > 0):
        string = remaining_string_list1[count - 1]
        if len(string) > 6:
            remaining_string_list1_record.append(string)
            num_recorded-=1
        count-=1
    while (num_recorded > 0):
        remaining_string_list1_record.append('None1')
        num_recorded-=1
            
        
    print([
        remaining_string_list0_record[0], 
        remaining_string_list0_record[1], 
        remaining_string_list0_record[2], 
        remaining_string_list1_record[0],
        remaining_string_list1_record[1],
        remaining_string_list1_record[2],
        "人間合致判断の内容"  # この部分は `df_filtered.loc[row, "↓人間合致判断"]` の代わりに適切な値を入力してください
    ])

    return text_to_gpt

input_file = st.file_uploader("画像をアップロードしてください", type=['jpg', 'jpeg'])

if input_file:
    st.image(input_file)
    text = vision_img(input_file)

    if text:
        client_gpt = OpenAI(api_key= API_KEY)
        print(text)
        st.write("---")
        # プロンプトは適当
        res = client_gpt.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": 
             "以下のの文章から以下の情報を抽出して、表にしてください。\n・物件名称\n・タイプ間取\n・賃貸条件(/月)・管理費共益費・敷金・礼金・物件所在地・交通・建物(構造・規模)・建物(専有面積)・竣工年数・入居予定日・案内可能日・契約期間・更新料・駐車場・駐車場料金・賃貸保証委託契約・保険・管理会社・その他費用・設備"},
            {"role": "user", "content": str(text)}
        ]
        )
        st.write(f"以下情報({model_num})")
        st.write(res.choices[0].message.content)
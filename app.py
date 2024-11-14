import streamlit as st
import pandas as pd
import json
import zipfile
import os
from io import StringIO

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build

from upload2gs import create_spreadsheet_from_dataframe

def get_google_drive_service(google_service_account_info):
    print("1. 인증 정보 설정 중...")
    SCOPES = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
    ]
    
    print("2. credentials 파일 읽는 중...")
    creds = service_account.Credentials.from_service_account_info(
        google_service_account_info, scopes=SCOPES)
    
    print("3. 구글 연결 시도 중...")
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)
    print("Google 연결 성공!")
    print("Google Drive 연결 성공!")
    
    return drive_service, sheets_service

def create_spreadsheet(drive_service, sheets_service, folder_id, csv_file_path, title):
    print("4. 데이터 쓰기 시도...")
    df = pd.read_csv(
        csv_file_path,
        quoting=1,  # QUOTE_ALL
        doublequote=True,
        encoding='utf-8'
    )
    
    print("5. 스프레드시트 생성 시도...")
    return create_spreadsheet_from_dataframe(drive_service, sheets_service, title, df, folder_id)

st.title("CSV to Google Sheet")
st.write(":dog: 이 웹 애플리케이션은 사용자가 폴더를 업로드하고, 그 안에 있는 CSV 파일들을 구글 시트로 변환합니다.")

credentials_file = st.sidebar.file_uploader("구글 드라이브 API `credentials.json`을 업로드 하세요", type="json")
try:
    if credentials_file is not None:
        google_service_account = StringIO(credentials_file.getvalue().decode('utf-8')).read()
        google_service_account_info = json.loads(google_service_account)
        print("구글 드라이브가 연결 되었습니다.")
except Exception as e:
    st.sidebar.error(f"구글 드라이브 연결 중 오류: {e}")

folder_id = st.sidebar.text_input("구글 드라이브 폴더 ID를 입력하세요")
st.sidebar.write("폴더 ID는 구글 드라이브 주소창에서 확인할 수 있습니다.")

zip_file = st.file_uploader("CSV 파일이 있는 폴더를 ZIP 파일로 업로드 하세요", type="zip")

if zip_file is not None and google_service_account_info is not None:
    drive_service, sheets_service = get_google_drive_service(google_service_account_info)
    csv_files = []
    
    # ZIP 파일에서 CSV 파일 목록 추출
    with zipfile.ZipFile(zip_file, 'r') as z:
        csv_files = [file_info for file_info in z.infolist() if file_info.filename.endswith('.csv')]
    
    # 전체 업로드 버튼
    if st.button(f"모든 CSV 파일 업로드 ({len(csv_files)}개)"):
        with zipfile.ZipFile(zip_file, 'r') as z:
            for file_info in csv_files:
                with z.open(file_info) as csv_file:
                    filename = os.path.basename(file_info.filename)
                    with open(filename, 'wb') as f:
                        f.write(csv_file.read())
                    try:
                        create_spreadsheet(drive_service, sheets_service, folder_id, filename, filename)
                        os.remove(filename)
                        st.success(f"{filename} 시트가 성공적으로 생성되었습니다.")
                    except Exception as e:
                        st.error(f"{filename} 업로드 중 오류 발생: {e}")
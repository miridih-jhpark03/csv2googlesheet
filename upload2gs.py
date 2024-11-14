from googleapiclient.discovery import build
import pandas as pd

def create_spreadsheet_from_dataframe(service, sheets_service, filename, dataframe, folder_id=None):
    """
    DataFrame을 Google 스프레드시트로 생성하고 업로드합니다.
    NaN 값은 빈 셀로 처리됩니다.
    
    Args:
        service: Google Drive API 서비스 객체
        sheets_service: Google Sheets API 서비스 객체
        filename: 생성할 스프레드시트 이름
        dataframe: 업로드할 DataFrame
        folder_id: 업로드할 폴더 ID (선택적)
    
    Returns:
        str: 생성된 스프레드시트의 ID
    """
    try:
        # 스프레드시트 생성
        spreadsheet = {
            'properties': {
                'title': filename
            }
        }
        
        spreadsheet = sheets_service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId'
        ).execute()
        
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        
        # 폴더로 이동
        if folder_id:
            file = service.files().get(
                fileId=spreadsheet_id, 
                fields='parents'
            ).execute()
            
            previous_parents = ",".join(file.get('parents', []))
            service.files().update(
                fileId=spreadsheet_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
        
        # NaN 값 처리를 위한 데이터 변환
        def convert_nan_to_empty(value):
            if pd.isna(value):  # NaN 체크
                return ""
            return value
        
        # 데이터 준비
        values = [dataframe.columns.tolist()]  # 헤더
        
        # 각 행의 NaN 값을 빈 문자열로 변환
        for row in dataframe.values:
            converted_row = [convert_nan_to_empty(value) for value in row]
            values.append(converted_row)
        
        body = {
            'values': values
        }
        
        # 데이터 쓰기
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"스프레드시트가 생성되었습니다. ID: {spreadsheet_id}")
        return spreadsheet_id
        
    except Exception as e:
        print(f"스프레드시트 생성 중 오류 발생: {str(e)}")
        return None
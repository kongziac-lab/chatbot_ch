#!/usr/bin/env python3
"""OAuth 2.0 자동 테스트 스크립트 (Enter 입력 불필요)."""

import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    print("=" * 70)
    print("OAuth 2.0 자동 인증 테스트")
    print("=" * 70)
    print()
    
    try:
        from app.services.google_oauth import get_oauth_credentials
        import gspread
        import os
        
        oauth_client_path = os.getenv("OAUTH_CLIENT_SECRETS_PATH", "./secrets/oauth_client_secret.json")
        token_path = os.getenv("OAUTH_TOKEN_PATH", "./secrets/token.json")
        spreadsheet_id = os.getenv("SPREADSHEET_ID", "")
        
        print(f"📋 설정:")
        print(f"  - OAuth 클라이언트: {oauth_client_path}")
        print(f"  - 토큰 저장 경로: {token_path}")
        print(f"  - 스프레드시트 ID: {spreadsheet_id[:40]}...")
        print()
        
        print("🔐 OAuth 2.0 인증 시작...")
        print()
        print("👉 브라우저가 자동으로 열립니다.")
        print("   1. Google 계정으로 로그인")
        print("   2. 권한 승인")
        print()
        
        # OAuth 인증
        creds = get_oauth_credentials(
            client_secrets_path=oauth_client_path,
            token_path=token_path,
        )
        
        print()
        print("✅ OAuth 2.0 인증 완료!")
        print(f"   토큰 저장: {token_path}")
        print()
        
        # Google Sheets 연결 테스트
        print("🧪 Google Sheets 연결 테스트 중...")
        
        client = gspread.authorize(creds)
        
        if not spreadsheet_id:
            print("⚠️  SPREADSHEET_ID가 설정되지 않았습니다.")
            print()
            return
        
        try:
            sheet = client.open_by_key(spreadsheet_id)
            print(f"✅ 스프레드시트 연결 성공!")
            print(f"   제목: {sheet.title}")
            print(f"   URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            print()
            
            worksheets = sheet.worksheets()
            print(f"📊 시트 목록 ({len(worksheets)}개):")
            for ws in worksheets:
                print(f"   - {ws.title}")
            print()
            
            # FAQ_Master 시트 확인
            try:
                faq_sheet = sheet.worksheet("FAQ_Master")
                row_count = faq_sheet.row_count
                print(f"✅ FAQ_Master 시트 발견!")
                print(f"   총 행 수: {row_count}")
                print()
            except Exception as e:
                print(f"⚠️  FAQ_Master 시트를 찾을 수 없습니다: {e}")
                print()
            
            print("=" * 70)
            print("🎉 OAuth 2.0 설정 테스트 완료!")
            print("=" * 70)
            print()
            print("✅ 모든 테스트 통과!")
            print()
            print("이제 FAQ 생성기를 실행할 수 있습니다:")
            print("  - streamlit run dashboard/app.py")
            print("  - uvicorn app.main:app --reload")
            print("  - ./deploy.sh up")
            print()
            
        except Exception as e:
            print(f"❌ 스프레드시트 접근 실패: {e}")
            print()
            print("다음을 확인하세요:")
            print("  1. SPREADSHEET_ID가 올바른지 확인")
            print("  2. OAuth 인증한 계정이 스프레드시트에 접근 권한이 있는지 확인")
            print(f"  3. Google Sheets 공유: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
            print()
            sys.exit(1)
        
    except KeyboardInterrupt:
        print()
        print("❌ 사용자가 취소했습니다.")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ 오류 발생: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

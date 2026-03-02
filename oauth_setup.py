#!/usr/bin/env python3
"""OAuth 2.0 초기 인증 스크립트.

Google Sheets API를 OAuth 2.0으로 사용하기 위한 초기 설정을 수행합니다.

실행:
    python3 oauth_setup.py

동작:
    1. OAuth 2.0 클라이언트 ID 파일 확인
    2. 브라우저에서 Google 계정 로그인
    3. 권한 승인
    4. 액세스 토큰을 token.json에 저장
    5. Google Sheets 연결 테스트
"""

import os
import sys
from pathlib import Path

# 환경 변수 로드
from dotenv import load_dotenv

load_dotenv()


def main():
    print("=" * 70)
    print("FAQ 생성기 - OAuth 2.0 초기 인증")
    print("=" * 70)
    print()

    # 1. 환경 변수 확인
    oauth_client_path = os.getenv("OAUTH_CLIENT_SECRETS_PATH", "./secrets/oauth_client_secret.json")
    token_path = os.getenv("OAUTH_TOKEN_PATH", "./secrets/token.json")
    spreadsheet_id = os.getenv("SPREADSHEET_ID", "")

    print(f"📋 설정 확인:")
    print(f"  - OAuth 클라이언트 ID: {oauth_client_path}")
    print(f"  - 토큰 저장 경로: {token_path}")
    print(f"  - 스프레드시트 ID: {spreadsheet_id[:40]}...")
    print()

    # 2. OAuth 클라이언트 ID 파일 확인
    if not Path(oauth_client_path).exists():
        print("❌ OAuth 2.0 클라이언트 ID 파일을 찾을 수 없습니다!")
        print()
        print("다음 단계를 따라주세요:")
        print()
        print("1️⃣  Google Cloud Console 접속")
        print("   https://console.cloud.google.com")
        print()
        print("2️⃣  프로젝트 선택 또는 생성")
        print()
        print("3️⃣  Google Sheets API 활성화")
        print("   - API 및 서비스 → 라이브러리")
        print("   - 'Google Sheets API' 검색 → 사용 설정")
        print()
        print("4️⃣  OAuth 2.0 클라이언트 ID 생성")
        print("   - API 및 서비스 → 사용자 인증 정보")
        print("   - '+ 사용자 인증 정보 만들기' → 'OAuth 클라이언트 ID'")
        print("   - 애플리케이션 유형: '데스크톱 앱'")
        print("   - 이름: 'FAQ 생성기' (또는 원하는 이름)")
        print("   - '만들기' 클릭")
        print()
        print("5️⃣  JSON 파일 다운로드")
        print("   - 생성된 클라이언트 ID 우측의 다운로드 버튼 클릭")
        print(f"   - 다운로드한 파일을 '{oauth_client_path}'로 저장")
        print()
        print(f"💡 파일 위치: {Path(oauth_client_path).absolute()}")
        print()
        sys.exit(1)

    # 3. OAuth 설정 검증
    print("🔍 OAuth 2.0 클라이언트 ID 검증 중...")
    from app.services.google_oauth import validate_oauth_setup

    valid, message = validate_oauth_setup(oauth_client_path)
    print(f"   {message}")
    print()

    if not valid:
        print("❌ OAuth 설정을 다시 확인해주세요.")
        sys.exit(1)

    # 4. 인증 시작
    print("🔐 OAuth 2.0 인증 시작...")
    print()
    print("👉 잠시 후 브라우저가 열립니다.")
    print("   1. Google 계정으로 로그인")
    print("   2. 'FAQ 생성기' 앱에 권한 부여")
    print("   3. '계속' 또는 '허용' 클릭")
    print()
    input("준비되었으면 Enter 키를 누르세요...")
    print()

    try:
        from app.services.google_oauth import get_oauth_credentials
        import gspread

        # OAuth 인증
        creds = get_oauth_credentials(
            client_secrets_path=oauth_client_path,
            token_path=token_path,
        )

        print()
        print("✅ OAuth 2.0 인증 완료!")
        print(f"   토큰 저장됨: {token_path}")
        print()

        # 5. Google Sheets 연결 테스트
        print("🧪 Google Sheets 연결 테스트 중...")

        client = gspread.authorize(creds)
        
        if not spreadsheet_id:
            print("⚠️  SPREADSHEET_ID가 설정되지 않았습니다.")
            print("   .env 파일에서 SPREADSHEET_ID를 설정하세요.")
            print()
        else:
            try:
                sheet = client.open_by_key(spreadsheet_id)
                print(f"✅ 스프레드시트 연결 성공!")
                print(f"   제목: {sheet.title}")
                print(f"   시트 목록: {[ws.title for ws in sheet.worksheets()]}")
                print()
            except Exception as e:
                print(f"❌ 스프레드시트 접근 실패: {e}")
                print()
                print("다음을 확인하세요:")
                print("  1. SPREADSHEET_ID가 올바른지 확인")
                print("  2. 해당 스프레드시트가 OAuth 인증한 계정과 공유되어 있는지 확인")
                print()
                sys.exit(1)

        # 완료
        print("=" * 70)
        print("🎉 OAuth 2.0 설정 완료!")
        print("=" * 70)
        print()
        print("이제 FAQ 생성기를 실행할 수 있습니다:")
        print()
        print("  # Streamlit 대시보드")
        print("  streamlit run dashboard/app.py")
        print()
        print("  # FastAPI 서버")
        print("  uvicorn app.main:app --reload")
        print()
        print("  # Docker Compose")
        print("  ./deploy.sh up")
        print()

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

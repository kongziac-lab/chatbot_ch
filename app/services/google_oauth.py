"""Google OAuth 2.0 인증 헬퍼.

서비스 계정 키 대신 사용자 계정으로 인증합니다.
최초 1회 브라우저 인증 후 토큰을 자동으로 갱신합니다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from loguru import logger

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_oauth_credentials(
    client_secrets_path: str | Path,
    token_path: str | Path = "./token.json",
) -> Credentials:
    """OAuth 2.0 사용자 인증 정보를 가져옵니다.

    Args:
        client_secrets_path: OAuth 2.0 클라이언트 ID JSON 파일 경로
        token_path: 액세스 토큰 저장 경로 (자동 갱신)

    Returns:
        Google OAuth2 Credentials 객체

    Raises:
        FileNotFoundError: client_secrets 파일이 없는 경우
        Exception: 인증 실패 시

    사용 예시:
        ```python
        creds = get_oauth_credentials("./oauth_client_secret.json")
        client = gspread.authorize(creds)
        ```

    최초 실행 시:
        1. 브라우저가 자동으로 열립니다
        2. Google 계정으로 로그인
        3. 권한 승인
        4. 토큰이 token.json에 저장됩니다

    이후 실행:
        - token.json에서 자동으로 로드
        - 만료 시 자동 갱신
    """
    client_secrets_path = Path(client_secrets_path)
    token_path = Path(token_path)

    if not client_secrets_path.exists():
        raise FileNotFoundError(
            f"OAuth 2.0 클라이언트 ID 파일을 찾을 수 없습니다: {client_secrets_path}\n"
            f"Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고 다운로드하세요.\n"
            f"자세한 방법은 README_OAUTH.md를 참고하세요."
        )

    creds = None

    # 기존 토큰 파일이 있으면 로드
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            logger.info(f"기존 OAuth 토큰 로드: {token_path}")
        except Exception as e:
            logger.warning(f"토큰 파일 로드 실패 ({e}), 재인증이 필요합니다.")
            creds = None

    # 토큰이 없거나 만료된 경우
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("OAuth 토큰 갱신 중...")
                creds.refresh(Request())
                logger.info("✅ OAuth 토큰 갱신 완료")
            except Exception as e:
                logger.warning(f"토큰 갱신 실패 ({e}), 재인증이 필요합니다.")
                creds = None

        # 새로운 인증 필요
        if not creds:
            logger.info("OAuth 2.0 인증 시작 - 브라우저가 열립니다...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(client_secrets_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("✅ OAuth 2.0 인증 완료")
            except Exception as e:
                logger.error(f"OAuth 인증 실패: {e}")
                raise

        # 토큰 저장
        try:
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())
            logger.info(f"OAuth 토큰 저장: {token_path}")
        except Exception as e:
            logger.warning(f"토큰 저장 실패: {e}")

    return creds


def validate_oauth_setup(client_secrets_path: str | Path) -> tuple[bool, str]:
    """OAuth 2.0 설정이 올바른지 검증합니다.

    Args:
        client_secrets_path: OAuth 2.0 클라이언트 ID JSON 파일 경로

    Returns:
        (성공 여부, 메시지) 튜플
    """
    client_secrets_path = Path(client_secrets_path)

    if not client_secrets_path.exists():
        return False, f"OAuth 클라이언트 ID 파일이 없습니다: {client_secrets_path}"

    try:
        with open(client_secrets_path, "r") as f:
            data = json.load(f)

        # 올바른 형식 확인
        if "installed" not in data and "web" not in data:
            return False, "유효하지 않은 OAuth 클라이언트 ID 형식입니다."

        client_type = "installed" if "installed" in data else "web"
        client_data = data[client_type]

        required_fields = ["client_id", "client_secret", "auth_uri", "token_uri"]
        missing = [f for f in required_fields if f not in client_data]

        if missing:
            return False, f"필수 필드 누락: {', '.join(missing)}"

        return True, "✅ OAuth 2.0 클라이언트 ID 설정이 올바릅니다."

    except json.JSONDecodeError:
        return False, "OAuth 클라이언트 ID 파일이 올바른 JSON 형식이 아닙니다."
    except Exception as e:
        return False, f"OAuth 설정 검증 실패: {e}"

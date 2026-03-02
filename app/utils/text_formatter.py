"""텍스트 서식 변환 유틸리티.

Google Sheets의 서식(볼드, 링크)을 마크다운/HTML로 변환합니다.
"""

from __future__ import annotations

import re
from typing import Any


def parse_rich_text_runs(cell_data: dict[str, Any]) -> str:
    """Google Sheets API의 textFormatRuns를 파싱하여 마크다운으로 변환.
    
    Args:
        cell_data: Google Sheets API v4의 CellData 객체
        
    Returns:
        마크다운 형식의 텍스트 (볼드: **텍스트**)
    """
    if not cell_data:
        return ""
    
    # effectiveValue에서 실제 텍스트 추출
    if "effectiveValue" not in cell_data:
        return ""
    
    effective_value = cell_data["effectiveValue"]
    
    # 문자열 값 추출
    if "stringValue" in effective_value:
        text = effective_value["stringValue"]
    elif "numberValue" in effective_value:
        return str(effective_value["numberValue"])
    elif "boolValue" in effective_value:
        return str(effective_value["boolValue"])
    else:
        return ""
    
    # textFormatRuns가 없으면 일반 텍스트 반환
    if "textFormatRuns" not in cell_data:
        return text
    
    runs = cell_data["textFormatRuns"]
    
    # runs가 비어있거나 없으면 일반 텍스트
    if not runs:
        return text
    
    # 각 run의 시작 인덱스와 서식 정보
    result = []
    text_len = len(text)
    
    for i, run in enumerate(runs):
        start_index = run.get("startIndex", 0)
        
        # 다음 run의 시작 인덱스 (없으면 텍스트 끝)
        if i + 1 < len(runs):
            end_index = runs[i + 1].get("startIndex", text_len)
        else:
            end_index = text_len
        
        # 해당 범위의 텍스트 추출
        segment = text[start_index:end_index]
        
        # 서식 적용
        if "format" in run:
            text_format = run["format"]
            
            # 볼드체
            if text_format.get("bold", False):
                segment = f"**{segment}**"
            
            # 이탤릭
            if text_format.get("italic", False):
                segment = f"*{segment}*"
            
            # 밑줄
            if text_format.get("underline", False):
                segment = f"__{segment}__"
            
            # 취소선
            if text_format.get("strikethrough", False):
                segment = f"~~{segment}~~"
            
            # 링크
            if "link" in text_format:
                link_url = text_format["link"].get("uri", "")
                if link_url:
                    segment = f"[{segment}]({link_url})"
        
        result.append(segment)
    
    return "".join(result)


def extract_hyperlink_from_cell(cell_data: dict[str, Any]) -> tuple[str, str | None]:
    """셀에서 하이퍼링크 추출.
    
    Args:
        cell_data: Google Sheets API v4의 CellData 객체
        
    Returns:
        (텍스트, URL) 튜플. URL이 없으면 (텍스트, None)
    """
    if not cell_data:
        return "", None
    
    # 1. 직접 hyperlink 필드 확인
    hyperlink = cell_data.get("hyperlink")
    if hyperlink:
        text = ""
        if "effectiveValue" in cell_data:
            effective_value = cell_data["effectiveValue"]
            text = effective_value.get("stringValue", "")
        return text, hyperlink
    
    # 2. textFormatRuns에서 링크 확인
    if "textFormatRuns" in cell_data:
        runs = cell_data["textFormatRuns"]
        for run in runs:
            if "format" in run:
                text_format = run["format"].get("textFormat", {})
                if "link" in text_format:
                    link_url = text_format["link"].get("uri", "")
                    if link_url:
                        # 링크가 있는 텍스트 추출
                        effective_value = cell_data.get("effectiveValue", {})
                        text = effective_value.get("stringValue", "")
                        return text, link_url
    
    # 3. HYPERLINK 함수 파싱
    if "userEnteredValue" in cell_data:
        user_value = cell_data["userEnteredValue"]
        if "formulaValue" in user_value:
            formula = user_value["formulaValue"]
            if formula.startswith("=HYPERLINK"):
                # =HYPERLINK("URL", "텍스트") 파싱
                match = re.match(r'=HYPERLINK\("(.+?)",\s*"(.+?)"\)', formula)
                if match:
                    url = match.group(1)
                    text = match.group(2)
                    return text, url
                
                # =HYPERLINK("URL") 형식
                match = re.match(r'=HYPERLINK\("(.+?)"\)', formula)
                if match:
                    url = match.group(1)
                    return url, url
    
    # 링크가 없는 경우
    if "effectiveValue" in cell_data:
        effective_value = cell_data["effectiveValue"]
        text = effective_value.get("stringValue", "")
        return text, None
    
    return "", None


def parse_cell_with_formatting(cell_data: dict[str, Any]) -> str:
    """셀 데이터를 파싱하여 마크다운 형식으로 변환.
    
    볼드, 이탤릭, 링크 등을 모두 처리합니다.
    
    Args:
        cell_data: Google Sheets API v4의 CellData 객체
        
    Returns:
        마크다운 형식의 텍스트
    """
    if not cell_data:
        return ""
    
    # 하이퍼링크가 있는 경우
    text, url = extract_hyperlink_from_cell(cell_data)
    if url:
        # 텍스트에 볼드 등의 서식이 있을 수 있으므로 rich text 파싱
        formatted_text = parse_rich_text_runs(cell_data)
        if formatted_text and formatted_text != text:
            # 이미 링크 마크다운이 포함되어 있으면 그대로 반환
            if f"({url})" in formatted_text:
                return formatted_text
            # 아니면 링크로 감싸기
            return f"[{formatted_text}]({url})"
        return f"[{text}]({url})" if text else url
    
    # 일반 서식 처리
    return parse_rich_text_runs(cell_data)


def markdown_to_html(markdown_text: str) -> str:
    """간단한 마크다운을 HTML로 변환.
    
    Args:
        markdown_text: 마크다운 텍스트
        
    Returns:
        HTML 텍스트
    """
    if not markdown_text:
        return ""
    
    html = markdown_text
    
    # 링크: [텍스트](URL) → <a href="URL" target="_blank">텍스트</a>
    html = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2" target="_blank" class="text-blue-600 hover:text-blue-800 underline">\1</a>',
        html
    )
    
    # 볼드: **텍스트** → <strong>텍스트</strong>
    html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)
    
    # 이탤릭: *텍스트* (볼드 아닌 경우) → <em>텍스트</em>
    html = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', html)
    
    # 밑줄: __텍스트__ → <u>텍스트</u>
    html = re.sub(r'__([^_]+)__', r'<u>\1</u>', html)
    
    # 취소선: ~~텍스트~~ → <del>텍스트</del>
    html = re.sub(r'~~([^~]+)~~', r'<del>\1</del>', html)
    
    # 줄바꿈 처리
    html = html.replace('\n', '<br>')
    
    return html

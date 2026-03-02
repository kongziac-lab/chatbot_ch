// ============================================================
// FAQ Manager — Google Apps Script
// ============================================================
// 설치 방법:
//   1. Google Sheets 메뉴 → 확장 프로그램 → Apps Script
//   2. 이 파일 전체를 붙여넣기
//   3. ADMIN_EMAIL, MANAGER_EMAIL 상수를 실제 이메일로 변경
//   4. setup() 함수를 수동으로 한 번 실행 (트리거 + 조건부 서식 설치)
// ============================================================

// ────────────────────────────────────────────────────────────
// 설정 상수
// ────────────────────────────────────────────────────────────
var SHEET_NAME    = "FAQ_Master";
var ADMIN_EMAIL   = "admin@example.com";     // 일일 리포트 수신자
var MANAGER_EMAIL = "manager@example.com";   // 게시 승인 알림 수신자

// ── 자동 동기화 설정 ──────────────────────────────────────────
var API_BASE_URL  = "http://localhost:8002";  // FastAPI 서버 주소
var WEBHOOK_SECRET = "faq-auto-sync-secret-2026";  // .env의 WEBHOOK_SECRET과 동일하게

// FAQ_Master 열 인덱스 (1-based)
var COL = {
  ID:          1,   // A: 고유번호
  CAT_MAJOR:   2,   // B: 카테고리(대분류)
  CAT_MINOR:   3,   // C: 카테고리(중분류)
  Q_KO:        4,   // D: 질문(한국어)
  A_KO:        5,   // E: 답변(한국어)
  Q_ZH:        6,   // F: 질문(중국어)
  A_ZH:        7,   // G: 답변(중국어)
  SOURCE:      8,   // H: 출처
  STATUS:      9,   // I: 상태  ← 핵심 열
  DEPARTMENT:  10,  // J: 생성부서
  SCOPE:       11,  // K: 적용범위
  CREATED_AT:  12,  // L: 생성일
  UPDATED_AT:  13,  // M: 수정일  ← 자동 갱신
  PRIORITY:    14,  // N: 우선순위
  VIEW_COUNT:  15,  // O: 조회수
  HELPFUL_PCT: 16,  // P: 도움됨비율
};

// 상태 값
var STATUS = {
  AUTO:      "자동생성",
  REVIEW:    "검수대기",
  PUBLISHED: "게시중",
  REJECTED:  "폐기",
};

// 조건부 서식 색상
var COLORS = {
  AUTO:      { bg: "#FFF9C4", font: "#6D4C00" },  // 노란 배경
  REVIEW:    { bg: "#BBDEFB", font: "#0D47A1" },  // 파란 배경
  PUBLISHED: { bg: "#C8E6C9", font: "#1B5E20" },  // 초록 배경
  REJECTED:  { bg: "#EEEEEE", font: "#616161" },  // 회색 배경
};


// ============================================================
// 1. onEdit 트리거
// ============================================================

/**
 * FAQ 편집 감지 (실시간 증분 업데이트):
 *   - 상태(I열) 변경: 수정일 갱신 + 알림 + 벡터 동기화
 *   - FAQ 내용(D-G열) 변경: 수정일 갱신 + 벡터 동기화 (게시중인 경우만)
 */
function onEdit(e) {
  var range = e.range;
  var sheet = range.getSheet();

  // FAQ_Master 시트에서만 동작
  if (sheet.getName() !== SHEET_NAME) return;

  // 헤더 행(1행) 제외
  var row = range.getRow();
  if (row <= 1) return;

  var col = range.getColumn();
  var now = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy-MM-dd HH:mm:ss");
  
  // ═══════════════════════════════════════════════════════════
  // Case 1: 상태(I열) 변경
  // ═══════════════════════════════════════════════════════════
  if (col === COL.STATUS) {
    var newStatus = range.getValue();
    
    // 수정일 자동 갱신
    sheet.getRange(row, COL.UPDATED_AT).setValue(now);
    
    // 행 배경색 갱신
    _applyRowColor(sheet, row, newStatus);
    
    // 게시중 변경 시 이메일 알림
    if (newStatus === STATUS.PUBLISHED) {
      var questionKo = sheet.getRange(row, COL.Q_KO).getValue();
      var faqId      = sheet.getRange(row, COL.ID).getValue();
      var department = sheet.getRange(row, COL.DEPARTMENT).getValue();
      _sendPublishNotification(faqId, questionKo, department, now);
      
      // 벡터 DB 자동 동기화 (증분 업데이트)
      _triggerAutoSync();
    }
    
    // 게시중에서 다른 상태로 변경 시에도 동기화 (FAQ 제거)
    if (newStatus !== STATUS.PUBLISHED) {
      _triggerAutoSync();
    }
    
    return;
  }
  
  // ═══════════════════════════════════════════════════════════
  // Case 2: FAQ 내용(질문/답변) 변경 - 게시중인 경우만 자동 동기화
  // ═══════════════════════════════════════════════════════════
  var isFaqContentColumn = (
    col === COL.Q_KO ||     // 질문(한국어)
    col === COL.A_KO ||     // 답변(한국어)
    col === COL.Q_ZH ||     // 질문(중국어)
    col === COL.A_ZH        // 답변(중국어)
  );
  
  if (isFaqContentColumn) {
    var currentStatus = sheet.getRange(row, COL.STATUS).getValue();
    
    // 게시중인 FAQ만 동기화 (임시저장/검수대기는 동기화 불필요)
    if (currentStatus === STATUS.PUBLISHED) {
      // 수정일 자동 갱신
      sheet.getRange(row, COL.UPDATED_AT).setValue(now);
      
      // 벡터 DB 증분 업데이트 (변경된 FAQ만 재벡터화)
      Logger.log("FAQ 내용 변경 감지 | row=" + row + " | col=" + col + " | 증분 동기화 시작");
      _triggerAutoSync();
    }
  }
}


// ============================================================
// 2. 일일 리포트 (오전 9시 시간 기반 트리거)
// ============================================================

/**
 * 전체 FAQ 현황을 집계해 관리자에게 이메일로 발송.
 * setup() 에서 시간 기반 트리거로 등록됨.
 */
function sendDailyReport() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) {
    Logger.log("시트를 찾을 수 없습니다: " + SHEET_NAME);
    return;
  }

  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) {
    Logger.log("데이터가 없습니다.");
    return;
  }

  // 어제/오늘 날짜
  var today     = new Date();
  var yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  var todayStr     = Utilities.formatDate(today,     "Asia/Seoul", "yyyy-MM-dd");
  var yesterdayStr = Utilities.formatDate(yesterday, "Asia/Seoul", "yyyy-MM-dd");

  // 집계
  var counts = { total: 0, published: 0, review: 0, auto: 0, rejected: 0, newToday: 0 };

  for (var i = 1; i < data.length; i++) {
    var row    = data[i];
    var status = String(row[COL.STATUS - 1] || "").trim();
    var created = String(row[COL.CREATED_AT - 1] || "").substring(0, 10);

    if (!status) continue;
    counts.total++;

    if (status === STATUS.PUBLISHED) counts.published++;
    else if (status === STATUS.REVIEW)    counts.review++;
    else if (status === STATUS.AUTO)      counts.auto++;
    else if (status === STATUS.REJECTED)  counts.rejected++;

    if (created === todayStr || created === yesterdayStr) counts.newToday++;
  }

  // 카테고리별 집계
  var catMap = {};
  for (var i = 1; i < data.length; i++) {
    var cat = String(data[i][COL.CAT_MAJOR - 1] || "미분류").trim();
    catMap[cat] = (catMap[cat] || 0) + 1;
  }
  var catLines = Object.keys(catMap)
    .sort(function(a, b) { return catMap[b] - catMap[a]; })
    .slice(0, 5)
    .map(function(k) { return "  • " + k + ": " + catMap[k] + "건"; })
    .join("\n");

  // 이메일 본문 작성
  var subject = "[FAQ 시스템] 일일 현황 리포트 — " + todayStr;
  var body = [
    "안녕하세요,",
    "FAQ 관리 시스템 일일 현황 리포트입니다.",
    "",
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "■ 전체 현황 (" + todayStr + " 기준)",
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "  전체 FAQ :  " + counts.total + "건",
    "  게시중   :  " + counts.published + "건",
    "  검수대기 :  " + counts.review + "건",
    "  자동생성 :  " + counts.auto + "건",
    "  폐기     :  " + counts.rejected + "건",
    "",
    "■ 신규 생성 (오늘/어제)",
    "  " + counts.newToday + "건",
    "",
    "■ 카테고리별 상위 5개",
    catLines || "  데이터 없음",
    "",
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "검수 대기 FAQ 가 있다면 FAQ 관리 대시보드에서 검토해 주세요.",
    "",
    "본 메일은 자동 발송됩니다.",
  ].join("\n");

  MailApp.sendEmail({
    to:      ADMIN_EMAIL,
    subject: subject,
    body:    body,
  });

  Logger.log("일일 리포트 발송 완료 → " + ADMIN_EMAIL);
}


// ============================================================
// 3. 조건부 서식 일괄 적용
// ============================================================

/**
 * FAQ_Master 시트 전체 행에 상태별 배경색을 적용.
 * setup() 또는 수동으로 실행.
 */
function applyConditionalFormatting() {
  var ss    = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    SpreadsheetApp.getUi().alert("시트 '" + SHEET_NAME + "'을 찾을 수 없습니다.");
    return;
  }

  // 기존 조건부 서식 규칙 모두 제거
  sheet.clearConditionalFormatRules();

  var lastCol  = sheet.getLastColumn() || COL.HELPFUL_PCT;
  var lastRow  = Math.max(sheet.getLastRow(), 2);
  var fullRange = sheet.getRange(2, 1, lastRow - 1, lastCol);

  var rules = [];

  // 상태 매핑
  var statusColorMap = [
    { status: STATUS.AUTO,      color: COLORS.AUTO      },
    { status: STATUS.REVIEW,    color: COLORS.REVIEW    },
    { status: STATUS.PUBLISHED, color: COLORS.PUBLISHED },
    { status: STATUS.REJECTED,  color: COLORS.REJECTED  },
  ];

  statusColorMap.forEach(function(sc) {
    var rule = SpreadsheetApp.newConditionalFormatRule()
      .whenFormulaSatisfied(
        '=$' + _colLetter(COL.STATUS) + '2="' + sc.status + '"'
      )
      .setBackground(sc.color.bg)
      .setFontColor(sc.color.font)
      .setRanges([fullRange])
      .build();
    rules.push(rule);
  });

  sheet.setConditionalFormatRules(rules);
  Logger.log("조건부 서식 적용 완료");
}


// ============================================================
// 4. 시간 기반 자동 동기화 (옵션)
// ============================================================

/**
 * 시간 기반 자동 동기화 (예: 매 1시간마다 실행)
 * 
 * 사용 시나리오:
 *   - onEdit으로 감지 못한 대량 수정 처리
 *   - 외부 API를 통한 FAQ 변경 감지
 *   - 정기적인 백업 동기화
 * 
 * 설정 방법:
 *   1. setup() 함수에서 자동으로 트리거 생성
 *   2. 또는 수동으로 이 함수를 Apps Script 트리거에 등록
 */
function scheduledAutoSync() {
  Logger.log("시간 기반 자동 동기화 시작");
  
  try {
    _triggerAutoSync();
    Logger.log("시간 기반 자동 동기화 성공");
  } catch (error) {
    Logger.log("시간 기반 자동 동기화 실패: " + error);
    
    // 관리자에게 이메일 알림 (옵션)
    if (ADMIN_EMAIL && ADMIN_EMAIL !== "admin@example.com") {
      MailApp.sendEmail({
        to: ADMIN_EMAIL,
        subject: "[FAQ 생성기] 자동 동기화 실패",
        body: "시간: " + new Date() + "\n오류: " + error
      });
    }
  }
}


// ============================================================
// 5. 초기 설정 (수동 1회 실행)
// ============================================================

/**
 * 트리거 등록 + 조건부 서식 초기 적용.
 * Apps Script 편집기에서 수동으로 한 번만 실행하세요.
 * 
 * 옵션:
 *   - enableScheduledSync: true로 설정 시 1시간마다 자동 동기화 추가
 */
function setup(enableScheduledSync) {
  if (typeof enableScheduledSync === 'undefined') {
    enableScheduledSync = false;
  }
  
  _registerTriggers(enableScheduledSync);
  applyConditionalFormatting();
  
  var message = "설정 완료!\n\n" +
    "• onEdit 트리거 등록 (FAQ 수정 시 실시간 동기화)\n" +
    "• 일일 리포트 트리거 등록 (매일 오전 9시)\n" +
    "• 조건부 서식 적용";
  
  if (enableScheduledSync) {
    message += "\n• 시간 기반 자동 동기화 (1시간 간격)";
  }
  
  SpreadsheetApp.getUi().alert(message);
}

/**
 * 시간 기반 자동 동기화를 포함한 전체 설정.
 * 대규모 FAQ 운영 시 권장.
 */
function setupWithScheduledSync() {
  setup(true);
}

/**
 * 등록된 트리거를 모두 삭제하고 재등록.
 * 
 * 옵션:
 *   - enableScheduledSync: true로 설정 시 1시간마다 자동 동기화 (기본값: false)
 */
function _registerTriggers(enableScheduledSync) {
  if (typeof enableScheduledSync === 'undefined') {
    enableScheduledSync = false;  // 기본값: 시간 기반 동기화 비활성화
  }
  
  var ss = SpreadsheetApp.getActiveSpreadsheet();

  // 기존 트리거 삭제
  ScriptApp.getProjectTriggers().forEach(function(t) {
    ScriptApp.deleteTrigger(t);
  });

  // onEdit 트리거 (설치형 — 공유 시트에서도 동작)
  ScriptApp.newTrigger("onEdit")
    .forSpreadsheet(ss)
    .onEdit()
    .create();

  // 일일 리포트 트리거 (매일 오전 9~10시)
  ScriptApp.newTrigger("sendDailyReport")
    .timeBased()
    .everyDays(1)
    .atHour(9)
    .create();
  
  // ── 시간 기반 자동 동기화 트리거 (옵션) ──────────────────────
  if (enableScheduledSync) {
    ScriptApp.newTrigger("scheduledAutoSync")
      .timeBased()
      .everyHours(1)  // 1시간마다 실행
      .create();
    
    Logger.log("시간 기반 자동 동기화 트리거 등록 완료 (1시간 간격)");
  }

  Logger.log("트리거 등록 완료");
}


// ============================================================
// 내부 헬퍼
// ============================================================

/**
 * 특정 행에 상태별 배경색 적용 (onEdit 실시간 갱신용).
 */
function _applyRowColor(sheet, row, status) {
  var lastCol = sheet.getLastColumn() || COL.HELPFUL_PCT;
  var range   = sheet.getRange(row, 1, 1, lastCol);

  var colorMap = {};
  colorMap[STATUS.AUTO]      = COLORS.AUTO;
  colorMap[STATUS.REVIEW]    = COLORS.REVIEW;
  colorMap[STATUS.PUBLISHED] = COLORS.PUBLISHED;
  colorMap[STATUS.REJECTED]  = COLORS.REJECTED;

  var c = colorMap[status];
  if (c) {
    range.setBackground(c.bg).setFontColor(c.font);
  } else {
    range.setBackground(null).setFontColor(null);
  }
}

/**
 * 게시 승인 이메일 알림 발송.
 */
function _sendPublishNotification(faqId, questionKo, department, publishedAt) {
  var subject = "[FAQ 시스템] 새 FAQ가 게시되었습니다";
  var body = [
    "새로운 FAQ가 게시 상태로 변경되었습니다.",
    "",
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "  FAQ ID   : " + faqId,
    "  질문     : " + questionKo,
    "  생성 부서: " + (department || "미지정"),
    "  게시 일시: " + publishedAt,
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "",
    "FAQ 관리 대시보드에서 내용을 확인하세요.",
  ].join("\n");

  MailApp.sendEmail({
    to:      MANAGER_EMAIL,
    subject: subject,
    body:    body,
  });
}

/**
 * 열 번호(1-based) → 열 문자 변환 (예: 1→A, 9→I).
 */
function _colLetter(colNum) {
  var letter = "";
  while (colNum > 0) {
    var mod = (colNum - 1) % 26;
    letter  = String.fromCharCode(65 + mod) + letter;
    colNum  = Math.floor((colNum - 1) / 26);
  }
  return letter;
}


// ============================================================
// 7. 자동 동기화 (Webhook)
// ============================================================

/**
 * FastAPI 서버에 FAQ 자동 동기화 Webhook 호출.
 * FAQ 상태가 "게시중"으로 변경되거나 "게시중"에서 변경될 때 자동 실행.
 */
function _triggerAutoSync() {
  var url = API_BASE_URL + "/api/v1/faq/webhook/auto-sync";
  
  var options = {
    method: "post",
    headers: {
      "Content-Type": "application/json",
      "X-Webhook-Secret": WEBHOOK_SECRET
    },
    muteHttpExceptions: true
  };
  
  try {
    var response = UrlFetchApp.fetch(url, options);
    var statusCode = response.getResponseCode();
    
    if (statusCode === 202) {
      Logger.log("✅ FAQ 자동 동기화 Webhook 호출 성공");
    } else {
      Logger.log("⚠️ Webhook 호출 실패: " + statusCode + " - " + response.getContentText());
    }
  } catch (e) {
    Logger.log("❌ Webhook 호출 오류: " + e.toString());
    // 오류가 발생해도 사용자 작업은 방해하지 않음
  }
}

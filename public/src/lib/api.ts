/**
 * FastAPI 클라이언트 모듈
 */

import type { FAQItem, Language } from '@/types';

const PROD_API_FALLBACK = 'https://chatbot-ch-backend.zeabur.app';
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD ? PROD_API_FALLBACK : 'http://localhost:8000');

export interface ChatResponse {
  answer: string;
  language: string;
  related_faqs: Array<{
    faq_id: string;
    question: string;
    language: Language;
  }>;
  session_id: string;
  confidence: 'high' | 'medium' | 'low';
}

export interface FeedbackRequest {
  message: string;
  answer: string;
  helpful: boolean;
  comment?: string;
}

export interface FAQListResponse {
  items: FAQItem[];
  total: number;
  language: Language;
}

/**
 * 챗봇 API 호출
 */
export const chatApi = {
  /**
   * 메시지 전송
   */
  async sendMessage(message: string, sessionId: string | null = null): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`API 호출 실패: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 피드백 전송
   */
  async sendFeedback(feedback: FeedbackRequest): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(feedback),
    });

    if (!response.ok) {
      throw new Error(`피드백 전송 실패: ${response.status}`);
    }
  },

  /**
   * 헬스 체크
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/health`);
    return response.json();
  },
};

/**
 * FAQ API 호출
 */
export const faqApi = {
  /**
   * 카테고리별 FAQ 목록 조회
   */
  async getFAQsByCategory(
    categoryMajor: string,
    categoryMinor: string,
    language: Language = 'ko'
  ): Promise<FAQItem[]> {
    const params = new URLSearchParams({
      category_major: categoryMajor,
      category_minor: categoryMinor,
      lang: language,
    });

    const url = `${API_BASE_URL}/api/v1/faqs?${params}`;
    console.log('API 요청 URL:', url);
    console.log('API_BASE_URL:', API_BASE_URL);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60초 타임아웃

    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);

    console.log('API 응답 상태:', response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API 응답 에러:', errorText);
      throw new Error(`FAQ 조회 실패: ${response.status} ${response.statusText}\n${errorText}`);
    }

    const data: FAQListResponse = await response.json();
    console.log('API 응답 데이터:', data);
    return data.items;
  },

  /**
   * FAQ 상세 조회
   */
  async getFAQById(faqId: string, language: Language = 'ko'): Promise<FAQItem> {
    const url = `${API_BASE_URL}/api/v1/faqs/${encodeURIComponent(faqId)}?lang=${language}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`FAQ 상세 조회 실패: ${response.status}`);
    }
    return response.json();
  },
};

/**
 * 마크다운을 HTML로 변환
 */
export function markdownToHtml(markdown: string, language: Language = 'ko'): string {
  if (!markdown) return '';

  let html = markdown;

  // 링크: [텍스트](URL) → <a href="URL" target="_blank">텍스트</a>
  html = html.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">$1</a>'
  );

  // 링크: 텍스트(URL) → 텍스트(바로가기 🔗)
  html = html.replace(
    /(^|[\s>])([^\s<()（）]+(?:\s+[^\s<()（）]+)*)[（(]((?:https?:\/\/|www\.)[^\s)）]+)[）)]/g,
    (_m, prefix, label, rawUrl) => {
      const href = rawUrl.startsWith('www.') ? `https://${rawUrl}` : rawUrl;
      const linkLabel = language === 'zh' ? '直达链接 🔗' : '바로가기 🔗';
      return `${prefix}${label}(<a href="${href}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">${linkLabel}</a>)`;
    }
  );

  // 일반 URL: https://... → <a href="...">...</a>
  html = html.replace(
    /(^|[\s(（])(https?:\/\/[^\s<)）]+)/g,
    '$1<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">$2</a>'
  );

  // www URL: www.example.com → <a href="https://www.example.com">www.example.com</a>
  html = html.replace(
    /(^|[\s(（])(www\.[^\s<)）]+)/g,
    '$1<a href="https://$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">$2</a>'
  );

  // 볼드: **텍스트** → <strong>텍스트</strong>
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // 이탤릭: *텍스트* (볼드 아닌 경우) → <em>텍스트</em>
  html = html.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>');

  // 밑줄: __텍스트__ → <u>텍스트</u>
  html = html.replace(/__([^_]+)__/g, '<u>$1</u>');

  // 취소선: ~~텍스트~~ → <del>텍스트</del>
  html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>');

  // 줄바꿈/목록 서식 처리 (번호 목록 + 보조문장 들여쓰기)
  const lines = html.split('\n');
  let prevWasNumbered = false;
  html = lines
    .map((line) => {
      const trimmed = line.trim();
      if (!trimmed) {
        prevWasNumbered = false;
        return '<div class="h-3"></div>';
      }

      const numbered = trimmed.match(/^(\d+)\.\s*(.*)$/);
      if (numbered) {
        prevWasNumbered = true;
        return `<div class="flex items-start gap-1 my-1">
          <span class="text-blue-600 font-semibold min-w-[1rem]">${numbered[1]}.</span>
          <span class="flex-1">${numbered[2]}</span>
        </div>`;
      }

      if (trimmed.startsWith('※')) {
        prevWasNumbered = false;
        return `<div class="my-2">${trimmed}</div>`;
      }

      if (prevWasNumbered) {
        return `<div class="pl-8 my-1">${trimmed}</div>`;
      }

      const startsWithText = /^[A-Za-z\u00C0-\u024F\u4E00-\u9FFF\u3400-\u4DBF\uAC00-\uD7AF]/.test(trimmed);
      if (startsWithText) {
        prevWasNumbered = false;
        return `<div class="flex items-start gap-2 my-1">
          <span class="text-blue-600 font-semibold leading-none mt-1">•</span>
          <span class="flex-1">${trimmed}</span>
        </div>`;
      }

      prevWasNumbered = false;
      return `<div>${trimmed}</div>`;
    })
    .join('');

  return html;
}

export { API_BASE_URL };

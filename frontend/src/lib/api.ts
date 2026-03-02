const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export interface FAQItem {
  faq_id: string;
  category_major: string;
  category_minor: string;
  question: string;
  answer: string;
  source: string;
  scope: string;
  priority: number;
  view_count: number;
  helpful_pct: number | null;
  language: string;
}

export interface FAQListResponse {
  items: FAQItem[];
  total: number;
  language: string;
}

export interface FAQDetailResponse extends FAQItem {
  question_ko: string;
  answer_ko: string;
  question_zh: string;
  answer_zh: string;
  created_at: string;
  updated_at: string;
}

export interface ChatResponse {
  answer: string;
  language: string;
  session_id: string;
  confidence: string;
  related_faqs: Array<{ faq_id: string; question: string; language: string }>;
}

export async function fetchFAQs(params?: {
  category?: string;
  search?: string;
  lang?: string;
  scope?: string;
}): Promise<FAQListResponse> {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.search)   query.set("search",   params.search);
  if (params?.lang)     query.set("lang",      params.lang);
  if (params?.scope)    query.set("scope",     params.scope);

  const res = await fetch(`${API_BASE}/api/v1/faqs?${query}`, {
    next: { revalidate: 60 },   // ISR: 60초마다 갱신
  });
  if (!res.ok) throw new Error(`FAQ 목록 조회 실패: ${res.status}`);
  return res.json();
}

export async function fetchFAQDetail(
  faqId: string,
  lang = "ko"
): Promise<FAQDetailResponse> {
  const res = await fetch(
    `${API_BASE}/api/v1/faqs/${faqId}?lang=${lang}`,
    { cache: "no-store" }   // 조회수 반영을 위해 캐시 비활성
  );
  if (!res.ok) throw new Error(`FAQ 상세 조회 실패: ${res.status}`);
  return res.json();
}

export async function submitFeedback(
  faqId: string,
  helpful: boolean,
  comment = "",
  language = "ko"
) {
  const res = await fetch(`${API_BASE}/api/v1/faqs/${faqId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ helpful, comment, language }),
  });
  if (!res.ok) throw new Error("피드백 저장 실패");
  return res.json();
}

export async function sendChat(
  message: string,
  sessionId?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (!res.ok) throw new Error("챗봇 응답 실패");
  return res.json();
}

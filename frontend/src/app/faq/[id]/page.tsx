import { notFound } from "next/navigation";
import { fetchFAQDetail } from "@/lib/api";
import FeedbackButtons from "@/components/FeedbackButtons";
import Link from "next/link";

interface Props {
  params:      { id: string };
  searchParams: { lang?: string };
}

export default async function FAQDetailPage({ params, searchParams }: Props) {
  const lang = searchParams.lang || "ko";

  let faq;
  try {
    faq = await fetchFAQDetail(params.id, lang);
  } catch {
    notFound();
  }

  const isZh = lang === "zh";

  return (
    <div className="max-w-3xl mx-auto">
      {/* 뒤로가기 */}
      <Link
        href={`/?lang=${lang}`}
        className="inline-flex items-center text-sm text-gray-500 hover:text-primary mb-6"
      >
        ← {isZh ? "返回列表" : "목록으로"}
      </Link>

      {/* 카테고리 배지 */}
      <div className="flex gap-2 mb-3">
        <span className="px-2 py-0.5 bg-blue-50 text-primary text-xs rounded-full border border-blue-200">
          {faq.category_major}
        </span>
        {faq.category_minor && (
          <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
            {faq.category_minor}
          </span>
        )}
      </div>

      {/* 질문 */}
      <h1 className="text-2xl font-bold mb-6 leading-snug text-gray-900">
        {isZh ? faq.question_zh || faq.question_ko : faq.question_ko}
      </h1>

      {/* 답변 */}
      <div className="bg-white rounded-xl border shadow-sm p-6 mb-6">
        <p className="text-sm font-semibold text-gray-500 mb-3">
          {isZh ? "解答" : "답변"}
        </p>
        <div className="whitespace-pre-wrap text-gray-800 leading-relaxed">
          {isZh ? faq.answer_zh || faq.answer_ko : faq.answer_ko}
        </div>
      </div>

      {/* 메타 정보 */}
      <div className="text-xs text-gray-400 flex flex-wrap gap-4 mb-6">
        {faq.source && <span>{isZh ? "来源" : "출처"}: {faq.source}</span>}
        <span>{isZh ? "浏览" : "조회수"}: {faq.view_count}</span>
        {faq.helpful_pct !== null && (
          <span>{isZh ? "有用率" : "도움됨"}: {faq.helpful_pct}%</span>
        )}
        <span>{isZh ? "更新" : "수정일"}: {faq.updated_at?.slice(0, 10)}</span>
      </div>

      {/* 언어 전환 */}
      {faq.question_zh && (
        <div className="mb-6">
          <Link
            href={`/faq/${params.id}?lang=${isZh ? "ko" : "zh"}`}
            className="text-sm text-primary underline underline-offset-2"
          >
            {isZh ? "한국어로 보기" : "查看中文版本"}
          </Link>
        </div>
      )}

      {/* 피드백 */}
      <FeedbackButtons faqId={params.id} lang={lang} />
    </div>
  );
}

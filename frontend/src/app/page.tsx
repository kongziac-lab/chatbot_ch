import Link from "next/link";
import { fetchFAQs, FAQItem } from "@/lib/api";
import SearchBar from "@/components/SearchBar";
import FAQCard from "@/components/FAQCard";
import LangToggle from "@/components/LangToggle";
import ChatWidget from "@/components/ChatWidget";

interface PageProps {
  searchParams: { lang?: string; search?: string; category?: string };
}

export default async function HomePage({ searchParams }: PageProps) {
  const lang     = searchParams.lang     || "ko";
  const search   = searchParams.search   || "";
  const category = searchParams.category || "";

  let items: FAQItem[] = [];
  let error = "";

  try {
    const data = await fetchFAQs({ lang, search, category });
    items = data.items;
  } catch (e) {
    error = "FAQ를 불러오는 중 오류가 발생했습니다.";
  }

  // 대분류 목록 (필터 버튼용)
  const categories = Array.from(new Set(items.map((i) => i.category_major))).sort();

  return (
    <>
      {/* 언어 토글 + 검색 */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-6">
        <LangToggle current={lang} />
        <div className="flex-1">
          <SearchBar defaultValue={search} lang={lang} />
        </div>
      </div>

      {/* 카테고리 필터 */}
      {categories.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          <Link
            href={`/?lang=${lang}${search ? `&search=${search}` : ""}`}
            className={`px-3 py-1 rounded-full text-sm border transition
              ${!category ? "bg-primary text-white border-primary" : "border-gray-300 hover:border-primary"}`}
          >
            {lang === "zh" ? "全部" : "전체"}
          </Link>
          {categories.map((cat) => (
            <Link
              key={cat}
              href={`/?lang=${lang}&category=${encodeURIComponent(cat)}${search ? `&search=${search}` : ""}`}
              className={`px-3 py-1 rounded-full text-sm border transition
                ${category === cat ? "bg-primary text-white border-primary" : "border-gray-300 hover:border-primary"}`}
            >
              {cat}
            </Link>
          ))}
        </div>
      )}

      {/* 결과 */}
      {error ? (
        <p className="text-red-500 text-center py-12">{error}</p>
      ) : items.length === 0 ? (
        <p className="text-gray-400 text-center py-12">
          {lang === "zh" ? "暂无相关FAQ。" : "검색 결과가 없습니다."}
        </p>
      ) : (
        <div className="space-y-3">
          {items.map((faq) => (
            <FAQCard key={faq.faq_id} faq={faq} lang={lang} />
          ))}
        </div>
      )}

      {/* 챗봇 위젯 */}
      <ChatWidget lang={lang} />
    </>
  );
}

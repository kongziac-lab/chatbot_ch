"use client";

import Link from "next/link";
import { useState } from "react";
import { FAQItem } from "@/lib/api";

interface Props {
  faq:  FAQItem;
  lang: string;
}

export default function FAQCard({ faq, lang }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="bg-white rounded-xl border shadow-sm overflow-hidden transition hover:shadow-md">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full text-left px-5 py-4 flex items-start gap-3"
      >
        <span className="mt-0.5 text-primary font-bold text-lg flex-shrink-0">Q</span>
        <span className="flex-1 font-medium text-gray-900">{faq.question}</span>
        <span className="ml-2 text-gray-400 text-lg">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t bg-gray-50">
          <p className="pt-4 text-gray-700 whitespace-pre-wrap leading-relaxed">
            {faq.answer}
          </p>
          <div className="mt-4 flex items-center justify-between">
            <div className="flex gap-2 text-xs text-gray-400">
              {faq.source && <span>출처: {faq.source}</span>}
              <span>조회 {faq.view_count}</span>
            </div>
            <Link
              href={`/faq/${faq.faq_id}?lang=${lang}`}
              className="text-xs text-primary underline underline-offset-2"
            >
              {lang === "zh" ? "查看详情" : "상세보기"}
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

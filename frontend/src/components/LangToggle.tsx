"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

export default function LangToggle({ current }: { current: string }) {
  const params = useSearchParams();

  function hrefFor(lang: string) {
    const qs = new URLSearchParams(params.toString());
    qs.set("lang", lang);
    return `/?${qs}`;
  }

  return (
    <div className="flex rounded-lg overflow-hidden border border-gray-300 flex-shrink-0">
      {(["ko", "zh"] as const).map((lang) => (
        <Link
          key={lang}
          href={hrefFor(lang)}
          className={`px-4 py-2 text-sm font-medium transition ${
            current === lang
              ? "bg-primary text-white"
              : "bg-white text-gray-600 hover:bg-gray-50"
          }`}
        >
          {lang === "ko" ? "한국어" : "中文"}
        </Link>
      ))}
    </div>
  );
}

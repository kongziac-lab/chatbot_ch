"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, FormEvent } from "react";

export default function SearchBar({
  defaultValue,
  lang,
}: {
  defaultValue: string;
  lang: string;
}) {
  const [value, setValue] = useState(defaultValue);
  const router = useRouter();
  const params = useSearchParams();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const qs = new URLSearchParams(params.toString());
    if (value.trim()) {
      qs.set("search", value.trim());
    } else {
      qs.delete("search");
    }
    qs.set("lang", lang);
    router.push(`/?${qs}`);
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="search"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={lang === "zh" ? "搜索常见问题…" : "FAQ 검색…"}
        className="flex-1 border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      />
      <button
        type="submit"
        className="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primary-light transition"
      >
        {lang === "zh" ? "搜索" : "검색"}
      </button>
    </form>
  );
}

"use client";

import { useState } from "react";
import { submitFeedback } from "@/lib/api";

export default function FeedbackButtons({
  faqId,
  lang,
}: {
  faqId: string;
  lang:  string;
}) {
  const [state, setState] = useState<"idle" | "done" | "error">("idle");
  const isZh = lang === "zh";

  async function handleFeedback(helpful: boolean) {
    try {
      await submitFeedback(faqId, helpful, "", lang);
      setState("done");
    } catch {
      setState("error");
    }
  }

  if (state === "done") {
    return (
      <p className="text-sm text-green-600">
        {isZh ? "感谢您的反馈！" : "피드백 감사합니다!"}
      </p>
    );
  }

  if (state === "error") {
    return (
      <p className="text-sm text-red-500">
        {isZh ? "提交失败，请稍后重试。" : "제출 중 오류가 발생했습니다."}
      </p>
    );
  }

  return (
    <div>
      <p className="text-sm text-gray-500 mb-3">
        {isZh ? "这个回答对您有帮助吗？" : "이 답변이 도움이 되었나요?"}
      </p>
      <div className="flex gap-3">
        <button
          onClick={() => handleFeedback(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-green-300 text-green-700 hover:bg-green-50 text-sm transition"
        >
          👍 {isZh ? "有帮助" : "도움됨"}
        </button>
        <button
          onClick={() => handleFeedback(false)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm transition"
        >
          👎 {isZh ? "没有帮助" : "도움 안 됨"}
        </button>
      </div>
    </div>
  );
}

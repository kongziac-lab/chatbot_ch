"use client";

import { useState, useRef, useEffect } from "react";
import { sendChat } from "@/lib/api";
import Link from "next/link";

interface Message {
  role:       "user" | "bot";
  text:       string;
  confidence?: string;
}

export default function ChatWidget({ lang }: { lang: string }) {
  const [open,      setOpen]      = useState(false);
  const [messages,  setMessages]  = useState<Message[]>([]);
  const [input,     setInput]     = useState("");
  const [loading,   setLoading]   = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const bottomRef = useRef<HTMLDivElement>(null);
  const isZh = lang === "zh";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    setLoading(true);

    try {
      const res = await sendChat(text, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: res.answer, confidence: res.confidence },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: isZh ? "抱歉，暂时无法回答。" : "죄송합니다. 현재 답변을 생성할 수 없습니다.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  const confidenceColor: Record<string, string> = {
    high:   "bg-green-100 text-green-700",
    medium: "bg-yellow-100 text-yellow-700",
    low:    "bg-red-100 text-red-700",
  };

  return (
    <>
      {/* FAB 버튼 */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-primary text-white shadow-lg
                   flex items-center justify-center text-2xl z-50 hover:bg-primary-light transition"
        aria-label="FAQ 챗봇 열기"
      >
        {open ? "✕" : "💬"}
      </button>

      {/* 챗 패널 */}
      {open && (
        <div className="fixed bottom-24 right-6 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl
                        border z-50 flex flex-col overflow-hidden" style={{ maxHeight: "70vh" }}>
          {/* 헤더 */}
          <div className="bg-primary text-white px-4 py-3 flex items-center gap-2">
            <span className="text-lg">🤖</span>
            <div>
              <p className="font-semibold text-sm">FAQ 챗봇</p>
              <p className="text-xs text-blue-200">{isZh ? "24小时在线" : "24시간 답변 가능"}</p>
            </div>
            <span className="ml-auto text-xs bg-white/20 px-2 py-0.5 rounded-full">
              {isZh ? "中文" : "KO"}
            </span>
          </div>

          {/* 메시지 목록 */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.length === 0 && (
              <p className="text-center text-xs text-gray-400 pt-4">
                {isZh ? "请输入您的问题…" : "질문을 입력하세요…"}
              </p>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] px-3 py-2 rounded-2xl text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-primary text-white rounded-br-none"
                      : "bg-gray-100 text-gray-800 rounded-bl-none"
                  }`}
                >
                  {m.text}
                  {m.confidence && (
                    <span
                      className={`block mt-1 text-xs px-1.5 py-0.5 rounded-full w-fit
                        ${confidenceColor[m.confidence] || "bg-gray-100 text-gray-600"}`}
                    >
                      {m.confidence}
                    </span>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-500 px-3 py-2 rounded-2xl rounded-bl-none text-sm animate-pulse">
                  {isZh ? "正在思考…" : "답변 생성 중…"}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* 입력창 */}
          <div className="border-t px-3 py-2 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder={isZh ? "输入问题…" : "질문 입력…"}
              disabled={loading}
              className="flex-1 text-sm border rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-primary text-white px-3 py-1.5 rounded-lg text-sm disabled:opacity-40 hover:bg-primary-light transition"
            >
              {isZh ? "发送" : "전송"}
            </button>
          </div>
        </div>
      )}
    </>
  );
}

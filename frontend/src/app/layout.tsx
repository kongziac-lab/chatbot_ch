import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FAQ - 외국인 유학생 도우미",
  description: "계명대학교 외국인 유학생을 위한 FAQ 서비스",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen flex flex-col">
        <header className="bg-primary text-white shadow-md">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-3">
            <span className="text-xl font-bold tracking-tight">KMU FAQ</span>
            <span className="text-sm text-blue-200">외국인 유학생 도우미</span>
          </div>
        </header>
        <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-8">
          {children}
        </main>
        <footer className="bg-gray-100 border-t text-center text-xs text-gray-500 py-4">
          © 2025 Keimyung University International Affairs Office
        </footer>
      </body>
    </html>
  );
}

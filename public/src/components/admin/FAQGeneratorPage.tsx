import React, { useState } from 'react';
import { Wand2, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { categories } from '@/data/menuData';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

interface GeneratedFAQ {
  question: string;
  answer: string;
  category?: string;
  language: string;
}

interface GenerateResponse {
  faqs: GeneratedFAQ[];
  source_document?: string;
  generated_at?: string;
}

export const FAQGeneratorPage: React.FC = () => {
  const [topic, setTopic] = useState('');
  const [category, setCategory] = useState('입학/졸업');
  const [subCategory, setSubCategory] = useState('');
  const [numFaqs, setNumFaqs] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState('');

  const selectedCategory = categories.find((c) => c.label.ko === category);
  const subCategories = selectedCategory?.subCategories ?? [];

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/faq/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: topic.trim(),
          num_faqs: numFaqs,
          language: 'ko',
          category: category,
          category_minor: subCategory,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `API 오류: ${response.status}`);
      }

      const data: GenerateResponse = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Form Card */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-kmu-blue/10 rounded-lg">
            <Wand2 className="w-6 h-6 text-kmu-blue" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-800">FAQ 자동 생성</h2>
            <p className="text-sm text-gray-500">
              AI를 활용하여 주제 기반 FAQ를 자동 생성합니다. 생성된 FAQ는 Google Sheets에 저장됩니다.
            </p>
          </div>
        </div>

        <form onSubmit={handleGenerate} className="space-y-4">
          {/* Topic Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              주제 / Topic <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="예: 입학 전형, 수강 신청 방법, 등록금 납부"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kmu-blue focus:border-transparent outline-none transition-all"
              required
            />
          </div>

          {/* Category */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                대분류 카테고리
              </label>
              <select
                value={category}
                onChange={(e) => {
                  setCategory(e.target.value);
                  setSubCategory('');
                }}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kmu-blue focus:border-transparent outline-none"
              >
                {categories.map((c) => (
                  <option key={c.id} value={c.label.ko}>
                    {c.label.ko}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                중분류 카테고리 (선택)
              </label>
              <select
                value={subCategory}
                onChange={(e) => setSubCategory(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kmu-blue focus:border-transparent outline-none"
              >
                <option value="">선택 안 함</option>
                {subCategories.map((sub) => (
                  <option key={sub.id} value={sub.label.ko}>
                    {sub.label.ko}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Count */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              생성 개수 (1~20)
            </label>
            <input
              type="number"
              value={numFaqs}
              onChange={(e) => setNumFaqs(Math.min(20, Math.max(1, Number(e.target.value))))}
              min={1}
              max={20}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kmu-blue focus:border-transparent outline-none"
            />
          </div>

          {/* Generate Button */}
          <button
            type="submit"
            disabled={loading || !topic.trim()}
            className="w-full px-6 py-3 bg-kmu-blue hover:bg-kmu-middleBlue text-white font-semibold rounded-lg transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>생성 중...</span>
              </>
            ) : (
              <>
                <Wand2 className="w-5 h-5" />
                <span>FAQ 생성</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-red-800">오류</p>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Result Card */}
      {result && result.faqs && result.faqs.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center gap-3 mb-6">
            <CheckCircle className="w-6 h-6 text-green-500" />
            <div>
              <h3 className="text-xl font-bold text-gray-800">생성 결과</h3>
              <p className="text-sm text-gray-500">
                {result.faqs.length}개의 FAQ가 생성되었습니다. 모든 FAQ가 Google Sheets에 저장되었습니다.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {result.faqs.map((faq, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-4 hover:border-kmu-blue/30 transition-colors"
              >
                <div className="font-medium text-gray-800 mb-2">
                  Q{index + 1}. {faq.question}
                </div>
                <div className="text-sm text-gray-600 whitespace-pre-wrap">
                  A. {faq.answer}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FAQGeneratorPage;

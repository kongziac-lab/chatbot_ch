import React, { useState, useRef } from 'react';
import { Upload, Loader2, CheckCircle, AlertCircle, FileText } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002';

const DOC_TYPES = [
  { value: '규정', label: '규정' },
  { value: '공지', label: '공지' },
  { value: '안내', label: '안내' },
] as const;

interface UploadResponse {
  document_id: string;
  filename: string;
  doc_type: string;
  total_pages: number;
  num_chunks: number;
  message: string;
}

export const DocumentUploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>('안내');
  const [uploader, setUploader] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    const ext = selected.name.toLowerCase().slice(selected.name.lastIndexOf('.'));
    if (ext !== '.pdf' && ext !== '.docx') {
      setError('PDF 또는 DOCX 파일만 업로드할 수 있습니다.');
      setFile(null);
      return;
    }
    setError('');
    setResult(null);
    setFile(selected);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', docType);
      if (uploader.trim()) formData.append('uploader', uploader.trim());

      const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `API 오류: ${response.status}`);
      }

      setResult(data as UploadResponse);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (!dropped) return;
    const ext = dropped.name.toLowerCase().slice(dropped.name.lastIndexOf('.'));
    if (ext !== '.pdf' && ext !== '.docx') {
      setError('PDF 또는 DOCX 파일만 업로드할 수 있습니다.');
      setFile(null);
      return;
    }
    setError('');
    setResult(null);
    setFile(dropped);
  };

  const handleDragOver = (e: React.DragEvent) => e.preventDefault();

  return (
    <div className="space-y-6">
      {/* Form Card */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-kmu-blue/10 rounded-lg">
            <Upload className="w-6 h-6 text-kmu-blue" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-800">문서 업로드</h2>
            <p className="text-sm text-gray-500">
              PDF 또는 DOCX 문서를 업로드하면 벡터 DB에 인덱싱되고 Source_Documents 시트에 기록됩니다.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              파일 <span className="text-red-500">*</span>
            </label>
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-kmu-blue/50 hover:bg-kmu-blue/5 transition-colors"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                onChange={handleFileChange}
                className="hidden"
              />
              {file ? (
                <div className="flex items-center justify-center gap-2 text-gray-700">
                  <FileText className="w-5 h-5 text-kmu-blue" />
                  <span className="font-medium">{file.name}</span>
                  <span className="text-sm text-gray-500">
                    ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
              ) : (
                <div className="text-gray-500">
                  <Upload className="w-10 h-10 mx-auto mb-2 text-gray-400" />
                  <p>클릭하거나 파일을 드래그하여 업로드</p>
                  <p className="text-xs mt-1">PDF, DOCX 지원</p>
                </div>
              )}
            </div>
          </div>

          {/* Doc Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              문서 유형
            </label>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kmu-blue focus:border-transparent outline-none"
            >
              {DOC_TYPES.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Uploader (optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              업로더 / 부서 (선택)
            </label>
            <input
              type="text"
              value={uploader}
              onChange={(e) => setUploader(e.target.value)}
              placeholder="예: 입학처, 학사팀"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kmu-blue focus:border-transparent outline-none"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !file}
            className="w-full px-6 py-3 bg-kmu-blue hover:bg-kmu-middleBlue text-white font-semibold rounded-lg transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>업로드 중...</span>
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                <span>문서 업로드</span>
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
      {result && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle className="w-6 h-6 text-green-500" />
            <div>
              <h3 className="text-xl font-bold text-gray-800">업로드 완료</h3>
              <p className="text-sm text-gray-500">{result.message}</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">파일명</span>
              <span className="font-medium text-gray-800">{result.filename}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">문서 유형</span>
              <span className="font-medium text-gray-800">{result.doc_type}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">총 페이지</span>
              <span className="font-medium text-gray-800">{result.total_pages}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-500">청크 수</span>
              <span className="font-medium text-gray-800">{result.num_chunks}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentUploadPage;

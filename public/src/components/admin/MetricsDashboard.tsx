import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { RefreshCw, Database, Search, MessageSquare } from 'lucide-react';

const PROD_API_FALLBACK = 'https://chatbot-ch-backend.zeabur.app';
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD ? PROD_API_FALLBACK : 'http://localhost:8000');

interface SyncStats {
  period_hours: number;
  total_syncs: number;
  incremental_syncs: number;
  full_syncs: number;
  success_rate: number;
  avg_duration_ms: number;
}

interface SearchStats {
  period_hours: number;
  total_searches: number;
  success_rate: number;
  avg_duration_ms: number;
  avg_results: number;
}

interface ChatStats {
  period_hours: number;
  total_chats: number;
  success_rate: number;
  avg_duration_ms: number;
}

interface RecentSync {
  timestamp: string;
  displayTime?: string;
  sync_type: string;
  duration_ms: number;
  faq_count: number;
  chunk_count?: number;
  success: boolean;
}

function formatMetricTimestamp(ts?: string): string {
  if (!ts) return '-';
  const hasTimezone = /[zZ]|[+-]\d{2}:\d{2}$/.test(ts);
  const normalized = hasTimezone ? ts : `${ts}Z`;
  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) return ts;
  return parsed.toLocaleString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-800 mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-400 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}

export const MetricsDashboard: React.FC = () => {
  const [syncStats, setSyncStats] = useState<SyncStats | null>(null);
  const [searchStats, setSearchStats] = useState<SearchStats | null>(null);
  const [chatStats, setChatStats] = useState<ChatStats | null>(null);
  const [recentSyncs, setRecentSyncs] = useState<RecentSync[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [hours, setHours] = useState(24);

  const loadMetrics = async () => {
    setLoading(true);
    setError('');
    try {
      const [syncRes, searchRes, chatRes, syncsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/metrics/sync/stats?hours=${hours}`),
        fetch(`${API_BASE_URL}/api/v1/metrics/search/stats?hours=${hours}`),
        fetch(`${API_BASE_URL}/api/v1/metrics/chat/stats?hours=${hours}`),
        fetch(`${API_BASE_URL}/api/v1/metrics/sync/recent?limit=10`),
      ]);

      if (!syncRes.ok || !searchRes.ok || !chatRes.ok || !syncsRes.ok) {
        throw new Error('메트릭 조회 실패');
      }

      const [sync, search, chat, syncs] = await Promise.all([
        syncRes.json(),
        searchRes.json(),
        chatRes.json(),
        syncsRes.json(),
      ]);

      setSyncStats(sync);
      setSearchStats(search);
      setChatStats(chat);
      setRecentSyncs(
        syncs.map((s: any) => ({
          ...s,
          displayTime: formatMetricTimestamp(s.timestamp),
          faq_count: s.faq_count ?? 0,
        }))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : '메트릭을 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetrics();
  }, [hours]);

  if (loading && !syncStats) {
    return (
      <div className="flex items-center justify-center py-20">
        <RefreshCw className="w-8 h-8 text-kmu-blue animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">조회 기간:</label>
          <select
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-kmu-blue outline-none"
          >
            <option value={1}>최근 1시간</option>
            <option value={6}>최근 6시간</option>
            <option value={24}>최근 24시간</option>
            <option value={168}>최근 7일</option>
          </select>
        </div>
        <button
          onClick={loadMetrics}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-kmu-blue hover:bg-kmu-middleBlue text-white rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>새로고침</span>
        </button>
      </div>

      {error && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-amber-800">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="동기화"
          value={syncStats?.total_syncs ?? 0}
          subtitle={`평균 ${((syncStats?.avg_duration_ms ?? 0) / 1000).toFixed(2)}초`}
          icon={Database}
          color="bg-blue-500"
        />
        <StatCard
          title="검색"
          value={searchStats?.total_searches ?? 0}
          subtitle={`평균 ${((searchStats?.avg_duration_ms ?? 0) / 1000).toFixed(2)}초`}
          icon={Search}
          color="bg-emerald-500"
        />
        <StatCard
          title="채팅"
          value={chatStats?.total_chats ?? 0}
          subtitle={`평균 ${((chatStats?.avg_duration_ms ?? 0) / 1000).toFixed(2)}초`}
          icon={MessageSquare}
          color="bg-purple-500"
        />
      </div>

      {/* Charts */}
      {recentSyncs.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">최근 동기화 기록</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={recentSyncs}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="displayTime" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="faq_count" name="FAQ 개수" fill="#1e40af" />
              <Bar dataKey="duration_ms" name="소요시간(ms)" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent Syncs Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <h3 className="text-lg font-bold text-gray-800 p-6 pb-4">최근 동기화 상세</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">시간</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">유형</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">FAQ 개수</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">소요시간</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">상태</th>
              </tr>
            </thead>
            <tbody>
              {recentSyncs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-gray-500">
                    최근 동기화 기록이 없습니다.
                  </td>
                </tr>
              ) : (
                recentSyncs.map((sync, i) => (
                  <tr key={i} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm text-gray-700">{sync.displayTime ?? sync.timestamp}</td>
                    <td className="py-3 px-4 text-sm text-gray-700">
                      {sync.sync_type === 'incremental' ? '증분' : '전체'}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-700">{sync.faq_count}</td>
                    <td className="py-3 px-4 text-sm text-gray-700">
                      {(sync.duration_ms / 1000).toFixed(2)}초
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          sync.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {sync.success ? '완료' : '실패'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default MetricsDashboard;

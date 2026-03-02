import React, { useState } from 'react';
import { Settings, BarChart3, LogOut } from 'lucide-react';
import { MetricsDashboard } from './MetricsDashboard';

interface AdminDashboardProps {
  onBack: () => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onBack }) => {
  const [activeTab, setActiveTab] = useState<'metrics'>('metrics');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-kmu-blue/10 rounded-lg">
              <Settings className="w-6 h-6 text-kmu-blue" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">관리자 페이지</h1>
              <p className="text-xs text-gray-500">Admin Dashboard</p>
            </div>
          </div>
          <button
            onClick={onBack}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-gray-700"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm font-medium">로그아웃</span>
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b sticky top-[73px] z-10">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1">
            <button
              onClick={() => setActiveTab('metrics')}
              className={`px-6 py-4 font-medium border-b-2 transition-all ${
                activeTab === 'metrics'
                  ? 'border-kmu-blue text-kmu-blue bg-kmu-blue/5'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                <span>대시보드</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'metrics' && <MetricsDashboard />}
      </main>

      {/* Footer */}
      <footer className="mt-auto py-6 text-center text-gray-400 text-sm">
        <p>© 2026 Keimyung University Admin Panel</p>
      </footer>
    </div>
  );
};

export default AdminDashboard;

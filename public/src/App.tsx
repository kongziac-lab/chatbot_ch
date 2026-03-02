import { useState } from 'react';
import { LanguageSelector } from './components/LanguageSelector';
import { ChatPage } from './components/ChatPage';
import { AdminLogin } from './components/admin/AdminLogin';
import { AdminDashboard } from './components/admin/AdminDashboard';
import type { Language } from './types';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState<'landing' | 'chat' | 'admin'>('landing');
  const [selectedLanguage, setSelectedLanguage] = useState<Language>('ko');
  const [isAdminAuthenticated, setIsAdminAuthenticated] = useState(false);

  const handleLanguageSelect = (lang: Language) => {
    setSelectedLanguage(lang);
    setCurrentView('chat');
  };

  const handleBackToLanding = () => {
    setCurrentView('landing');
    setIsAdminAuthenticated(false);
  };

  const handleAdminAccess = () => {
    setCurrentView('admin');
  };

  const handleAdminLogin = (password: string): boolean => {
    if (password === 'kmu5806998') {
      setIsAdminAuthenticated(true);
      return true;
    }
    return false;
  };

  return (
    <div className="app-container">
      {currentView === 'landing' ? (
        <LanguageSelector 
          onSelectLanguage={handleLanguageSelect}
          onAdminClick={handleAdminAccess}
        />
      ) : currentView === 'chat' ? (
        <ChatPage language={selectedLanguage} onBack={handleBackToLanding} />
      ) : (
        isAdminAuthenticated ? (
          <AdminDashboard onBack={handleBackToLanding} />
        ) : (
          <AdminLogin onLogin={handleAdminLogin} onBack={handleBackToLanding} />
        )
      )}
    </div>
  );
}

export default App;

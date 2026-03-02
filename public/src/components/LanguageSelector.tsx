import React, { useState } from 'react';
import { Globe, Check } from 'lucide-react';
import { KMULogo } from './KMULogo';
import { translations } from '@/data/menuData';
import type { Language } from '@/types';

interface LanguageSelectorProps {
  onSelectLanguage: (lang: Language) => void;
  onAdminClick: () => void;
}

interface LanguageOption {
  code: Language;
  flag: string;
  label: string;
  subLabel: string;
}

const languageOptions: LanguageOption[] = [
  { code: 'ko', flag: '🇰🇷', label: '한국어', subLabel: 'Korean' },
  { code: 'zh', flag: '🇨🇳', label: '中文', subLabel: 'Chinese' },
];

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({ onSelectLanguage, onAdminClick }) => {
  const [selectedLang, setSelectedLang] = useState<Language>('ko');

  const handleStart = () => {
    onSelectLanguage(selectedLang);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex flex-col items-center justify-center p-6">
      {/* Background Decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-64 h-64 bg-kmu-blue/5 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-10 w-80 h-80 bg-kmu-red/5 rounded-full blur-3xl" />
      </div>

      {/* Main Content */}
      <div className="relative z-10 w-full max-w-md">
        {/* Logo Section */}
        <div className="flex flex-col items-center mb-10">
          <div className="bg-white rounded-3xl shadow-xl p-6 mb-6">
            <KMULogo size={120} />
          </div>
          <h1 className="text-2xl font-bold text-gray-800 text-center mb-2">
            {translations.welcome.ko}
          </h1>
          <p className="text-gray-500 text-center text-sm">
            {translations.subtitle.ko}
          </p>
        </div>

        {/* Language Selection Card */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          {/* Header */}
          <div className="flex items-center gap-2 mb-6">
            <Globe className="w-5 h-5 text-kmu-blue" />
            <span className="text-gray-700 font-medium">
              {translations.selectLanguage.ko}
            </span>
          </div>

          {/* Language Options */}
          <div className="space-y-3 mb-8">
            {languageOptions.map((lang) => (
              <button
                key={lang.code}
                onClick={() => setSelectedLang(lang.code)}
                className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all duration-200 ${
                  selectedLang === lang.code
                    ? 'border-kmu-blue bg-kmu-blue text-white'
                    : 'border-gray-200 hover:border-kmu-blue/50 hover:bg-gray-50'
                }`}
              >
                <span className="text-2xl">{lang.flag}</span>
                <div className="flex-1 text-left">
                  <span className="font-medium text-lg">{lang.label}</span>
                  <span
                    className={`ml-2 text-sm ${
                      selectedLang === lang.code ? 'text-white/80' : 'text-gray-400'
                    }`}
                  >
                    {lang.subLabel}
                  </span>
                </div>
                {selectedLang === lang.code && (
                  <Check className="w-5 h-5" />
                )}
              </button>
            ))}
          </div>

          {/* Start Button */}
          <button
            onClick={handleStart}
            className="w-full bg-kmu-blue hover:bg-kmu-middleBlue text-white font-semibold py-4 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 active:translate-y-0"
          >
            {translations.start.ko}
          </button>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-gray-400 text-xs">
            © 2026 Keimyung University. All rights reserved.{' '}
            <button
              onClick={onAdminClick}
              className="text-gray-500 hover:text-kmu-blue underline ml-1 cursor-pointer transition-colors"
            >
              admin
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LanguageSelector;

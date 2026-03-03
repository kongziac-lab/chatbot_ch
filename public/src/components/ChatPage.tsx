import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  GraduationCap,
  BookOpen,
  FileText,
  Home,
  ChevronLeft,
  Menu,
  MessageSquare,
} from 'lucide-react';
import { ChatBotIcon } from './ChatBotIcon';
import kmuLogo from '@/assets/kmu-logo.png';
import { categories, translations } from '@/data/menuData';
import type { Language, Message, SubCategory, FAQItem } from '@/types';
import { chatApi, faqApi, markdownToHtml } from '@/lib/api';

interface ChatPageProps {
  language: Language;
  onBack: () => void;
}

// Icon mapping
const iconMap: { [key: string]: React.ElementType } = {
  GraduationCap,
  BookOpen,
  FileText,
  Home,
};

const quickMenuBorderColors: Record<string, string> = {
  admission: '#3b82f6', // 입학/졸업
  academic: '#10b981',  // 학사/수업
  visa: '#f59e0b',      // 비자/체류/비교과
  life: '#ef4444',      // 생활/숙박
};

export const ChatPage: React.FC<ChatPageProps> = ({ language, onBack }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const renderBotAvatar = (size: number) => (
      <img
      src={kmuLogo}
      alt="계명대학교 로고"
      width={size}
      height={size}
      style={{ objectFit: 'contain' }}
    />
  );

  const normalizeKeyword = (text: string) =>
    text.toLowerCase().replace(/\s+/g, '').trim();

  const isSingleKeywordInput = (rawInput: string) => {
    const text = rawInput.trim();
    if (!text) return false;

    // 공백이 있으면 문장으로 간주
    if (/\s/.test(text)) return false;
    // 문장부호가 있으면 문장으로 간주
    if (/[.,!?;:()'"“”‘’\-_/\\。！？]/.test(text)) return false;
    // 너무 길면 문장으로 간주
    if (text.length > 12) return false;

    return true;
  };

  const findMatchedCategories = (rawInput: string) => {
    const q = normalizeKeyword(rawInput);
    if (!q) return [];

    return categories.filter((cat) => {
      const majorKo = normalizeKeyword(cat.label.ko);
      const majorZh = normalizeKeyword(cat.label.zh);
      const majorMatched =
        majorKo.includes(q) || q.includes(majorKo) || majorZh.includes(q) || q.includes(majorZh);

      if (majorMatched) return true;

      return cat.subCategories.some((sub) => {
        const subKo = normalizeKeyword(sub.label.ko);
        const subZh = normalizeKeyword(sub.label.zh);
        return subKo.includes(q) || q.includes(subKo) || subZh.includes(q) || q.includes(subZh);
      });
    });
  };

  // Initialize with welcome message
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      type: 'bot',
      content: `${translations.botWelcome[language]}\n\n${translations.instruction1[language]}\n${translations.instruction2[language]}`,
      timestamp: new Date(),
      menuCards: categories,
    };
    setMessages([welcomeMessage]);
  }, [language]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const messageText = inputText;
    setInputText('');

    // 0) 단어 입력일 때만 대/중분류 키워드 매칭으로 메뉴 즉시 노출
    const matchedCategories = findMatchedCategories(messageText);
    if (isSingleKeywordInput(messageText) && matchedCategories.length > 0) {
      setIsTyping(true);
      setTimeout(() => {
        const botResponse: Message = {
          id: (Date.now() + 1).toString(),
          type: 'bot',
          content:
            matchedCategories.length === 1
              ? language === 'ko'
                ? `'${matchedCategories[0].label.ko}' 메뉴를 찾았습니다. 항목을 선택해주세요.`
                : `已找到'${matchedCategories[0].label.zh}'菜单。请选择项目。`
              : language === 'ko'
              ? `관련 메뉴 ${matchedCategories.length}개를 찾았습니다. 선택해주세요.`
              : `找到${matchedCategories.length}个相关菜单。请选择。`,
          timestamp: new Date(),
          menuCards: matchedCategories.length > 1 ? matchedCategories : undefined,
          subMenuCards:
            matchedCategories.length === 1
              ? [
                  {
                    categoryId: matchedCategories[0].id,
                    items: matchedCategories[0].subCategories,
                  },
                ]
              : undefined,
        };
        setMessages((prev) => [...prev, botResponse]);
        setIsTyping(false);
      }, 250);
      return;
    }

    setIsTyping(true);

    try {
      // 실제 FastAPI 호출
      const response = await chatApi.sendMessage(messageText, sessionId);
      
      // 세션 ID 저장
      if (!sessionId) {
        setSessionId(response.session_id);
      }

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: response.answer,
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, botResponse]);
      setIsTyping(false);
      
    } catch (error) {
      console.error('API 호출 오류:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: language === 'ko'
          ? '해당 정보를 찾을 수 없습니다. 담당 부서(장춘대학 계명학원 행정팀 053-580-8743)에 문의하세요.'
          : '找不到相关信息。请联系负责部门（长春大学启明学院行政组 053-580-8743）。',
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, errorMessage]);
      setIsTyping(false);
    }
  };

  const handleCategoryClick = (categoryId: string) => {
    const category = categories.find((c) => c.id === categoryId);
    if (!category) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: category.label[language],
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    setTimeout(() => {
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: translations.selectOption[language],
        timestamp: new Date(),
        subMenuCards: [
          {
            categoryId: category.id,
            items: category.subCategories,
          },
        ],
      };
      setMessages((prev) => [...prev, botResponse]);
      setIsTyping(false);
    }, 500);
  };

  const handleSubCategoryClick = async (subCategory: SubCategory) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: subCategory.label[language],
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    // Render 콜드스타트 대비 안내
    const loadingTimer = setTimeout(() => {
      setMessages((prev) => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg?.type === 'bot' && lastMsg.content.includes('잠시')) return prev;
        const loadingMsg: Message = {
          id: 'loading-hint',
          type: 'bot',
          content: language === 'ko'
            ? '서버를 시작하는 중입니다. 잠시만 기다려주세요...'
            : '服务器正在启动，请稍候...',
          timestamp: new Date(),
        };
        return [...prev, loadingMsg];
      });
    }, 5000);

    try {
      // 중분류에 해당하는 대분류 찾기
      const parentCategory = categories.find((cat) =>
        cat.subCategories.some((sub) => sub.id === subCategory.id)
      );

      if (!parentCategory) {
        throw new Error('카테고리를 찾을 수 없습니다');
      }

      // 디버깅 로그 추가
      console.log('=== FAQ 조회 시작 ===');
      console.log('대분류(한국어):', parentCategory.label.ko);
      console.log('중분류(한국어):', subCategory.label.ko);
      console.log('표시 언어:', language);

      // API로 FAQ 목록 가져오기
      // 카테고리는 항상 한국어로 전송 (Google Sheets의 실제 카테고리는 한국어)
      const faqs = await faqApi.getFAQsByCategory(
        parentCategory.label.ko,
        subCategory.label.ko,
        language
      );

      console.log('조회된 FAQ 개수:', faqs.length);
      console.log('FAQ 목록:', faqs);
      console.log('=== FAQ 조회 완료 ===');

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content:
          faqs.length > 0
            ? language === 'ko'
              ? `'${subCategory.label.ko}'에 대한 ${faqs.length}개의 FAQ가 있습니다. 질문을 선택해주세요.`
              : `关于'${subCategory.label.zh}'有${faqs.length}个FAQ。请选择问题。`
            : language === 'ko'
            ? '해당 정보를 찾을 수 없습니다. 담당 부서(장춘대학 계명학원 행정팀 053-580-8743)에 문의하세요.'
            : '找不到相关信息。请联系负责部门（长春大学启明学院行政组 053-580-8743）。',
        timestamp: new Date(),
        faqCards: faqs.length > 0 ? faqs : undefined,
      };

      clearTimeout(loadingTimer);
      // 로딩 안내 메시지 제거
      setMessages((prev) => prev.filter((m) => m.id !== 'loading-hint'));
      setMessages((prev) => [...prev, botResponse]);
      setIsTyping(false);
    } catch (error) {
      clearTimeout(loadingTimer);
      setMessages((prev) => prev.filter((m) => m.id !== 'loading-hint'));

      console.error('=== FAQ 조회 오류 ===');
      console.error('에러 상세:', error);
      console.error('에러 메시지:', error instanceof Error ? error.message : String(error));

      const isTimeout = error instanceof Error && error.name === 'AbortError';
      const isNetwork = error instanceof TypeError;

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: isTimeout || isNetwork
          ? language === 'ko'
            ? '서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.'
            : '服务器连接失败，请稍后再试。'
          : language === 'ko'
            ? '해당 정보를 찾을 수 없습니다. 담당 부서(장춘대학 계명학원 행정팀 053-580-8743)에 문의하세요.'
            : '找不到相关信息。请联系负责部门（长春大学启明学院行政组 053-580-8743）。',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      setIsTyping(false);
    }
  };

  const handleFAQClick = (faq: FAQItem) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: faq.question,
      timestamp: new Date(),
    };

    const botResponse: Message = {
      id: (Date.now() + 1).toString(),
      type: 'bot',
      content: faq.answer,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage, botResponse]);
  };

  const handleBackToMain = () => {
    const botMessage: Message = {
      id: Date.now().toString(),
      type: 'bot',
      content: translations.selectOption[language],
      timestamp: new Date(),
      menuCards: categories,
    };
    setMessages((prev) => [...prev, botMessage]);
  };

  const renderCategoryCard = (category: typeof categories[0], index: number) => {
    const Icon = iconMap[category.icon] || MessageSquare;

    return (
      <div
        key={category.id}
        className="category-card bg-white rounded-xl overflow-hidden shadow-md border border-gray-100 cursor-pointer"
        style={{ animationDelay: `${index * 0.1}s` }}
        onClick={() => handleCategoryClick(category.id)}
      >
        {/* Card Header with Gradient */}
        <div className={`bg-gradient-to-r ${category.color} p-4 text-white`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium opacity-90">
              {translations.botTitle[language]}
            </span>
            <Icon className="w-6 h-6 opacity-80" />
          </div>
          <h3 className="text-lg font-bold mt-2">{category.label[language]}</h3>
        </div>

        {/* Card Body with Subcategories */}
        <div className="p-3 space-y-2">
          {category.subCategories.slice(0, 3).map((sub) => (
            <div
              key={sub.id}
              className="menu-btn px-3 py-2 rounded-lg text-sm text-gray-700 bg-gray-50 text-center"
            >
              {sub.label[language]}
            </div>
          ))}
          {category.subCategories.length > 3 && (
            <div className="text-xs text-gray-400 text-center py-1">
              +{category.subCategories.length - 3}{' '}
              {language === 'ko' ? '더보기' : '更多'}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderSubMenuCard = (categoryId: string, items: SubCategory[]) => {
    const category = categories.find((c) => c.id === categoryId);
    if (!category) return null;

    const Icon = iconMap[category.icon] || MessageSquare;

    return (
      <div className="bg-white rounded-xl overflow-hidden shadow-md border border-gray-100 mb-4">
        {/* Card Header */}
        <div className={`bg-gradient-to-r ${category.color} p-4 text-white`}>
          <div className="flex items-center gap-2">
            <Icon className="w-5 h-5" />
            <span className="font-bold">{category.label[language]}</span>
          </div>
        </div>

        {/* Subcategory Items */}
        <div className="p-3 grid grid-cols-2 gap-2">
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => handleSubCategoryClick(item)}
              className="menu-btn px-3 py-3 rounded-lg text-sm text-gray-700 bg-gray-50 text-center font-medium"
            >
              {item.label[language]}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <ChevronLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div className="flex items-center gap-2">
              {renderBotAvatar(35)}
              <div>
                <h1 className="font-bold text-gray-800">
                  {translations.botTitle[language]}
                </h1>
                <p className="text-xs text-gray-500">
                  {language === 'ko' ? '온라인' : '在线'}
                </p>
              </div>
            </div>
          </div>
          <button className="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <Menu className="w-5 h-5 text-gray-600" />
          </button>
        </div>
      </header>

      {/* Chat Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
          {messages.map((message, index) => (
            <div
              key={message.id}
              className={`message-enter flex ${
                message.type === 'user' ? 'justify-end' : 'justify-start'
              }`}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              {message.type === 'bot' && (
                <div className="mr-2 flex-shrink-0">
                  {renderBotAvatar(25)}
                </div>
              )}

              <div
                className={`max-w-[80%] ${
                  message.type === 'user'
                    ? 'bg-kmu-blue text-white rounded-2xl rounded-tr-sm'
                    : 'bg-white border border-gray-200 rounded-2xl rounded-tl-sm'
                } px-4 py-3 shadow-sm`}
              >
                {message.type === 'bot' && (
                  <p className="text-xs text-kmu-blue font-medium mb-1">
                    {translations.botTitle[language]}
                  </p>
                )}
                {/* 메시지 내용 (마크다운 → HTML 렌더링) */}
                <div
                  className={`text-sm ${
                    message.type === 'user' ? 'text-white' : 'text-gray-700'
                  }`}
                  dangerouslySetInnerHTML={{
                    __html: markdownToHtml(message.content, language),
                  }}
                />

                {/* Category Cards */}
                {message.menuCards && (
                  <div className="mt-4 grid grid-cols-2 gap-3">
                    {message.menuCards.map((card, idx) =>
                      renderCategoryCard(card, idx)
                    )}
                  </div>
                )}

                {/* Sub Menu Cards */}
                {message.subMenuCards && (
                  <div className="mt-4">
                    {message.subMenuCards.map((card) =>
                      renderSubMenuCard(card.categoryId, card.items)
                    )}
                    <button
                      onClick={handleBackToMain}
                      className="flex items-center gap-2 text-sm text-kmu-blue hover:text-kmu-middleBlue transition-colors mt-2"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      {translations.mainMenu[language]}
                    </button>
                  </div>
                )}

                {/* FAQ Cards */}
                {message.faqCards && message.faqCards.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {message.faqCards.map((faq) => (
                      <button
                        key={faq.faq_id}
                        onClick={() => handleFAQClick(faq)}
                        className="w-full text-left p-4 bg-gray-50 hover:bg-blue-50 
                                 rounded-lg border border-gray-200 hover:border-blue-400 
                                 hover:shadow-md transition-all group"
                      >
                        <div className="flex items-start gap-3">
                          <MessageSquare className="w-5 h-5 text-gray-400 group-hover:text-blue-500 mt-0.5 flex-shrink-0 transition-colors" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                              {faq.question}
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <span className="text-xs text-gray-500">
                                {language === 'ko' ? '답변 보기' : '查看答案'}
                              </span>
                              {faq.view_count > 0 && (
                                <span className="text-xs text-gray-400">
                                  · {language === 'ko' ? '조회' : '查看'} {faq.view_count}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                <p
                  className={`text-xs mt-2 ${
                    message.type === 'user'
                      ? 'text-white/70'
                      : 'text-gray-400'
                  }`}
                >
                  {message.timestamp.toLocaleTimeString(language === 'ko' ? 'ko-KR' : 'zh-CN', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>

              {message.type === 'user' && (
                <div className="w-10 h-10 rounded-full overflow-hidden bg-transparent flex items-center justify-center ml-2 flex-shrink-0">
                  <ChatBotIcon size={30} />
                </div>
              )}
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="mr-2">
                <ChatBotIcon size={25} />
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                <div className="flex gap-1">
                  <span className="typing-dot w-2 h-2 bg-kmu-blue rounded-full" />
                  <span className="typing-dot w-2 h-2 bg-kmu-blue rounded-full" />
                  <span className="typing-dot w-2 h-2 bg-kmu-blue rounded-full" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Quick Menu Buttons */}
      <div className="bg-white border-t border-gray-200 px-4 py-2">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
            <button
              onClick={handleBackToMain}
              className="flex-shrink-0 px-4 py-2 bg-gray-100 hover:bg-kmu-blue hover:text-white rounded-full text-sm text-gray-700 transition-colors"
            >
              {translations.mainMenu[language]}
            </button>
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => handleCategoryClick(cat.id)}
                className="flex-shrink-0 px-4 py-2 bg-gray-100 hover:bg-kmu-blue hover:text-white rounded-full text-sm text-gray-700 transition-colors border"
                style={{ borderColor: quickMenuBorderColors[cat.id] ?? '#d1d5db' }}
              >
                {cat.label[language]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Input Area */}
      <footer className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder={translations.placeholder[language]}
              className="chat-input w-full px-4 py-3 bg-gray-100 rounded-full text-sm text-gray-700 placeholder-gray-400 outline-none transition-all"
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputText.trim()}
            className={`p-3 rounded-full transition-all ${
              inputText.trim()
                ? 'bg-kmu-blue text-white hover:bg-kmu-middleBlue'
                : 'bg-gray-200 text-gray-400'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </footer>
    </div>
  );
};

export default ChatPage;

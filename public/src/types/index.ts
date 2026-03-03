export type Language = 'ko' | 'zh';

export interface SubCategory {
  id: string;
  label: {
    ko: string;
    zh: string;
  };
}

export interface Category {
  id: string;
  label: {
    ko: string;
    zh: string;
  };
  color: string;
  icon: string;
  subCategories: SubCategory[];
}

export interface FAQItem {
  faq_id: string;
  category_major: string;
  category_minor: string;
  question: string;
  answer: string;
  source: string;
  scope: string;
  priority: number;
  view_count: number;
  helpful_pct: number | null;
  language: Language;
}

export interface Message {
  id: string;
  type: 'bot' | 'user';
  content: string;
  timestamp: Date;
  sourceRefs?: {
    faq_id: string;
    question: string;
  }[];
  menuCards?: Category[];
  subMenuCards?: {
    categoryId: string;
    items: SubCategory[];
  }[];
  faqCards?: FAQItem[];
}

export interface ChatState {
  messages: Message[];
  selectedLanguage: Language;
  currentView: 'landing' | 'chat';
  selectedCategory: string | null;
}

export interface Translations {
  [key: string]: {
    ko: string;
    zh: string;
  };
}

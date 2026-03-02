import React from 'react';
import chatbotIcon from '@/assets/chatbot-icon.png';

interface ChatBotIconProps {
  size?: number;
  className?: string;
}

export const ChatBotIcon: React.FC<ChatBotIconProps> = ({ size = 50, className = '' }) => {
  return (
    <img
      src={chatbotIcon}
      alt="계명대학교 AI 챗봇"
      width={size}
      height={size}
      className={`chatbot-icon ${className}`}
      style={{ 
        objectFit: 'contain',
        backgroundColor: 'transparent'
      }}
    />
  );
};

export default ChatBotIcon;

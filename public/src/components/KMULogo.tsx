import React from 'react';
import logoImage from '@/assets/kmu-full-emblem.png';

interface KMULogoProps {
  size?: number;
  className?: string;
}

export const KMULogo: React.FC<KMULogoProps> = ({ size = 120, className = '' }) => {
  return (
    <img
      src={logoImage}
      alt="계명대학교 로고"
      width={size}
      height={size}
      className={`kmu-logo ${className}`}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default KMULogo;

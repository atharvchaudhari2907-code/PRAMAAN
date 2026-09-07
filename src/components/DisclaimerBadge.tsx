import React from 'react';

interface DisclaimerBadgeProps {
  variant?: 'subtle' | 'banner';
}

export const DisclaimerBadge: React.FC<DisclaimerBadgeProps> = ({ variant = 'subtle' }) => {
  if (variant === 'banner') {
    return null;
  }

  return null;
};

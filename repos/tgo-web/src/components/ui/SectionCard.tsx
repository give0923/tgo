import React from 'react';

type Variant = 'blue' | 'purple' | 'green' | 'orange' | 'teal' | 'gray';

const variantClasses: Record<Variant, string> = {
  blue: 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-100',
  purple: 'bg-gradient-to-r from-purple-50 to-pink-50 border-purple-100',
  green: 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-100',
  orange: 'bg-gradient-to-r from-orange-50 to-amber-50 border-orange-100',
  teal: 'bg-gradient-to-r from-teal-50 to-cyan-50 border-teal-100',
  gray: 'bg-white border-gray-200',
};

interface SectionCardProps {
  variant?: Variant;
  className?: string;
  children: React.ReactNode;
}

/**
 * Reusable section container for modals and pages
 */
const SectionCard: React.FC<SectionCardProps> = ({ variant = 'gray', className = '', children }) => {
  const classes = variantClasses[variant];
  return (
    <div className={`rounded-lg p-6 border ${classes} ${className}`}>
      {children}
    </div>
  );
};

export default SectionCard;


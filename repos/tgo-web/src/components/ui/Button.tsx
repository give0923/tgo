import React from 'react';
import Icon from './Icon';
import type { ButtonProps } from '@/types';

/**
 * Button component with various styles and sizes
 */
const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  icon,
  disabled = false,
  className = '',
  onClick,
  type = 'button',
  title,
  ...props 
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1';
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs rounded-md',
    md: 'px-3 py-1.5 text-sm rounded-md',
    lg: 'px-4 py-2 text-base rounded-lg'
  };

  const iconSizeClasses = {
    sm: 'p-1 rounded-md',
    md: 'p-1.5 rounded-md',
    lg: 'p-2 rounded-lg'
  };

  const variantClasses = {
    primary: 'bg-blue-500 text-white hover:bg-blue-600 focus:ring-blue-500',
    secondary: 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200 focus:ring-gray-500',
    ghost: 'text-gray-500 hover:bg-gray-200/50 hover:text-gray-700 focus:ring-gray-500',
    danger: 'bg-red-500 text-white hover:bg-red-600 focus:ring-red-500',
    icon: 'text-gray-500 hover:bg-gray-200/50 hover:text-gray-700 focus:ring-gray-500'
  };

  const disabledClasses = 'opacity-50 cursor-not-allowed';

  const isIconOnly = variant === 'icon' || (!children && icon);
  const sizeClass = isIconOnly ? iconSizeClasses[size] : sizeClasses[size];

  return (
    <button
      type={type}
      title={title}
      className={`
        ${baseClasses}
        ${sizeClass}
        ${variantClasses[variant]}
        ${disabled ? disabledClasses : ''}
        ${className}
      `}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {icon && (
        <Icon 
          name={icon} 
          size={size === 'sm' ? 16 : size === 'lg' ? 20 : 18}
          className={children ? 'mr-1.5' : ''}
        />
      )}
      {children}
    </button>
  );
};

export default Button;

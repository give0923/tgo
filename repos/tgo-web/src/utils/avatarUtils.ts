// Shared avatar generation utilities for the TGO Web application

// Color mapping for default avatars (similar to Telegram's system)
export const AVATAR_COLORS = [
  'bg-gradient-to-br from-red-500 to-red-600',      // A
  'bg-gradient-to-br from-orange-500 to-orange-600', // B
  'bg-gradient-to-br from-amber-500 to-amber-600',   // C
  'bg-gradient-to-br from-yellow-500 to-yellow-600', // D
  'bg-gradient-to-br from-lime-500 to-lime-600',     // E
  'bg-gradient-to-br from-green-500 to-green-600',   // F
  'bg-gradient-to-br from-emerald-500 to-emerald-600', // G
  'bg-gradient-to-br from-teal-500 to-teal-600',     // H
  'bg-gradient-to-br from-cyan-500 to-cyan-600',     // I
  'bg-gradient-to-br from-sky-500 to-sky-600',       // J
  'bg-gradient-to-br from-blue-500 to-blue-600',     // K
  'bg-gradient-to-br from-indigo-500 to-indigo-600', // L
  'bg-gradient-to-br from-violet-500 to-violet-600', // M
  'bg-gradient-to-br from-purple-500 to-purple-600', // N
  'bg-gradient-to-br from-fuchsia-500 to-fuchsia-600', // O
  'bg-gradient-to-br from-pink-500 to-pink-600',     // P
  'bg-gradient-to-br from-rose-500 to-rose-600',     // Q
  'bg-gradient-to-br from-slate-500 to-slate-600',   // R
  'bg-gradient-to-br from-gray-500 to-gray-600',     // S
  'bg-gradient-to-br from-zinc-500 to-zinc-600',     // T
  'bg-gradient-to-br from-neutral-500 to-neutral-600', // U
  'bg-gradient-to-br from-stone-500 to-stone-600',   // V
  'bg-gradient-to-br from-red-400 to-red-500',       // W
  'bg-gradient-to-br from-orange-400 to-orange-500', // X
  'bg-gradient-to-br from-amber-400 to-amber-500',   // Y
  'bg-gradient-to-br from-yellow-400 to-yellow-500', // Z
];

export interface DefaultAvatar {
  letter: string;
  colorClass: string;
}

/**
 * Generate default avatar for entities without profile pictures
 * @param name - The name to generate avatar from
 * @returns Object containing the letter and color class
 */
export const generateDefaultAvatar = (name: string): DefaultAvatar => {
  if (!name || name.trim() === '') {
    return {
      letter: '?',
      colorClass: 'bg-gradient-to-br from-gray-400 to-gray-500'
    };
  }

  const firstChar = name.trim().charAt(0).toUpperCase();
  
  // Convert character to index (A=0, B=1, etc.)
  const charCode = firstChar.charCodeAt(0);
  let colorIndex = 0;
  
  if (charCode >= 65 && charCode <= 90) { // A-Z
    colorIndex = charCode - 65;
  } else if (charCode >= 48 && charCode <= 57) { // 0-9
    colorIndex = (charCode - 48) % AVATAR_COLORS.length;
  } else {
    // For non-ASCII characters (like Chinese), use a hash-like approach
    colorIndex = charCode % AVATAR_COLORS.length;
  }
  
  return {
    letter: firstChar,
    colorClass: AVATAR_COLORS[colorIndex] || AVATAR_COLORS[0]
  };
};

/**
 * Check if an avatar URL is valid and should be displayed
 * @param avatarUrl - The avatar URL to validate
 * @returns Boolean indicating if the avatar is valid
 */
export const hasValidAvatar = (avatarUrl?: string): boolean => {
  return !!(
    avatarUrl && 
    avatarUrl.trim() !== '' && 
    !avatarUrl.includes('placeholder') &&
    !avatarUrl.includes('default')
  );
};

/**
 * Avatar component props for consistent avatar rendering
 */
export interface AvatarProps {
  name: string;
  avatarUrl?: string;
  size?: 'sm' | 'md' | 'lg';
  shape?: 'rounded' | 'circle';
  className?: string;
  onError?: () => void;
}

/**
 * Get size classes for avatars
 * @param size - The size variant
 * @returns CSS classes for the specified size
 */
export const getAvatarSizeClasses = (size: 'sm' | 'md' | 'lg' = 'md'): string => {
  switch (size) {
    case 'sm':
      return 'w-8 h-8 text-xs';
    case 'md':
      return 'w-10 h-10 text-sm';
    case 'lg':
      return 'w-12 h-12 text-base';
    default:
      return 'w-10 h-10 text-sm';
  }
};

/**
 * Get shape classes for avatars
 * @param shape - The shape variant
 * @returns CSS classes for the specified shape
 */
export const getAvatarShapeClasses = (shape: 'rounded' | 'circle' = 'rounded'): string => {
  switch (shape) {
    case 'circle':
      return 'rounded-full';
    case 'rounded':
      return 'rounded-md';
    default:
      return 'rounded-md';
  }
};

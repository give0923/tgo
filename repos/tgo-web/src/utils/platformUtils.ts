import { PlatformType } from '@/types';
import type { ComponentType } from 'react';
// react-icons brand/generic icons
import { IoLogoWechat } from 'react-icons/io5';
import { AiOutlineWechatWork } from 'react-icons/ai';
import { TbWorld, TbMessageCircle, TbUsers } from 'react-icons/tb';
import { MdEmail, MdSms } from 'react-icons/md';
import { FaTelegramPlane, FaWhatsapp, FaDiscord, FaSlack, FaFacebook, FaInstagram, FaLinkedin, FaPhone, FaTwitter } from 'react-icons/fa';
import { FiShare2 } from 'react-icons/fi';
import { SiTiktok } from 'react-icons/si';

/** React icon component type with common props */
export type IconComponent = ComponentType<{ size?: number | string; className?: string }>;

/**
 * Coerce a raw string to a PlatformType enum (fallback to WEBSITE)
 */
export function toPlatformType(input: string | null | undefined): PlatformType {
  const v = String(input || '').toLowerCase();
  switch (v) {
    case PlatformType.WEBSITE: return PlatformType.WEBSITE;
    case PlatformType.WECHAT: return PlatformType.WECHAT;
    case PlatformType.WHATSAPP: return PlatformType.WHATSAPP;
    case PlatformType.TELEGRAM: return PlatformType.TELEGRAM;
    case PlatformType.EMAIL: return PlatformType.EMAIL;
    case PlatformType.SMS: return PlatformType.SMS;
    case PlatformType.FACEBOOK: return PlatformType.FACEBOOK;
    case PlatformType.INSTAGRAM: return PlatformType.INSTAGRAM;
    case PlatformType.TWITTER: return PlatformType.TWITTER;
    case PlatformType.LINKEDIN: return PlatformType.LINKEDIN;
    case PlatformType.DISCORD: return PlatformType.DISCORD;
    case PlatformType.SLACK: return PlatformType.SLACK;
    case PlatformType.TEAMS: return PlatformType.TEAMS;
    case PlatformType.WEBCHAT: return PlatformType.WEBCHAT;
    case PlatformType.PHONE: return PlatformType.PHONE;
    case PlatformType.DOUYIN: return PlatformType.DOUYIN;
    case PlatformType.TIKTOK: return PlatformType.TIKTOK;
    case PlatformType.CUSTOM: return PlatformType.CUSTOM;
    case PlatformType.WECOM: return PlatformType.WECOM;
    default: return PlatformType.WEBSITE;
  }
}

/**
 * Map platform type to a react-icons component
 */
export function getPlatformIconComponent(platformType: PlatformType): IconComponent {
  switch (platformType) {
    case PlatformType.WECHAT: return IoLogoWechat;
    case PlatformType.WECOM: return AiOutlineWechatWork;
    case PlatformType.WEBSITE: return TbWorld;
    case PlatformType.EMAIL: return MdEmail;
    case PlatformType.TELEGRAM: return FaTelegramPlane;
    case PlatformType.WHATSAPP: return FaWhatsapp;
    case PlatformType.DOUYIN: return SiTiktok; // fallback brand icon
    case PlatformType.TIKTOK: return SiTiktok;
    case PlatformType.CUSTOM: return FiShare2;
    case PlatformType.DISCORD: return FaDiscord;
    case PlatformType.SLACK: return FaSlack;
    case PlatformType.FACEBOOK: return FaFacebook;
    case PlatformType.INSTAGRAM: return FaInstagram;
    case PlatformType.TWITTER: return FaTwitter;
    case PlatformType.LINKEDIN: return FaLinkedin;
    case PlatformType.TEAMS: return TbUsers;
    case PlatformType.WEBCHAT: return TbMessageCircle;
    case PlatformType.SMS: return MdSms;
    case PlatformType.PHONE: return FaPhone;
    default: return TbWorld;
  }
}

/**
 * Map platform type to a Lucide icon name (string)
 * Note: Lucide does not include brand icons; using generic icons for brands.
 */
export function getPlatformIcon(platformType: PlatformType): string {
  switch (platformType) {
    case PlatformType.WEBSITE: return 'Globe';
    case PlatformType.WECHAT: return 'MessageSquare';
    case PlatformType.WHATSAPP: return 'MessageCircle';
    case PlatformType.TELEGRAM: return 'Send';
    case PlatformType.EMAIL: return 'Mail';
    case PlatformType.SMS: return 'MessageSquare';
    case PlatformType.FACEBOOK: return 'MessageSquare';
    case PlatformType.INSTAGRAM: return 'Camera';
    case PlatformType.TWITTER: return 'Bird';
    case PlatformType.LINKEDIN: return 'Briefcase';
    case PlatformType.DISCORD: return 'MessageSquare';
    case PlatformType.SLACK: return 'Hash';
    case PlatformType.TEAMS: return 'Users';
    case PlatformType.WEBCHAT: return 'MessageSquare';
    case PlatformType.PHONE: return 'Phone';
    case PlatformType.DOUYIN: return 'Music';
    case PlatformType.TIKTOK: return 'Music';
    case PlatformType.CUSTOM: return 'Share2';
    case PlatformType.WECOM: return 'MessageSquare';
    default: return 'Globe';
  }
}

/**
 * Map platform type to a Tailwind text color class
 * Ensures visually distinct, brand-appropriate colors
 */
export function getPlatformColor(platformType: PlatformType): string {
  switch (platformType) {
    case PlatformType.WECHAT: return 'text-green-600';
    case PlatformType.WHATSAPP: return 'text-green-500';
    case PlatformType.TELEGRAM: return 'text-sky-500';
    case PlatformType.EMAIL: return 'text-blue-600';
    case PlatformType.SMS: return 'text-emerald-500';
    case PlatformType.FACEBOOK: return 'text-blue-700';
    case PlatformType.INSTAGRAM: return 'text-pink-500';
    case PlatformType.TWITTER: return 'text-cyan-500';
    case PlatformType.LINKEDIN: return 'text-blue-700';
    case PlatformType.DISCORD: return 'text-indigo-500';
    case PlatformType.SLACK: return 'text-purple-500';
    case PlatformType.TEAMS: return 'text-violet-600';
    case PlatformType.WEBCHAT: return 'text-teal-500';
    case PlatformType.PHONE: return 'text-lime-600';
    case PlatformType.DOUYIN: return 'text-rose-500';
    case PlatformType.TIKTOK: return 'text-fuchsia-500';
    case PlatformType.CUSTOM: return 'text-orange-500';
    case PlatformType.WECOM: return 'text-blue-500';
    case PlatformType.WEBSITE:
    default:
      return 'text-blue-500';
  }
}


/**
 * Map platform type to a human-readable Chinese label
 */
export function getPlatformLabel(platformType: PlatformType): string {
  switch (platformType) {
    case PlatformType.WEBSITE: return '官网客服';
    case PlatformType.WECHAT: return '微信公众号';
    case PlatformType.WHATSAPP: return 'WhatsApp';
    case PlatformType.TELEGRAM: return 'Telegram';
    case PlatformType.EMAIL: return '邮件';
    case PlatformType.SMS: return '短信';
    case PlatformType.FACEBOOK: return 'Facebook';
    case PlatformType.INSTAGRAM: return 'Instagram';
    case PlatformType.TWITTER: return 'Twitter';
    case PlatformType.LINKEDIN: return '领英';
    case PlatformType.DISCORD: return 'Discord';
    case PlatformType.SLACK: return 'Slack';
    case PlatformType.TEAMS: return 'Microsoft Teams';
    case PlatformType.WEBCHAT: return '网页聊天';
    case PlatformType.PHONE: return '电话';
    case PlatformType.DOUYIN: return '抖音';
    case PlatformType.TIKTOK: return 'TikTok';
    case PlatformType.CUSTOM: return '自定义平台';
    case PlatformType.WECOM: return '企业微信';
    default: return '未知平台';
  }
}


/**
 * Navigation Configuration
 * Centralized navigation items for the sidebar
 */

import {
  LayoutDashboard,
  Upload,
  FileText,
  Calendar,
  BarChart3,
  MessageCircle,
  Clock,
  FileEdit,
  HelpCircle,
  Settings,
  Users,
  Package,
  Image as ImageIcon,
  Zap,
  Shield,
  MessageSquareHeart,
} from 'lucide-react';
import { NavItem } from './types';

/**
 * Main navigation items
 * These appear in the primary section of the sidebar
 */
export const mainNavItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'Upload', path: '/upload', icon: Upload },
  { label: 'Drafts', path: '/drafts', icon: FileText, badge: 12 },
  { label: 'Publish', path: '/publish', icon: Calendar },
  { label: 'Analytics', path: '/analytics', icon: BarChart3 },
  { label: 'Automation', path: '/automation', icon: Zap },
  { label: 'Messages', path: '/messages', icon: MessageCircle, badge: 3, badgeVariant: 'error' },
  { label: 'Orders', path: '/orders', icon: Package },
  { label: 'Image Editor', path: '/image-editor', icon: ImageIcon },
  { label: 'History', path: '/history', icon: Clock },
  { label: 'Templates', path: '/templates', icon: FileEdit },
];

/**
 * Secondary navigation items
 * These appear in the bottom section of the sidebar
 */
export const secondaryNavItems: NavItem[] = [
  { label: 'Comptes Vinted', path: '/accounts', icon: Users },
  { label: 'Feedback', path: '/feedback', icon: MessageSquareHeart },
  { label: 'Settings', path: '/settings', icon: Settings },
  { label: 'Help', path: '/help', icon: HelpCircle },
];

/**
 * Admin navigation item
 * Only visible to super admins
 */
export const adminNavItem: NavItem = {
  label: 'Admin Panel',
  path: '/admin',
  icon: Shield,
};

/**
 * Super admin email
 * Used to check if user has admin access
 */
export const SUPER_ADMIN_EMAIL = 'ronanchenlopes@gmail.com';

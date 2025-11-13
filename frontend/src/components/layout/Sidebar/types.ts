/**
 * Sidebar Types
 * Shared TypeScript interfaces for the Sidebar component
 */

import { LucideIcon } from 'lucide-react';

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon;
  badge?: string | number;
  badgeVariant?: 'default' | 'primary' | 'success' | 'warning' | 'error';
}

export interface SidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export interface MobileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

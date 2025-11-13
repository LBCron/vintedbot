import { useState, useEffect, useCallback } from 'react';

/**
 * Hook to manage Command Palette state and keyboard shortcuts
 */
export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen(prev => !prev), []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Command/Ctrl + K to open command palette
      if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        toggle();
      }

      // ESC to close (handled by Dialog component but also here as fallback)
      if (event.key === 'Escape' && isOpen) {
        close();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, toggle, close]);

  return {
    isOpen,
    open,
    close,
    toggle,
  };
}

/**
 * Hook to register additional keyboard shortcuts
 */
export function useKeyboardShortcuts(shortcuts: Record<string, (event: KeyboardEvent) => void>) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Build the key combination string (e.g., "ctrl+s", "cmd+shift+p")
      const keys = [];
      if (event.ctrlKey) keys.push('ctrl');
      if (event.metaKey) keys.push('cmd');
      if (event.shiftKey) keys.push('shift');
      if (event.altKey) keys.push('alt');
      keys.push(event.key.toLowerCase());

      const combination = keys.join('+');

      // Check if this combination has a handler
      const handler = shortcuts[combination];
      if (handler) {
        event.preventDefault();
        handler(event);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}

/**
 * Common keyboard shortcuts for the app
 */
export const APP_SHORTCUTS = {
  // Navigation
  'cmd+k': 'Open command palette',
  'ctrl+k': 'Open command palette',
  'cmd+/': 'Toggle sidebar',
  'ctrl+/': 'Toggle sidebar',

  // Actions
  'cmd+s': 'Save',
  'ctrl+s': 'Save',
  'cmd+enter': 'Submit/Publish',
  'ctrl+enter': 'Submit/Publish',
  'cmd+shift+p': 'Publish draft',
  'ctrl+shift+p': 'Publish draft',

  // Navigation shortcuts
  'g+d': 'Go to Dashboard',
  'g+u': 'Go to Upload',
  'g+r': 'Go to Drafts',
  'g+m': 'Go to Messages',
  'g+a': 'Go to Analytics',
  'g+s': 'Go to Settings',

  // UI
  'esc': 'Close dialog/drawer',
  '?': 'Show keyboard shortcuts help',
};

/**
 * Hook to show keyboard shortcuts help
 */
export function useShowShortcutsHelp() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === '?' && !event.metaKey && !event.ctrlKey) {
        // Check if we're not in an input field
        const target = event.target as HTMLElement;
        if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
          event.preventDefault();
          setIsOpen(true);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return {
    isOpen,
    close: () => setIsOpen(false),
  };
}

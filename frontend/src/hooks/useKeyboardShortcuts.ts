import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';

/**
 * Global keyboard shortcuts for VintedBot
 *
 * Shortcuts:
 * - ⌘/Ctrl + H: Dashboard
 * - ⌘/Ctrl + U: Upload
 * - ⌘/Ctrl + D: Drafts
 * - ⌘/Ctrl + P: Publish
 * - ⌘/Ctrl + M: Messages
 * - ⌘/Ctrl + A: Analytics
 * - ⌘/Ctrl + ,: Settings
 * - ?: Show shortcuts help
 */
export function useKeyboardShortcuts() {
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      const isMod = e.metaKey || e.ctrlKey;

      // Ignore if typing in input/textarea
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // Navigation shortcuts (with Cmd/Ctrl)
      if (isMod && !e.shiftKey && !e.altKey) {
        switch (e.key.toLowerCase()) {
          case 'h':
            e.preventDefault();
            navigate('/');
            toast.success('⌘H - Dashboard', { duration: 1500 });
            break;

          case 'u':
            e.preventDefault();
            navigate('/upload');
            toast.success('⌘U - Upload', { duration: 1500 });
            break;

          case 'd':
            e.preventDefault();
            navigate('/drafts');
            toast.success('⌘D - Drafts', { duration: 1500 });
            break;

          case 'p':
            e.preventDefault();
            navigate('/publish');
            toast.success('⌘P - Publish', { duration: 1500 });
            break;

          case 'm':
            e.preventDefault();
            navigate('/messages');
            toast.success('⌘M - Messages', { duration: 1500 });
            break;

          case 'a':
            e.preventDefault();
            navigate('/analytics');
            toast.success('⌘A - Analytics', { duration: 1500 });
            break;

          case ',':
            e.preventDefault();
            navigate('/settings');
            toast.success('⌘, - Settings', { duration: 1500 });
            break;
        }
      }

      // Help shortcut (without modifier)
      if (!isMod && !e.shiftKey && !e.altKey && e.key === '?') {
        e.preventDefault();
        showShortcutsHelp();
      }
    };

    document.addEventListener('keydown', handleKeyPress);

    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [navigate]);
}

/**
 * Show keyboard shortcuts help
 */
function showShortcutsHelp() {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const mod = isMac ? '⌘' : 'Ctrl';

  const shortcuts = [
    `${mod}+K - Command Palette`,
    `${mod}+H - Dashboard`,
    `${mod}+U - Upload Photos`,
    `${mod}+D - My Drafts`,
    `${mod}+P - Publish`,
    `${mod}+M - Messages`,
    `${mod}+A - Analytics`,
    `${mod}+, - Settings`,
    `? - Show this help`
  ];

  const message = `⌨️ Keyboard Shortcuts\n\n${shortcuts.join('\n')}`;

  toast(message, {
    duration: 8000,
    position: 'bottom-right',
    style: {
      maxWidth: '400px',
      whiteSpace: 'pre-line',
      fontFamily: 'monospace'
    }
  });
}

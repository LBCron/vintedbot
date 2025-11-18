import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useHotkeys } from 'react-hotkeys-hook';

export function useKeyboardShortcuts() {
  const navigate = useNavigate();

  // Navigation
  useHotkeys('ctrl+d,cmd+d', (e) => {
    e.preventDefault();
    navigate('/dashboard');
  }, { enableOnFormTags: false });

  useHotkeys('ctrl+u,cmd+u', (e) => {
    e.preventDefault();
    navigate('/upload');
  }, { enableOnFormTags: false });

  useHotkeys('ctrl+shift+d,cmd+shift+d', (e) => {
    e.preventDefault();
    navigate('/drafts');
  }, { enableOnFormTags: false });

  useHotkeys('ctrl+m,cmd+m', (e) => {
    e.preventDefault();
    navigate('/messages');
  }, { enableOnFormTags: false });

  useHotkeys('ctrl+shift+a,cmd+shift+a', (e) => {
    e.preventDefault();
    navigate('/analytics');
  }, { enableOnFormTags: false });

  // Save
  useHotkeys('ctrl+s,cmd+s', (e) => {
    e.preventDefault();
    // Trigger save event
    window.dispatchEvent(new CustomEvent('keyboard-save'));
  });

  // Escape
  useHotkeys('esc', (e) => {
    e.preventDefault();
    // Close modals, dropdowns, etc.
    window.dispatchEvent(new CustomEvent('keyboard-escape'));
  });

  return null;
}

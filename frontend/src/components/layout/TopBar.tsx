import { useState, Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { motion } from 'framer-motion';
import {
  Search,
  Bell,
  Sun,
  Moon,
  User,
  Settings,
  LogOut,
  HelpCircle,
  Command,
} from 'lucide-react';
import { Badge } from '../common/Badge';
import { useNavigate } from 'react-router-dom';
import NotificationCenter from '../NotificationCenter';

interface TopBarProps {
  onOpenCommandPalette: () => void;
}

export default function TopBar({ onOpenCommandPalette }: TopBarProps) {
  const navigate = useNavigate();
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <header className="sticky top-0 z-30 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
      <div className="px-6 py-4 flex items-center justify-between gap-4">
        {/* Search */}
        <div className="flex-1 max-w-2xl">
          <button
            onClick={onOpenCommandPalette}
            className="w-full flex items-center gap-3 px-4 py-2.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors text-left group"
          >
            <Search className="w-5 h-5 text-gray-400" />
            <span className="flex-1 text-gray-600 dark:text-gray-400 text-sm">
              Search pages, drafts, actions...
            </span>
            <div className="flex items-center gap-1 px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded text-xs font-medium text-gray-600 dark:text-gray-400">
              <Command className="w-3 h-3" />
              <span>K</span>
            </div>
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2.5 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
          >
            {theme === 'light' ? (
              <Moon className="w-5 h-5" />
            ) : (
              <Sun className="w-5 h-5" />
            )}
          </button>

          {/* Notifications */}
          <div className="relative">
            <NotificationCenter />
          </div>

          {/* User Menu */}
          <Menu as="div" className="relative">
            <Menu.Button className="flex items-center gap-3 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-purple-500 flex items-center justify-center text-white font-semibold text-sm">
                A
              </div>
            </Menu.Button>

            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right rounded-lg bg-white dark:bg-gray-800 shadow-lg ring-1 ring-black/5 dark:ring-white/10 focus:outline-none">
                {/* User Info */}
                <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                  <p className="font-medium text-gray-900 dark:text-white text-sm">
                    Admin User
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                    admin@vintedbot.com
                  </p>
                </div>

                {/* Menu Items */}
                <div className="py-1">
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={() => navigate('/settings')}
                        className={`w-full flex items-center gap-3 px-4 py-2 text-sm ${
                          active
                            ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                            : 'text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        <User className="w-4 h-4" />
                        Profile
                      </button>
                    )}
                  </Menu.Item>

                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={() => navigate('/settings')}
                        className={`w-full flex items-center gap-3 px-4 py-2 text-sm ${
                          active
                            ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                            : 'text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        <Settings className="w-4 h-4" />
                        Settings
                      </button>
                    )}
                  </Menu.Item>

                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={() => navigate('/help')}
                        className={`w-full flex items-center gap-3 px-4 py-2 text-sm ${
                          active
                            ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                            : 'text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        <HelpCircle className="w-4 h-4" />
                        Help Center
                      </button>
                    )}
                  </Menu.Item>
                </div>

                {/* Logout */}
                <div className="border-t border-gray-200 dark:border-gray-700 py-1">
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={() => navigate('/login')}
                        className={`w-full flex items-center gap-3 px-4 py-2 text-sm ${
                          active
                            ? 'bg-error-50 dark:bg-error-900/20 text-error-700 dark:text-error-400'
                            : 'text-error-600 dark:text-error-400'
                        }`}
                      >
                        <LogOut className="w-4 h-4" />
                        Logout
                      </button>
                    )}
                  </Menu.Item>
                </div>
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </header>
  );
}

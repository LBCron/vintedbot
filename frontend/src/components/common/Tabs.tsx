import { createContext, useContext, useState, ReactNode } from 'react';
import { clsx } from 'clsx';

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const TabsContext = createContext<TabsContextValue | undefined>(undefined);

function useTabsContext() {
  const context = useContext(TabsContext);
  if (!context) {
    throw new Error('Tabs components must be used within a Tabs provider');
  }
  return context;
}

interface TabsProps {
  defaultValue: string;
  children: ReactNode;
  className?: string;
  onValueChange?: (value: string) => void;
}

export function Tabs({ defaultValue, children, className, onValueChange }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultValue);

  const handleSetActiveTab = (tab: string) => {
    setActiveTab(tab);
    onValueChange?.(tab);
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleSetActiveTab }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

interface TabsListProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'pills' | 'underline';
}

export function TabsList({ children, className, variant = 'default' }: TabsListProps) {
  const variants = {
    default: 'bg-gray-100 dark:bg-gray-800 p-1 rounded-lg',
    pills: 'gap-2',
    underline: 'border-b border-gray-200 dark:border-gray-700',
  };

  return (
    <div className={clsx('flex', variants[variant], className)}>
      {children}
    </div>
  );
}

interface TabsTriggerProps {
  value: string;
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'pills' | 'underline';
}

export function TabsTrigger({ value, children, className, variant = 'default' }: TabsTriggerProps) {
  const { activeTab, setActiveTab } = useTabsContext();
  const isActive = activeTab === value;

  const variants = {
    default: {
      base: 'px-4 py-2 text-sm font-medium rounded-md transition-all',
      active: 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white shadow-sm',
      inactive: 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white',
    },
    pills: {
      base: 'px-4 py-2 text-sm font-medium rounded-full transition-all',
      active: 'bg-primary-500 text-white shadow-sm',
      inactive: 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800',
    },
    underline: {
      base: 'px-4 py-3 text-sm font-medium border-b-2 transition-all',
      active: 'border-primary-500 text-primary-600 dark:text-primary-400',
      inactive: 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:border-gray-300 dark:hover:border-gray-600',
    },
  };

  const variantStyles = variants[variant];

  return (
    <button
      type="button"
      onClick={() => setActiveTab(value)}
      className={clsx(
        variantStyles.base,
        isActive ? variantStyles.active : variantStyles.inactive,
        className
      )}
    >
      {children}
    </button>
  );
}

interface TabsContentProps {
  value: string;
  children: ReactNode;
  className?: string;
}

export function TabsContent({ value, children, className }: TabsContentProps) {
  const { activeTab } = useTabsContext();

  if (activeTab !== value) {
    return null;
  }

  return (
    <div className={clsx('animate-fade-in', className)}>
      {children}
    </div>
  );
}

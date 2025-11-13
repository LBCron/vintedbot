import { Fragment, ReactNode } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { X } from 'lucide-react';
import { clsx } from 'clsx';

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  position?: 'left' | 'right' | 'bottom';
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  title?: string;
  description?: string;
}

export default function Drawer({
  open,
  onClose,
  children,
  position = 'right',
  size = 'md',
  title,
  description,
}: DrawerProps) {
  const positions = {
    left: 'inset-y-0 left-0',
    right: 'inset-y-0 right-0',
    bottom: 'inset-x-0 bottom-0',
  };

  const sizes = {
    sm: position === 'bottom' ? 'max-h-[40vh]' : 'max-w-sm',
    md: position === 'bottom' ? 'max-h-[60vh]' : 'max-w-md',
    lg: position === 'bottom' ? 'max-h-[75vh]' : 'max-w-lg',
    xl: position === 'bottom' ? 'max-h-[85vh]' : 'max-w-xl',
    full: position === 'bottom' ? 'max-h-screen' : 'max-w-screen',
  };

  const slideDirections = {
    left: {
      enter: '-translate-x-full',
      enterTo: 'translate-x-0',
      leave: 'translate-x-0',
      leaveTo: '-translate-x-full',
    },
    right: {
      enter: 'translate-x-full',
      enterTo: 'translate-x-0',
      leave: 'translate-x-0',
      leaveTo: 'translate-x-full',
    },
    bottom: {
      enter: 'translate-y-full',
      enterTo: 'translate-y-0',
      leave: 'translate-y-0',
      leaveTo: 'translate-y-full',
    },
  };

  const slide = slideDirections[position];

  return (
    <Transition appear show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-hidden">
          <div className="absolute inset-0 overflow-hidden">
            <div className={clsx('pointer-events-none fixed flex', positions[position])}>
              <Transition.Child
                as={Fragment}
                enter="transform transition ease-in-out duration-300"
                enterFrom={slide.enter}
                enterTo={slide.enterTo}
                leave="transform transition ease-in-out duration-200"
                leaveFrom={slide.leave}
                leaveTo={slide.leaveTo}
              >
                <Dialog.Panel
                  className={clsx(
                    'pointer-events-auto w-screen',
                    sizes[size],
                    'bg-white dark:bg-gray-900 shadow-2xl'
                  )}
                >
                  <div className="flex h-full flex-col">
                    {/* Header */}
                    {(title || description) && (
                      <div className="border-b border-gray-200 dark:border-gray-800 px-6 py-4">
                        <div className="flex items-start justify-between">
                          <div>
                            {title && (
                              <Dialog.Title className="text-lg font-semibold text-gray-900 dark:text-white">
                                {title}
                              </Dialog.Title>
                            )}
                            {description && (
                              <Dialog.Description className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                                {description}
                              </Dialog.Description>
                            )}
                          </div>
                          <button
                            type="button"
                            className="rounded-lg p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:text-gray-300 dark:hover:bg-gray-800 transition-colors"
                            onClick={onClose}
                          >
                            <X className="h-5 w-5" />
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Content */}
                    <div className="flex-1 overflow-y-auto p-6">
                      {children}
                    </div>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

import { Fragment, ReactNode } from 'react';
import { Popover as HeadlessPopover, Transition } from '@headlessui/react';
import { clsx } from 'clsx';

interface PopoverProps {
  trigger: ReactNode;
  children: ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}

export default function Popover({
  trigger,
  children,
  position = 'bottom',
  className,
}: PopoverProps) {
  const positions = {
    top: 'bottom-full mb-2 left-1/2 -translate-x-1/2',
    bottom: 'top-full mt-2 left-1/2 -translate-x-1/2',
    left: 'right-full mr-2 top-1/2 -translate-y-1/2',
    right: 'left-full ml-2 top-1/2 -translate-y-1/2',
  };

  return (
    <HeadlessPopover className="relative">
      {({ open }) => (
        <>
          <HeadlessPopover.Button as="div" className="cursor-pointer">
            {trigger}
          </HeadlessPopover.Button>

          <Transition
            as={Fragment}
            enter="transition ease-out duration-200"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="transition ease-in duration-150"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <HeadlessPopover.Panel
              className={clsx(
                'absolute z-50',
                'bg-white dark:bg-gray-800',
                'border border-gray-200 dark:border-gray-700',
                'rounded-lg shadow-xl',
                'min-w-[200px] max-w-md',
                positions[position],
                className
              )}
            >
              {children}
            </HeadlessPopover.Panel>
          </Transition>
        </>
      )}
    </HeadlessPopover>
  );
}

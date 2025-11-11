import { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import {
  Bars3Icon,
  BellIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useUIStore } from '../../store/uiStore';
import { useAuth } from '../../hooks/useAuth';
import { classNames } from '../../utils/classNames';
import { ImpersonationDropdown } from '../admin/ImpersonationDropdown';

export function Header() {
  const { setSidebarOpen } = useUIStore();
  const { user, logout } = useAuth();

  const userNavigation = [
    { name: 'Your Profile', href: '/profile', icon: UserCircleIcon },
    { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
  ];

  return (
    <div className="sticky top-0 z-10 flex-shrink-0 flex h-16 bg-white shadow-md border-b border-gray-200">
      {/* Mobile menu button */}
      <button
        type="button"
        className="px-4 border-r border-gray-200 text-gray-500 hover:bg-gray-50 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 transition-colors lg:hidden"
        onClick={() => setSidebarOpen(true)}
      >
        <span className="sr-only">Open sidebar</span>
        <Bars3Icon className="h-6 w-6" aria-hidden="true" />
      </button>

      <div className="flex-1 px-4 flex justify-between">
        {/* Left side - Search or breadcrumbs could go here */}
        <div className="flex-1 flex items-center">
          <div className="w-full max-w-lg lg:max-w-xs">
            {/* Search component can be added here */}
          </div>
        </div>

        {/* Right side */}
        <div className="ml-4 flex items-center md:ml-6 space-x-4">
          {/* Impersonation (Admin only) */}
          <ImpersonationDropdown />

          {/* Notifications */}
          <button
            type="button"
            className="relative p-2 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-all duration-200"
          >
            <span className="sr-only">View notifications</span>
            <BellIcon className="h-6 w-6" aria-hidden="true" />
            {/* Notification badge */}
            <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full ring-2 ring-white"></span>
          </button>

          {/* Profile dropdown */}
          <Menu as="div" className="relative">
            <div>
              <Menu.Button className="max-w-xs bg-white flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 hover:ring-2 hover:ring-primary-300 transition-all duration-200">
                <span className="sr-only">Open user menu</span>
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center text-white font-semibold shadow-md">
                  {user?.displayName?.charAt(0) ||
                    user?.username?.charAt(0) ||
                    'U'}
                </div>
              </Menu.Button>
            </div>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="origin-top-right absolute right-0 mt-2 w-56 rounded-xl shadow-xl py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none animate-scale-in">
                {/* User info */}
                <div className="px-4 py-3 border-b border-gray-100 bg-gradient-to-r from-primary-50 to-secondary-50">
                  <p className="text-sm font-semibold text-gray-900">
                    {user?.displayName || user?.username || 'User'}
                  </p>
                  <p className="text-xs text-gray-600 truncate mt-1">
                    {user?.email}
                  </p>
                </div>

                {/* Navigation items */}
                {userNavigation.map((item) => (
                  <Menu.Item key={item.name}>
                    {({ active }) => (
                      <a
                        href={item.href}
                        className={classNames(
                          active ? 'bg-gray-50' : '',
                          'flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors duration-150'
                        )}
                      >
                        <item.icon
                          className={classNames(
                            active ? 'text-primary-600' : 'text-gray-400',
                            'mr-3 h-5 w-5 transition-colors'
                          )}
                          aria-hidden="true"
                        />
                        {item.name}
                      </a>
                    )}
                  </Menu.Item>
                ))}

                {/* Logout */}
                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={() => logout()}
                      className={classNames(
                        active ? 'bg-red-50' : '',
                        'flex w-full items-center px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors duration-150 border-t border-gray-100'
                      )}
                    >
                      <ArrowRightOnRectangleIcon
                        className="mr-3 h-5 w-5 text-red-500"
                        aria-hidden="true"
                      />
                      Sign out
                    </button>
                  )}
                </Menu.Item>
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </div>
  );
}

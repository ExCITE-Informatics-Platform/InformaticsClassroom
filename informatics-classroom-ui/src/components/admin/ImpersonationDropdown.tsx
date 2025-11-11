import { Fragment, useState } from 'react';
import { Menu, Transition, Combobox } from '@headlessui/react';
import { UserIcon, MagnifyingGlassIcon, CheckIcon } from '@heroicons/react/24/outline';
import { useImpersonation } from '../../hooks/useImpersonation';
import { classNames } from '../../utils/classNames';
import { useAuth } from '../../hooks/useAuth';

export function ImpersonationDropdown() {
  const { user } = useAuth();
  const { users, usersLoading, startImpersonation, isImpersonating, impersonationError } = useImpersonation();
  const [query, setQuery] = useState('');

  // Only show to admins
  if (!user?.roles?.includes('admin')) {
    return null;
  }

  const filteredUsers =
    query === ''
      ? users
      : users.filter((u) => {
          const searchTerm = query.toLowerCase();
          return (
            u.displayName.toLowerCase().includes(searchTerm) ||
            u.email.toLowerCase().includes(searchTerm) ||
            u.id.toLowerCase().includes(searchTerm)
          );
        });

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="p-2 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition-all duration-200">
        <span className="sr-only">Impersonate user</span>
        <UserIcon className="h-6 w-6" aria-hidden="true" />
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
        <Menu.Items className="origin-top-right absolute right-0 mt-2 w-80 rounded-xl shadow-xl bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
          <div className="p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">
              Impersonate User
            </h3>
            <p className="text-xs text-gray-500 mb-3">
              View the application as another user for testing and support
            </p>

            {/* Search input */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search users..."
                className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
            </div>

            {/* User list */}
            <div className="mt-3 max-h-64 overflow-y-auto">
              {usersLoading ? (
                <div className="text-center py-4 text-sm text-gray-500">
                  Loading users...
                </div>
              ) : filteredUsers.length === 0 ? (
                <div className="text-center py-4 text-sm text-gray-500">
                  No users found
                </div>
              ) : (
                <ul className="space-y-1">
                  {filteredUsers.map((u) => (
                    <li key={u.id}>
                      <button
                        onClick={() => {
                          startImpersonation(u.id);
                          setQuery('');
                        }}
                        disabled={isImpersonating || u.id === user.id}
                        className={classNames(
                          'w-full text-left px-3 py-2 rounded-lg transition-colors',
                          u.id === user.id
                            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            : 'hover:bg-amber-50 hover:text-amber-900',
                          isImpersonating ? 'opacity-50 cursor-wait' : ''
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {u.displayName}
                            </p>
                            <p className="text-xs text-gray-500 truncate">
                              {u.email}
                            </p>
                            <div className="flex gap-1 mt-1">
                              {u.roles.map((role) => (
                                <span
                                  key={role}
                                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                                >
                                  {role}
                                </span>
                              ))}
                            </div>
                          </div>
                          {u.id === user.id && (
                            <span className="ml-2 text-xs text-gray-400">
                              (You)
                            </span>
                          )}
                        </div>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
}

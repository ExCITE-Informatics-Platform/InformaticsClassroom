import { UserIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../hooks/useAuth';
import { useImpersonation } from '../../hooks/useImpersonation';
import { Button } from '../ui/button';

export function ImpersonationBanner() {
  const { impersonating, originalUser, user } = useAuth();
  const { stopImpersonation, isStoppingImpersonation } = useImpersonation();

  if (!impersonating) {
    return null;
  }

  return (
    <div className="bg-amber-500 text-white px-4 py-3 shadow-md border-b-2 border-amber-600">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <UserIcon className="h-6 w-6 flex-shrink-0" />
          <div>
            <p className="text-sm font-bold">
              🎭 Impersonating: {user?.displayName || user?.email || 'Unknown User'}
            </p>
            <p className="text-xs opacity-90">
              Original admin: {originalUser?.displayName || originalUser?.email}
            </p>
          </div>
        </div>
        <Button
          onClick={() => stopImpersonation()}
          disabled={isStoppingImpersonation}
          size="sm"
          variant="outline"
          className="bg-white text-amber-700 hover:bg-amber-50 border-amber-600 font-semibold"
        >
          {isStoppingImpersonation ? (
            <>
              <XMarkIcon className="h-4 w-4 mr-2 animate-spin" />
              Exiting...
            </>
          ) : (
            <>
              <XMarkIcon className="h-4 w-4 mr-2" />
              Exit Impersonation
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

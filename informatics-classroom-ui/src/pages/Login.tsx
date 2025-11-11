import { useState, useEffect, type FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Button, Input, Card } from '../components/common';

export function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, loginError, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as any)?.from?.pathname || '/';

  // Development mode bypass: if already authenticated (session auto-created), redirect to home
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    // Initiate MSAL login flow (redirects to Microsoft)
    login();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 animate-fade-in">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-gradient-to-br from-primary-600 to-secondary-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg">
            <span className="text-3xl font-bold text-white">IC</span>
          </div>
          <h2 className="text-3xl font-display font-bold text-gray-900">
            Informatics Classroom
          </h2>
          <p className="mt-2 text-base text-gray-600">
            Sign in to your account
          </p>
        </div>

        <Card className="shadow-xl border-0">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {loginError && (
              <div className="rounded-lg bg-red-50 border-l-4 border-red-500 p-4 animate-fade-in shadow-sm">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-red-500"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-semibold text-red-800">
                      Authentication failed
                    </h3>
                    <div className="mt-1 text-sm text-red-700">
                      {loginError.message}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <Input
              id="username"
              name="username"
              type="text"
              label="Username"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
            />

            <Input
              id="password"
              name="password"
              type="password"
              label="Password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
            />

            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded transition-colors"
                />
                <label
                  htmlFor="remember-me"
                  className="ml-2 block text-sm font-medium text-gray-700"
                >
                  Remember me
                </label>
              </div>

              <div className="text-sm">
                <a
                  href="#"
                  className="font-semibold text-primary-600 hover:text-primary-700 transition-colors"
                >
                  Forgot password?
                </a>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              fullWidth
              loading={isLoading}
              className="h-12 text-base font-semibold shadow-lg hover:shadow-xl"
            >
              Sign in
            </Button>

            <div className="text-center">
              <p className="text-sm text-gray-500">
                Don't have an account?{' '}
                <a href="/register" className="font-semibold text-primary-600 hover:text-primary-700 transition-colors">
                  Contact your administrator
                </a>
              </p>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}

/**
 * Login Page - Apple-Inspired Design
 *
 * User authentication with email/password or Google
 */
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Mail, Lock } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login, loginWithGoogle, resetPassword } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    try {
      setError('');
      setMessage('');
      setLoading(true);
      await login(email, password);
      router.push('/personas');
    } catch (err: any) {
      setError(err.message || 'Failed to log in');
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleSignIn() {
    try {
      setError('');
      setMessage('');
      setLoading(true);
      await loginWithGoogle();
      router.push('/personas');
    } catch (err: any) {
      setError(err.message || 'Failed to sign in with Google');
    } finally {
      setLoading(false);
    }
  }

  async function handleForgotPassword() {
    if (!email) {
      return setError('Please enter your email address');
    }

    try {
      setError('');
      setMessage('');
      setLoading(true);
      await resetPassword(email);
      setMessage('Password reset email sent! Check your inbox.');
    } catch (err: any) {
      setError(err.message || 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-apple-bg-tertiary gradient-apple-mesh flex items-center justify-center px-6">
      <div className="max-w-md w-full animate-fade-in-up">
        {/* Glass Card Container */}
        <div className="glass-card p-8 space-y-6">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-4xl font-bold text-apple-text-primary font-serif mb-2">
              Welcome Back
            </h1>
            <p className="text-apple-text-secondary">
              Log in to continue your simulations
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="alert-apple-error animate-scale-in">
              <p className="text-apple-red text-sm font-medium">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {message && (
            <div className="alert-apple-success animate-scale-in">
              <p className="text-apple-green text-sm font-medium">{message}</p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <Input
              type="email"
              label="Email Address"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail size={20} />}
              required
            />

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="label-apple">Password</span>
                <button
                  type="button"
                  onClick={handleForgotPassword}
                  className="text-sm text-apple-blue-500 hover:text-apple-blue-600 font-medium transition-colors"
                >
                  Forgot password?
                </button>
              </div>
              <Input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                icon={<Lock size={20} />}
                required
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              loading={loading}
            >
              {loading ? 'Logging in...' : 'Log In'}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-apple-border-light"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-3 bg-white text-apple-text-secondary font-medium">
                Or continue with
              </span>
            </div>
          </div>

          {/* Google Sign In */}
          <button
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="w-full bg-white hover:bg-apple-bg-tertiary border border-apple-border rounded-apple py-3 px-4 transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-apple-sm hover:shadow-apple-md"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Sign in with Google
          </button>

          {/* Sign Up Link */}
          <div className="text-center pt-2">
            <p className="text-apple-text-secondary text-sm">
              Don't have an account?{' '}
              <Link
                href="/signup"
                className="text-apple-blue-500 hover:text-apple-blue-600 font-semibold transition-colors"
              >
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

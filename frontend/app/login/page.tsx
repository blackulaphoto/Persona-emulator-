/**
 * Login Page
 * 
 * User authentication with email/password or Google
 */
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';

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
      router.push('/app');
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
      router.push('/app');
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
    <div className="min-h-screen bg-[#1a1d20] flex items-center justify-center px-6">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-[#F8F6F1] font-['Crimson_Pro'] mb-2">
            Welcome Back
          </h1>
          <p className="text-[#8B9D83] font-['Outfit']">
            Log in to continue your simulations
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-[#C17B5C]/10 border border-[#C17B5C]/30 rounded-lg p-4">
            <p className="text-[#C17B5C] text-sm font-['Outfit']">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {message && (
          <div className="bg-[#5B6B4D]/10 border border-[#5B6B4D]/30 rounded-lg p-4">
            <p className="text-[#5B6B4D] text-sm font-['Outfit']">{message}</p>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-[#8B9D83] mb-2 font-['Outfit']">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-[#2D3136] border border-[#8B9D83]/20 rounded-lg text-[#F8F6F1] focus:outline-none focus:border-[#5B6B4D] font-['Outfit']"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label htmlFor="password" className="block text-sm font-medium text-[#8B9D83] font-['Outfit']">
                Password
              </label>
              <button
                type="button"
                onClick={handleForgotPassword}
                className="text-sm text-[#5B6B4D] hover:text-[#4a5a3e] font-['Outfit']"
              >
                Forgot password?
              </button>
            </div>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-[#2D3136] border border-[#8B9D83]/20 rounded-lg text-[#F8F6F1] focus:outline-none focus:border-[#5B6B4D] font-['Outfit']"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#5B6B4D] hover:bg-[#4a5a3e] text-white font-semibold py-3 px-4 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed font-['Outfit']"
          >
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[#8B9D83]/20"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-[#1a1d20] text-[#8B9D83] font-['Outfit']">Or continue with</span>
          </div>
        </div>

        {/* Google Sign In */}
        <button
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="w-full bg-white hover:bg-gray-100 text-[#2D3136] font-semibold py-3 px-4 rounded-lg transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed font-['Outfit']"
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
        <div className="text-center">
          <p className="text-[#8B9D83] text-sm font-['Outfit']">
            Don't have an account?{' '}
            <Link href="/signup" className="text-[#5B6B4D] hover:text-[#4a5a3e] font-semibold">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

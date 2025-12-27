/**
 * Header Component with Logo
 * 
 * Place in: frontend/components/Header.tsx
 */
'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push('/');
  }

  return (
    <header className="bg-[#1a1d20] border-b border-[#8B9D83]/20 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo & Brand */}
          <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <Image
              src="/logo.png"
              alt="LifeStream Labs"
              width={40}
              height={40}
              className="object-contain"
            />
            <div className="flex flex-col">
              <span className="text-xl font-bold text-[#F8F6F1] font-['Crimson_Pro']">
                Persona Evolution
              </span>
              <span className="text-xs text-[#8B9D83] font-['Outfit']">
                by LifeStream Labs
              </span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-6">
            {user ? (
              <>
                <Link
                  href="/app"
                  className="text-[#F8F6F1] hover:text-[#5B6B4D] transition-colors font-['Outfit']"
                >
                  Dashboard
                </Link>
                <Link
                  href="/personas"
                  className="text-[#F8F6F1] hover:text-[#5B6B4D] transition-colors font-['Outfit']"
                >
                  Personas
                </Link>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-[#8B9D83] font-['Outfit']">
                    {user.email}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="px-4 py-2 bg-[#2D3136] hover:bg-[#3D4146] text-[#F8F6F1] rounded-lg transition-colors font-['Outfit']"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-[#F8F6F1] hover:text-[#5B6B4D] transition-colors font-['Outfit']"
                >
                  Login
                </Link>
                <Link
                  href="/signup"
                  className="px-4 py-2 bg-[#5B6B4D] hover:bg-[#4a5a3e] text-white rounded-lg transition-colors font-['Outfit']"
                >
                  Sign Up
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}

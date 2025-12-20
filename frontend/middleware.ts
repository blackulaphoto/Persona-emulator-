/**
 * Middleware
 * 
 * Protects routes that require authentication
 * Redirects unauthenticated users to login
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Get the pathname
  const path = request.nextUrl.pathname;

  // Define protected routes (require authentication)
  const protectedPaths = ['/app', '/persona', '/settings', '/profile'];
  
  // Define public routes (don't require authentication)
  const publicPaths = ['/', '/login', '/signup'];

  // Check if current path is protected
  const isProtectedPath = protectedPaths.some(protectedPath => 
    path.startsWith(protectedPath)
  );

  // Check if current path is public
  const isPublicPath = publicPaths.includes(path);

  // For now, we'll rely on client-side protection with AuthContext
  // Firebase auth state is checked on the client
  // This middleware is here for future enhancement with session cookies

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public directory)
     */
    '/((?!_next/static|_next/image|favicon.ico|splash).*)',
  ],
};

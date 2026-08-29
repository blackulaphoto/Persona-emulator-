/**
 * Small helpers for turning raw Firebase Auth error codes into the plain
 * language the Rubicks UI shows. AuthContext's methods rethrow the original
 * Firebase error (preserving `.code`) rather than wrapping it, specifically
 * so this module can tell "account already exists" apart from every other
 * failure - never surface a `.code` string or a raw Firebase message to the
 * user.
 */

const COLLISION_CODES = new Set([
  'auth/email-already-in-use',
  'auth/credential-already-in-use',
  'auth/account-exists-with-different-credential',
]);

export function getAuthErrorCode(error: unknown): string | undefined {
  if (typeof error === 'object' && error !== null && 'code' in error) {
    return String((error as { code: unknown }).code);
  }
  return undefined;
}

/** True when saving/linking failed because an account already exists for that email or provider. */
export function isAccountCollision(error: unknown): boolean {
  const code = getAuthErrorCode(error);
  return !!code && COLLISION_CODES.has(code);
}

/** Plain-language message for the auth errors the demo-conversion and login/signup UI need to explain. Never technical Firebase language. */
export function friendlyAuthErrorMessage(error: unknown): string {
  switch (getAuthErrorCode(error)) {
    case 'auth/email-already-in-use':
    case 'auth/credential-already-in-use':
    case 'auth/account-exists-with-different-credential':
      return 'An account already exists for that email or Google account.';
    case 'auth/weak-password':
      return 'Please choose a longer password (at least 6 characters).';
    case 'auth/invalid-email':
      return "That email address doesn't look right.";
    case 'auth/wrong-password':
    case 'auth/invalid-credential':
      return 'Incorrect email or password.';
    case 'auth/user-not-found':
      return 'No account found with that email.';
    case 'auth/popup-closed-by-user':
    case 'auth/cancelled-popup-request':
      return 'Sign-in was cancelled.';
    case 'auth/network-request-failed':
      return 'Network error - check your connection and try again.';
    case 'auth/too-many-requests':
      return 'Too many attempts. Please wait a moment and try again.';
    default:
      return 'Something went wrong. Please try again.';
  }
}

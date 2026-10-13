/**
 * Development-only session stub.
 *
 * Real accounts, roles and tenancy arrive in Sprint 2. Until then the app
 * separates the public side from the protected side with a flag held in
 * localStorage, so the split can be demonstrated without pretending to be
 * authentication.
 */

const SESSION_KEY = "tafi.devSession";
const DEMO_VALUE = "demo";

export function hasDevSession(): boolean {
  try {
    return window.localStorage.getItem(SESSION_KEY) === DEMO_VALUE;
  } catch {
    return false;
  }
}

export function startDevSession(): void {
  try {
    window.localStorage.setItem(SESSION_KEY, DEMO_VALUE);
  } catch {
    // Private browsing or a locked-down browser: the demo simply will not persist.
  }
}

export function endDevSession(): void {
  try {
    window.localStorage.removeItem(SESSION_KEY);
  } catch {
    // Nothing to clear.
  }
}

import { RefObject, useEffect } from 'react'

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

/**
 * Real keyboard focus trap for the drawer/modal overlays - Tab/Shift+Tab
 * cycle within the panel instead of escaping to the page underneath, focus
 * moves onto the panel when it opens, and returns to whatever triggered it
 * when it closes. Shared by RubixDrawer and RubixModal rather than
 * duplicated, since both are the same overlay pattern at heart.
 */
export function useFocusTrap(panelRef: RefObject<HTMLElement>, open: boolean) {
  useEffect(() => {
    if (!open) return
    const panel = panelRef.current
    if (!panel) return

    const previouslyFocused = document.activeElement as HTMLElement | null

    const focusables = () => Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR))
    const first = focusables()[0]
    ;(first || panel).focus()

    function onKeyDown(e: KeyboardEvent) {
      if (e.key !== 'Tab') return
      const items = focusables()
      if (items.length === 0) return
      const firstEl = items[0]
      const lastEl = items[items.length - 1]
      if (e.shiftKey && document.activeElement === firstEl) {
        e.preventDefault()
        lastEl.focus()
      } else if (!e.shiftKey && document.activeElement === lastEl) {
        e.preventDefault()
        firstEl.focus()
      }
    }

    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      previouslyFocused?.focus?.()
    }
  }, [open, panelRef])
}

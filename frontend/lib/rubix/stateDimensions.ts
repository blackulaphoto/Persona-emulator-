/**
 * Shared metadata for the six real `current_state` dimensions the backend
 * tracks (see backend/app/services/state_trait_engine.py). Used anywhere a
 * Rubix surface needs to turn a raw 0-1 state value into a human label -
 * originally lived only in app/persona/[id]/page.tsx's CurrentStatePanel;
 * pulled out here once Build Their Life's Impact Reveal needed the same
 * mapping, rather than duplicating it a second time.
 */
export const STATE_DIMENSIONS: Record<
  string,
  { label: string; adverseWhen: 'high' | 'low'; highLabel: string; lowLabel: string }
> = {
  trust: { label: 'Trust', adverseWhen: 'low', highLabel: 'Open to trusting', lowLabel: 'Guarded about trusting' },
  threat_sensitivity: { label: 'Threat Sensitivity', adverseWhen: 'high', highLabel: 'On alert', lowLabel: 'Feels safe' },
  mood: { label: 'Mood', adverseWhen: 'low', highLabel: 'Buoyant', lowLabel: 'Low' },
  regulation: { label: 'Emotional Regulation', adverseWhen: 'low', highLabel: 'Steady', lowLabel: 'Easily overwhelmed' },
  avoidance: { label: 'Avoidance', adverseWhen: 'high', highLabel: 'Pulling away', lowLabel: 'Staying present' },
  relational_security: { label: 'Relational Security', adverseWhen: 'low', highLabel: 'Secure with others', lowLabel: 'Unsure where they stand' },
}

// Only surface dimensions that have moved off neutral enough to be notable -
// same threshold CurrentStatePanel uses.
export const STATE_NEUTRAL = 0.5
export const STATE_NOTABLE_DELTA = 0.08

/** Handles both the snake_case the engine mostly uses (adaptation_strategy, pattern_key)
 *  and the camelCase a few fields use (foundational_environment_signals' keys, e.g.
 *  caregiverReliability) - both are real vocabularies in this codebase, not a typo. */
export function titleCase(value: string): string {
  return value
    .replace(/_/g, ' ')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

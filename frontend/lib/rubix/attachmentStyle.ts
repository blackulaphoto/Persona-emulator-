import type { RubixBadgeTone } from '@/components/rubix';

/**
 * Real attachment style strings the backend's attachment_engine ever stores
 * or derives (see backend/app/services/attachment_engine.py STYLE_BASELINES
 * and derive_attachment_style()). Kept here so every Rubix surface that
 * displays attachment style (Lives, Dashboard, Attachment Detail, Compare)
 * uses the same tone/label mapping instead of inventing its own.
 */
const LABELS: Record<string, string> = {
  secure: 'Secure',
  anxious: 'Anxious',
  'insecure-anxious': 'Anxious',
  avoidant: 'Avoidant',
  'insecure-avoidant': 'Avoidant',
  'fearful-avoidant': 'Fearful-avoidant',
  disorganized: 'Disorganized',
};

const TONES: Record<string, RubixBadgeTone> = {
  secure: 'positive',
  anxious: 'caution',
  'insecure-anxious': 'caution',
  avoidant: 'neutral',
  'insecure-avoidant': 'neutral',
  'fearful-avoidant': 'violet',
  disorganized: 'violet',
};

export function attachmentStyleLabel(style: string | null | undefined): string {
  if (!style) return 'Unknown';
  return LABELS[style.toLowerCase()] || style;
}

export function attachmentStyleTone(style: string | null | undefined): RubixBadgeTone {
  if (!style) return 'muted';
  return TONES[style.toLowerCase()] || 'muted';
}

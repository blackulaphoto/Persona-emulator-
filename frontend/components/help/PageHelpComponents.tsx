/**
 * Page-Level Help Components
 * Adapted for Apple design system
 */

'use client';

import { useState, ReactNode } from 'react';
import { Tooltip } from './HelpComponents';
import { SITE_HELP } from '@/lib/help/SiteWideHelpContent';

// ============================================
// SECTION HELP HEADER
// ============================================

interface SectionHelpProps {
  title: string;
  helpKey: string; // e.g., "personaDetail.bigFive"
}

export function SectionHelp({ title, helpKey }: SectionHelpProps) {
  const [showFullHelp, setShowFullHelp] = useState(false);

  // Get help content
  const parts = helpKey.split('.');
  let help: any = SITE_HELP;
  for (const part of parts) {
    help = help?.[part];
  }

  if (!help) return <h3 className="text-xl font-serif text-apple-text-primary">{title}</h3>;

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-xl font-serif text-apple-text-primary">{title}</h3>
          <Tooltip content={help.tooltip || help.whatIs} />
        </div>

        {(help.whatIs || help.howItWorks || help.whenToUse || help.whatItIncludes) && (
          <button
            onClick={() => setShowFullHelp(!showFullHelp)}
            className="text-sm text-apple-blue-600 hover:text-apple-blue-700 font-medium transition-colors"
          >
            {showFullHelp ? 'Hide guide' : 'Show guide'}
          </button>
        )}
      </div>

      {showFullHelp && (
        <div className="mt-3 p-4 bg-apple-blue-50 border border-apple-blue-200 rounded-lg animate-slide-down">
          {help.whatIs && (
            <div className="mb-3">
              <p className="text-sm font-semibold text-apple-blue-800 mb-1">What is this?</p>
              <p className="text-sm text-apple-text-secondary">{help.whatIs}</p>
            </div>
          )}

          {help.howItWorks && Array.isArray(help.howItWorks) && (
            <div className="mb-3">
              <p className="text-sm font-semibold text-apple-blue-800 mb-1">How it works:</p>
              <ul className="text-sm text-apple-text-secondary space-y-1">
                {help.howItWorks.map((item: string, i: number) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-apple-blue-600">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {help.whenToUse && Array.isArray(help.whenToUse) && (
            <div className="mb-3">
              <p className="text-sm font-semibold text-apple-blue-800 mb-1">When to use:</p>
              <ul className="text-sm text-apple-text-secondary space-y-1">
                {help.whenToUse.map((item: string, i: number) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-apple-blue-600">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {help.whatItIncludes && Array.isArray(help.whatItIncludes) && (
            <div>
              <p className="text-sm font-semibold text-apple-blue-800 mb-1">What it includes:</p>
              <ul className="text-sm text-apple-text-secondary space-y-1">
                {help.whatItIncludes.map((item: string, i: number) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-apple-blue-600">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================
// BUTTON HELP (for action buttons)
// ============================================

interface ButtonHelpProps {
  buttonText: string;
  helpKey: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  className?: string;
}

export function ButtonWithHelp({ buttonText, helpKey, onClick, variant = 'primary', className = '' }: ButtonHelpProps) {
  // Get help content
  const parts = helpKey.split('.');
  let help: any = SITE_HELP;
  for (const part of parts) {
    help = help?.[part];
  }

  const buttonClass = variant === 'primary'
    ? 'bg-apple-blue-600 text-white hover:bg-apple-blue-700 px-4 py-2 rounded-lg font-medium transition-colors'
    : 'bg-apple-bg-secondary text-apple-text-primary hover:bg-apple-bg-tertiary px-4 py-2 rounded-lg font-medium transition-colors';

  return (
    <div className="relative inline-block">
      <button onClick={onClick} className={`${buttonClass} ${className}`}>
        {buttonText}
      </button>
      {help && (
        <div className="absolute -top-1 -right-1">
          <Tooltip content={help.tooltip || help.whatIs} position="bottom" />
        </div>
      )}
    </div>
  );
}

// ============================================
// INLINE QUICK TIP
// ============================================

interface QuickTipProps {
  tip: string;
  type?: 'info' | 'tip' | 'warning';
}

export function QuickTip({ tip, type = 'tip' }: QuickTipProps) {
  const icons = {
    info: 'i',
    tip: 'TIP',
    warning: '!'
  };

  const colors = {
    info: 'bg-apple-blue-50 border-apple-blue-200 text-apple-blue-800',
    tip: 'bg-apple-green/10 border-apple-green/30 text-green-800',
    warning: 'bg-apple-orange/10 border-apple-orange/30 text-orange-800'
  };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium ${colors[type]}`}>
      <span>{icons[type]}</span>
      <span>{tip}</span>
    </div>
  );
}

// ============================================
// TRAIT DEFINITION POPOVER
// ============================================

interface TraitHelpProps {
  trait: 'openness' | 'conscientiousness' | 'extraversion' | 'agreeableness' | 'neuroticism';
  score: number;
}

export function TraitHelp({ trait, score }: TraitHelpProps) {
  const [show, setShow] = useState(false);

  const traitData = SITE_HELP.personaDetail.bigFive.traits[trait];
  const isHigh = score >= 60;

  return (
    <div className="relative inline-block ml-2">
      <button
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onClick={() => setShow(!show)}
        className="w-4 h-4 rounded-full bg-apple-blue-100 text-apple-blue-600 flex items-center justify-center text-xs hover:bg-apple-blue-200 transition-colors cursor-help"
      >
        ?
      </button>

      {show && (
        <div className="absolute z-50 w-72 p-4 bg-white border border-apple-border rounded-lg shadow-xl left-0 top-6 animate-fade-in">
          <div className="absolute -top-2 left-2 w-4 h-4 bg-white border-t border-l border-apple-border transform rotate-45" />

          <div className="relative">
            <p className="text-sm font-semibold text-apple-text-primary mb-2">
              {trait.charAt(0).toUpperCase() + trait.slice(1)}
            </p>

            <p className="text-xs text-apple-text-secondary mb-2">
              {traitData.definition}
            </p>

            <div className="bg-apple-blue-50 rounded p-2 mb-2">
              <p className="text-xs font-medium text-apple-blue-700 mb-1">
                This persona scores {score}% ({isHigh ? 'High' : 'Low'}):
              </p>
              <p className="text-xs text-apple-text-secondary">
                {isHigh ? traitData.high : traitData.low}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================
// PAGE HELP BANNER
// ============================================

interface PageHelpBannerProps {
  pageKey: string;
}

export function PageHelpBanner({ pageKey }: PageHelpBannerProps) {
  const [dismissed, setDismissed] = useState(() => {
    // Check if user has dismissed this help before
    if (typeof window !== 'undefined') {
      return localStorage.getItem(`help-dismissed-${pageKey}`) === 'true';
    }
    return false;
  });

  // Get page help
  const parts = pageKey.split('.');
  let help: any = SITE_HELP;
  for (const part of parts) {
    help = help?.[part];
  }

  if (!help?.pageHelp || dismissed) return null;

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem(`help-dismissed-${pageKey}`, 'true');
  };

  return (
    <div className="bg-apple-blue-50 border border-apple-blue-200 rounded-lg p-4 mb-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">?</span>
            <h4 className="text-sm font-semibold text-apple-blue-800">
              {help.pageHelp.title}
            </h4>
          </div>
          <p className="text-sm text-apple-text-secondary">
            {help.pageHelp.content}
          </p>
        </div>

        <button
          onClick={handleDismiss}
          className="text-apple-text-tertiary hover:text-apple-text-secondary transition-colors"
        >
          ×
        </button>
      </div>
    </div>
  );
}

// ============================================
// EMPTY STATE WITH HELP
// ============================================

interface EmptyStateWithHelpProps {
  icon: string;
  title: string;
  description: string;
  actionButton?: {
    text: string;
    onClick: () => void;
    helpKey?: string;
  };
  helpItems?: string[];
}

export function EmptyStateWithHelp({
  icon,
  title,
  description,
  actionButton,
  helpItems
}: EmptyStateWithHelpProps) {
  return (
    <div className="text-center py-12">
      <div className="text-6xl mb-4">{icon}</div>
      <h3 className="text-xl font-serif text-apple-text-primary mb-2">{title}</h3>
      <p className="text-apple-text-secondary mb-6 max-w-md mx-auto">{description}</p>

      {helpItems && helpItems.length > 0 && (
        <div className="bg-apple-blue-50 border border-apple-blue-200 rounded-lg p-4 mb-6 max-w-lg mx-auto text-left">
          <p className="text-sm font-semibold text-apple-blue-800 mb-2">Quick tips:</p>
          <ul className="space-y-1">
            {helpItems.map((item, i) => (
              <li key={i} className="text-sm text-apple-text-secondary flex gap-2">
                <span className="text-apple-blue-600">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {actionButton && (
        <div className="flex justify-center">
          {actionButton.helpKey ? (
            <ButtonWithHelp
              buttonText={actionButton.text}
              helpKey={actionButton.helpKey}
              onClick={actionButton.onClick}
            />
          ) : (
            <button onClick={actionButton.onClick} className="bg-apple-blue-600 text-white hover:bg-apple-blue-700 px-4 py-2 rounded-lg font-medium transition-colors">
              {actionButton.text}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

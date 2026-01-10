/**
 * Page-Level Help Components
 * 
 * Add these to every page/section for contextual guidance
 */

'use client';

import { useState } from 'react';
import { Tooltip } from './HelpComponents';
import { SITE_HELP } from '@/lib/SiteWideHelpContent';

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
  
  if (!help) return <h3 className="text-xl font-serif">{title}</h3>;
  
  return (
    <div className="mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-xl font-serif text-text-primary">{title}</h3>
          <Tooltip content={help.tooltip || help.whatIs} />
        </div>
        
        {(help.whatIs || help.howItWorks) && (
          <button
            onClick={() => setShowFullHelp(!showFullHelp)}
            className="text-sm text-accent-600 hover:text-accent-700 font-medium"
          >
            {showFullHelp ? 'Hide guide' : 'Show guide'}
          </button>
        )}
      </div>
      
      {showFullHelp && (
        <div className="mt-3 p-4 bg-accent-50 border border-accent-200 rounded-lg animate-slide-down">
          {help.whatIs && (
            <div className="mb-3">
              <p className="text-sm font-semibold text-accent-800 mb-1">What is this?</p>
              <p className="text-sm text-text-secondary">{help.whatIs}</p>
            </div>
          )}
          
          {help.howItWorks && (
            <div className="mb-3">
              <p className="text-sm font-semibold text-accent-800 mb-1">How it works:</p>
              <ul className="text-sm text-text-secondary space-y-1">
                {help.howItWorks.map((item: string, i: number) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-accent-600">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {help.whenToUse && (
            <div>
              <p className="text-sm font-semibold text-accent-800 mb-1">When to use:</p>
              <ul className="text-sm text-text-secondary space-y-1">
                {help.whenToUse.map((item: string, i: number) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-accent-600">•</span>
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
}

export function ButtonWithHelp({ buttonText, helpKey, onClick, variant = 'primary' }: ButtonHelpProps) {
  // Get help content
  const parts = helpKey.split('.');
  let help: any = SITE_HELP;
  for (const part of parts) {
    help = help?.[part];
  }
  
  const buttonClass = variant === 'primary' ? 'btn btn-primary' : 'btn btn-secondary';
  
  return (
    <div className="relative inline-block">
      <button onClick={onClick} className={buttonClass}>
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
    info: 'ℹ️',
    tip: '💡',
    warning: '⚠️'
  };
  
  const colors = {
    info: 'bg-accent-50 border-accent-200 text-accent-800',
    tip: 'bg-success-light border-success text-success-dark',
    warning: 'bg-warning-light border-warning text-warning-dark'
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
        className="w-4 h-4 rounded-full bg-primary-200 text-primary-700 flex items-center justify-center text-xs hover:bg-primary-300 transition-colors"
      >
        ?
      </button>
      
      {show && (
        <div className="absolute z-50 w-72 p-4 bg-white border border-border rounded-lg shadow-xl left-0 top-6 animate-fade-in">
          <div className="absolute -top-2 left-2 w-4 h-4 bg-white border-t border-l border-border transform rotate-45" />
          
          <div className="relative">
            <p className="text-sm font-semibold text-text-primary mb-2">
              {trait.charAt(0).toUpperCase() + trait.slice(1)}
            </p>
            
            <p className="text-xs text-text-secondary mb-2">
              {traitData.definition}
            </p>
            
            <div className="bg-primary-50 rounded p-2 mb-2">
              <p className="text-xs font-medium text-accent-700 mb-1">
                This persona scores {score}% ({isHigh ? 'High' : 'Low'}):
              </p>
              <p className="text-xs text-text-secondary">
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
    <div className="bg-accent-50 border border-accent-200 rounded-lg p-4 mb-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">💡</span>
            <h4 className="text-sm font-semibold text-accent-800">
              {help.pageHelp.title}
            </h4>
          </div>
          <p className="text-sm text-text-secondary">
            {help.pageHelp.content}
          </p>
        </div>
        
        <button
          onClick={handleDismiss}
          className="text-text-tertiary hover:text-text-secondary transition-colors"
        >
          ✕
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
      <h3 className="text-xl font-serif text-text-primary mb-2">{title}</h3>
      <p className="text-text-secondary mb-6 max-w-md mx-auto">{description}</p>
      
      {helpItems && helpItems.length > 0 && (
        <div className="bg-accent-50 border border-accent-200 rounded-lg p-4 mb-6 max-w-lg mx-auto text-left">
          <p className="text-sm font-semibold text-accent-800 mb-2">Quick tips:</p>
          <ul className="space-y-1">
            {helpItems.map((item, i) => (
              <li key={i} className="text-sm text-text-secondary flex gap-2">
                <span className="text-accent-600">•</span>
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
            <button onClick={actionButton.onClick} className="btn btn-primary">
              {actionButton.text}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Reusable Help Components
 * 
 * Use these throughout your app for consistent contextual help
 */

'use client';

import { useState, ReactNode } from 'react';

// ============================================
// TOOLTIP COMPONENT
// ============================================

interface TooltipProps {
  content: string | ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  children?: ReactNode;
}

export function Tooltip({ content, position = 'top', children }: TooltipProps) {
  const [show, setShow] = useState(false);
  
  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2'
  };
  
  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 -mt-1 border-t border-l',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 -mb-1 border-b border-r',
    left: 'left-full top-1/2 -translate-y-1/2 -ml-1 border-l border-b',
    right: 'right-full top-1/2 -translate-y-1/2 -mr-1 border-r border-t'
  };
  
  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onClick={() => setShow(!show)}
      >
        {children || (
          <button
            type="button"
            className="w-5 h-5 rounded-full bg-accent-100 text-accent-700 flex items-center justify-center text-xs font-bold hover:bg-accent-200 transition-colors cursor-help"
          >
            ?
          </button>
        )}
      </div>
      
      {show && (
        <div className={`absolute z-50 ${positionClasses[position]}`}>
          <div className="w-80 max-w-sm p-3 bg-white border border-border rounded-lg shadow-xl text-sm animate-fade-in">
            <div className={`absolute w-3 h-3 bg-white transform rotate-45 ${arrowClasses[position]}`} />
            <div className="relative z-10">
              {typeof content === 'string' ? (
                <p className="text-text-primary">{content}</p>
              ) : (
                content
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================
// INLINE HELP TEXT
// ============================================

interface HelpTextProps {
  children: ReactNode;
  type?: 'info' | 'tip' | 'warning';
}

export function HelpText({ children, type = 'info' }: HelpTextProps) {
  const styles = {
    info: 'bg-accent-50 border-accent-200 text-accent-800',
    tip: 'bg-success-light border-success text-success-dark',
    warning: 'bg-warning-light border-warning text-warning-dark'
  };
  
  const icons = {
    info: 'ℹ️',
    tip: '💡',
    warning: '⚠️'
  };
  
  return (
    <div className={`mt-2 p-3 border rounded-lg text-sm ${styles[type]}`}>
      <span className="mr-2">{icons[type]}</span>
      {children}
    </div>
  );
}

// ============================================
// EXPANDABLE EXAMPLES
// ============================================

interface ExampleProps {
  title: string;
  examples: Array<string | { label: string; text: string }>;
  defaultOpen?: boolean;
}

export function Examples({ title, examples, defaultOpen = false }: ExampleProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="text-sm text-accent-600 hover:text-accent-700 font-medium flex items-center gap-2 transition-colors"
      >
        <span className="transform transition-transform" style={{ transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)' }}>
          ▶
        </span>
        {title}
      </button>
      
      {isOpen && (
        <div className="mt-3 space-y-3 bg-primary-50 border border-primary-200 rounded-lg p-4 animate-slide-down">
          {examples.map((example, i) => (
            <div key={i} className="border-l-4 border-accent-500 pl-3">
              {typeof example === 'string' ? (
                <p className="text-sm text-text-secondary italic">"{example}"</p>
              ) : (
                <>
                  <p className="text-sm font-medium text-accent-700 mb-1">
                    {example.label}
                  </p>
                  <p className="text-sm text-text-secondary italic leading-relaxed">
                    "{example.text}"
                  </p>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================
// CHECKLIST COMPONENT
// ============================================

interface ChecklistProps {
  title: string;
  items: string[];
}

export function Checklist({ title, items }: ChecklistProps) {
  return (
    <div className="bg-accent-50 border border-accent-200 rounded-lg p-4">
      <p className="text-sm font-semibold text-accent-800 mb-3">
        {title}
      </p>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
            <span className="text-accent-600 font-bold mt-0.5">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ============================================
// FAQ ACCORDION
// ============================================

interface FAQItem {
  question: string;
  answer: string | ReactNode;
}

interface FAQProps {
  items: FAQItem[];
}

export function FAQ({ items }: FAQProps) {
  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <details key={i} className="group">
          <summary className="text-sm font-medium text-accent-600 cursor-pointer hover:text-accent-700 list-none flex items-center gap-2">
            <span className="transform transition-transform group-open:rotate-90">▶</span>
            {item.question}
          </summary>
          <div className="mt-2 pl-6 text-sm text-text-secondary">
            {typeof item.answer === 'string' ? (
              <p>{item.answer}</p>
            ) : (
              item.answer
            )}
          </div>
        </details>
      ))}
    </div>
  );
}

// ============================================
// SIDEBAR HELP PANEL
// ============================================

interface SidebarHelpProps {
  title: string;
  children: ReactNode;
}

export function SidebarHelp({ title, children }: SidebarHelpProps) {
  return (
    <div className="sidebar sticky top-24">
      <div className="sidebar-header">
        💡 {title}
      </div>
      <div className="p-6 space-y-4">
        {children}
      </div>
    </div>
  );
}

// ============================================
// USAGE EXAMPLES
// ============================================

/*
// Example 1: Simple tooltip
<Tooltip content="This is helpful information">
  <button>Hover me</button>
</Tooltip>

// Example 2: Info icon with tooltip
<div className="flex items-center gap-2">
  <label>Backstory</label>
  <Tooltip content="Provide comprehensive background information" />
</div>

// Example 3: Inline help text
<HelpText type="tip">
  Include both challenges AND strengths for a realistic simulation
</HelpText>

// Example 4: Expandable examples
<Examples
  title="See examples"
  examples={[
    "Example 1: Simple text",
    { label: "Clinical Example", text: "28-year-old with depression..." }
  ]}
/>

// Example 5: Checklist
<Checklist
  title="What to include:"
  items={[
    "Family background",
    "Early experiences",
    "Current symptoms"
  ]}
/>

// Example 6: FAQ
<FAQ
  items={[
    {
      question: "How much detail do I need?",
      answer: "More is better! Aim for 200-500 words."
    },
    {
      question: "Can I use real client info?",
      answer: "Only if de-identified!"
    }
  ]}
/>

// Example 7: Full sidebar
<SidebarHelp title="Quick Guide">
  <HelpText type="tip">
    Think of this as a client intake form
  </HelpText>
  
  <Checklist
    title="Essential Information"
    items={["Family", "Trauma", "Symptoms"]}
  />
  
  <FAQ items={faqItems} />
</SidebarHelp>
*/

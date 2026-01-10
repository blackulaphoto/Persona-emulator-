/**
 * Contextual Help System - Tooltips, Examples, and Guidance
 * 
 * Add to: frontend/components/PersonaForm.tsx or your creation page
 */

'use client';

import { useState } from 'react';

// Helper content for each field
const FIELD_HELPERS = {
  name: {
    tooltip: "The persona's name - can be real or fictional",
    examples: [
      "Ryan Myers",
      "Sarah Johnson",
      "Alex Chen"
    ],
    tips: "Use a realistic name that helps you remember the person"
  },
  
  age: {
    tooltip: "Current age of the persona (0-120)",
    examples: ["28", "15", "42"],
    tips: "This will be their age in the present day of the simulation"
  },
  
  gender: {
    tooltip: "Gender identity",
    examples: ["Male", "Female", "Non-binary", "Other"],
    tips: "Choose what's relevant for the case you're building"
  },
  
  backstory: {
    tooltip: "Comprehensive background information - the most important field!",
    examples: [
      {
        title: "Clinical Summary Example",
        text: "28-year-old male presenting with major depressive disorder. History of emotional neglect by alcoholic parents (ages 0-12). Father absent, mother emotionally unavailable. First depressive episode at age 15 following parental divorce. Struggled with substance use in college (ages 18-22). Currently in recovery (3 years sober) but experiencing relationship difficulties and low self-esteem. Seeking therapy for depression, anxiety, and attachment issues."
      },
      {
        title: "Developmental History Example",
        text: "15-year-old female raised in upper-middle-class family. Parents are high-achieving professionals with perfectionistic expectations. Early childhood was stable but emotionally cold - parents prioritized achievement over emotional connection. Excelled academically but developed severe anxiety around performance. Experienced bullying in middle school (ages 11-13) which parents dismissed as 'character building'. Recently developed eating disorder (restricting) as a way to control something in her life."
      },
      {
        title: "Trauma-Focused Example",
        text: "34-year-old male veteran. Grew up in stable, loving home. Deployed to Iraq at age 22, witnessed multiple casualties including death of close friend. Returned home at 23 with PTSD symptoms (nightmares, hypervigilance, flashbacks). Struggled to maintain relationships due to emotional numbing and irritability. Married at 26, divorced at 30 due to PTSD-related conflict. Currently experiencing increased symptoms after car accident triggered trauma memories."
      }
    ],
    whatToInclude: [
      "Family background and parenting style",
      "Early childhood experiences (0-6 years)",
      "Significant life events or trauma",
      "Developmental challenges or delays",
      "School/social experiences",
      "Medical or psychiatric history",
      "Current symptoms or concerns",
      "Strengths and protective factors"
    ],
    tips: "Think like a therapist taking an intake history. Include BOTH challenges AND strengths. The more detail here, the more accurate the simulation will be."
  }
};

// Tooltip component
function InfoTooltip({ content }: { content: string }) {
  const [show, setShow] = useState(false);
  
  return (
    <div className="relative inline-block ml-2">
      <button
        type="button"
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onClick={() => setShow(!show)}
        className="w-5 h-5 rounded-full bg-accent-100 text-accent-700 flex items-center justify-center text-xs font-bold hover:bg-accent-200 transition-colors"
      >
        ?
      </button>
      
      {show && (
        <div className="absolute z-50 w-80 p-3 bg-white border border-border rounded-lg shadow-xl left-0 top-6 text-sm animate-fade-in">
          <div className="absolute -top-2 left-3 w-4 h-4 bg-white border-t border-l border-border transform rotate-45" />
          <p className="text-text-primary">{content}</p>
        </div>
      )}
    </div>
  );
}

// Expandable examples section
function FieldExamples({ field }: { field: keyof typeof FIELD_HELPERS }) {
  const [showExamples, setShowExamples] = useState(false);
  const helper = FIELD_HELPERS[field];
  
  if (!helper.examples || helper.examples.length === 0) return null;
  
  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setShowExamples(!showExamples)}
        className="text-sm text-accent-600 hover:text-accent-700 font-medium flex items-center gap-1"
      >
        {showExamples ? '▼' : '▶'} See examples
      </button>
      
      {showExamples && (
        <div className="mt-2 space-y-3 bg-primary-50 border border-primary-200 rounded-lg p-4 animate-slide-down">
          {typeof helper.examples[0] === 'string' ? (
            // Simple string examples
            <div className="space-y-1">
              {(helper.examples as string[]).map((example, i) => (
                <div key={i} className="text-sm text-text-secondary">
                  <span className="text-accent-600 font-medium">Example {i + 1}:</span> {example}
                </div>
              ))}
            </div>
          ) : (
            // Complex examples with titles
            (helper.examples as Array<{title: string, text: string}>).map((example, i) => (
              <div key={i} className="border-l-4 border-accent-500 pl-3">
                <p className="font-medium text-sm text-accent-700 mb-1">
                  {example.title}
                </p>
                <p className="text-sm text-text-secondary italic leading-relaxed">
                  "{example.text}"
                </p>
              </div>
            ))
          )}
          
          {helper.tips && (
            <div className="pt-2 border-t border-primary-300">
              <p className="text-xs text-accent-700 font-medium mb-1">💡 Tip:</p>
              <p className="text-xs text-text-secondary">{helper.tips}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// "What to include" checklist for complex fields
function WhatToInclude({ items }: { items: string[] }) {
  return (
    <div className="mt-3 bg-accent-50 border border-accent-200 rounded-lg p-4">
      <p className="text-sm font-semibold text-accent-800 mb-2">
        📝 What to include:
      </p>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-text-secondary flex items-start gap-2">
            <span className="text-accent-600 mt-0.5">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// Main form with helpers
export function PersonaCreationFormWithHelpers() {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    backstory: ''
  });
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
      {/* Main Form - 3 columns */}
      <div className="lg:col-span-3">
        <form className="space-y-6">
          {/* Name Field */}
          <div>
            <div className="flex items-center">
              <label className="label mb-0">Name</label>
              <InfoTooltip content={FIELD_HELPERS.name.tooltip} />
            </div>
            <input
              type="text"
              className="input mt-2"
              placeholder="e.g., Ryan Myers"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
            <FieldExamples field="name" />
          </div>
          
          {/* Age Field */}
          <div>
            <div className="flex items-center">
              <label className="label mb-0">Age</label>
              <InfoTooltip content={FIELD_HELPERS.age.tooltip} />
            </div>
            <input
              type="number"
              className="input mt-2"
              placeholder="e.g., 28"
              value={formData.age}
              onChange={(e) => setFormData({...formData, age: e.target.value})}
            />
            <p className="text-xs text-text-tertiary mt-1">
              {FIELD_HELPERS.age.tips}
            </p>
          </div>
          
          {/* Gender Field */}
          <div>
            <div className="flex items-center">
              <label className="label mb-0">Gender</label>
              <InfoTooltip content={FIELD_HELPERS.gender.tooltip} />
            </div>
            <select
              className="input mt-2"
              value={formData.gender}
              onChange={(e) => setFormData({...formData, gender: e.target.value})}
            >
              <option value="">Select gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="non-binary">Non-binary</option>
              <option value="other">Other</option>
            </select>
          </div>
          
          {/* Backstory Field - THE BIG ONE */}
          <div>
            <div className="flex items-center">
              <label className="label mb-0">Backstory / Clinical Summary</label>
              <InfoTooltip content={FIELD_HELPERS.backstory.tooltip} />
            </div>
            
            <textarea
              className="input mt-2 min-h-[250px]"
              placeholder="Provide comprehensive background information..."
              value={formData.backstory}
              onChange={(e) => setFormData({...formData, backstory: e.target.value})}
            />
            
            {/* Character counter */}
            <div className="flex justify-between items-center mt-1">
              <span className="text-xs text-text-tertiary">
                {formData.backstory.length} / 2,000 characters
              </span>
              <span className="text-xs text-accent-600 font-medium">
                More detail = Better results
              </span>
            </div>
            
            {/* What to include checklist */}
            <WhatToInclude items={FIELD_HELPERS.backstory.whatToInclude} />
            
            {/* Examples */}
            <FieldExamples field="backstory" />
          </div>
          
          <button type="submit" className="btn btn-primary w-full">
            Create Persona
          </button>
        </form>
      </div>
      
      {/* Sidebar Guide - 1 column */}
      <div className="lg:col-span-1">
        <SidebarGuide currentField={getCurrentFocusedField()} />
      </div>
    </div>
  );
}

// Helper to detect which field is focused (for sidebar)
function getCurrentFocusedField() {
  // This would be more sophisticated in real implementation
  return 'backstory';
}

// Sidebar guide component
function SidebarGuide({ currentField }: { currentField?: string }) {
  return (
    <div className="sidebar sticky top-24">
      <div className="sidebar-header">
        💡 Quick Guide
      </div>
      
      <div className="p-6 space-y-4">
        <div className="bg-accent-50 border-l-4 border-accent-500 p-3 rounded">
          <p className="text-sm font-semibold text-accent-800 mb-1">
            Pro Tip
          </p>
          <p className="text-xs text-text-secondary">
            Think of this as writing a client intake form. Include both challenges AND strengths!
          </p>
        </div>
        
        <div>
          <h4 className="text-sm font-semibold text-text-primary mb-2">
            Essential Information
          </h4>
          <ul className="space-y-2 text-xs text-text-secondary">
            <li className="flex items-start gap-2">
              <span className="text-success">✓</span>
              <span>Family background & parenting</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-success">✓</span>
              <span>Early childhood experiences</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-success">✓</span>
              <span>Trauma or adversity</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-success">✓</span>
              <span>Current symptoms/concerns</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-success">✓</span>
              <span>Protective factors</span>
            </li>
          </ul>
        </div>
        
        <div className="border-t border-border pt-4">
          <h4 className="text-sm font-semibold text-text-primary mb-2">
            Common Questions
          </h4>
          
          <details className="mb-2">
            <summary className="text-xs font-medium text-accent-600 cursor-pointer hover:text-accent-700">
              How much detail do I need?
            </summary>
            <p className="text-xs text-text-secondary mt-1 pl-4">
              More is better! Aim for 200-500 words. Include specific ages, events, and contexts.
            </p>
          </details>
          
          <details className="mb-2">
            <summary className="text-xs font-medium text-accent-600 cursor-pointer hover:text-accent-700">
              Can I use real client info?
            </summary>
            <p className="text-xs text-text-secondary mt-1 pl-4">
              Only if de-identified! Change names, dates, and identifying details.
            </p>
          </details>
          
          <details className="mb-2">
            <summary className="text-xs font-medium text-accent-600 cursor-pointer hover:text-accent-700">
              What if I don't know everything?
            </summary>
            <p className="text-xs text-text-secondary mt-1 pl-4">
              That's okay! Fill in what you know. You can add experiences later.
            </p>
          </details>
        </div>
        
        <div className="bg-primary-50 border border-primary-200 rounded p-3">
          <p className="text-xs text-text-primary">
            <span className="font-semibold">New to this?</span> Try our{' '}
            <button className="text-accent-600 font-medium hover:underline">
              demo persona
            </button>{' '}
            first to see how it works!
          </p>
        </div>
      </div>
    </div>
  );
}

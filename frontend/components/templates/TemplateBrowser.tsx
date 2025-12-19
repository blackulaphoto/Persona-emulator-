/**
 * Template Browser Component - RESTYLED FOR CUSTOM DESIGN SYSTEM
 * 
 * Updated to match existing UI:
 * - Custom color palette (cream/clay/moss/sage/charcoal)
 * - Custom button classes (.btn-primary, .btn-secondary)
 * - Crimson Pro / Outfit fonts
 * - Warm, earthy aesthetic
 */
'use client';

import { useState, useEffect } from 'react';
import { templatesAPI, Template, APIError } from '@/lib/api/templates';

interface TemplateBrowserProps {
  onSelectTemplate: (templateId: string) => void;
}

export default function TemplateBrowser({ onSelectTemplate }: TemplateBrowserProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [disorderTypes, setDisorderTypes] = useState<string[]>([]);
  const [selectedDisorder, setSelectedDisorder] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [selectedDisorder]);

  async function loadData() {
    setLoading(true);
    setError(null);

    try {
      if (disorderTypes.length === 0) {
        const types = await templatesAPI.getDisorderTypes();
        setDisorderTypes(types);
      }

      const templateList = await templatesAPI.list(selectedDisorder || undefined);
      setTemplates(templateList);
    } catch (err) {
      if (err instanceof APIError && err.status === 404) {
        setError('Clinical templates feature is not enabled. Please contact your administrator.');
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load templates');
      }
    } finally {
      setLoading(false);
    }
  }

  function formatDisorderType(type: string): string {
    return type.replace(/_/g, ' ');
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-moss"></div>
        <span className="ml-3 text-sage font-['Outfit']">Loading templates...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-terracotta/10 border border-terracotta/30 rounded-xl p-6">
        <div className="flex items-start">
          <svg className="h-5 w-5 text-terracotta mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-charcoal font-['Outfit']">Error loading templates</h3>
            <p className="mt-1 text-sm text-sage font-['Outfit']">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with filter */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-charcoal font-['Crimson_Pro']">Clinical Templates</h2>
          <p className="mt-1 text-sm text-sage font-['Outfit']">
            Evidence-based disorder development pathways
          </p>
        </div>

        {/* Disorder type filter */}
        <div className="flex items-center space-x-3">
          <label className="text-sm font-medium text-charcoal font-['Outfit']">Filter:</label>
          <select
            value={selectedDisorder}
            onChange={(e) => setSelectedDisorder(e.target.value)}
            className="rounded-lg border-charcoal/20 bg-cream shadow-sm focus:border-moss focus:ring-moss font-['Outfit']"
          >
            <option value="">All Disorders</option>
            {disorderTypes.map((type) => (
              <option key={type} value={type}>
                {formatDisorderType(type)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Templates grid */}
      {templates.length === 0 ? (
        <div className="text-center py-12 bg-cream rounded-xl border border-charcoal/10">
          <svg className="mx-auto h-12 w-12 text-sage" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-charcoal font-['Outfit']">No templates found</h3>
          <p className="mt-1 text-sm text-sage font-['Outfit']">
            {selectedDisorder ? 'Try selecting a different disorder type.' : 'No templates available.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              onSelect={() => onSelectTemplate(template.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Individual template card component
interface TemplateCardProps {
  template: Template;
  onSelect: () => void;
}

function TemplateCard({ template, onSelect }: TemplateCardProps) {
  // Color scheme based on disorder type - using custom palette
  const getDisorderColor = (type: string) => {
    const colors: Record<string, string> = {
      'BPD': 'bg-terracotta/20 text-terracotta border-terracotta/30',
      'C-PTSD': 'bg-moss/20 text-moss border-moss/30',
      'Social_Anxiety': 'bg-sage/30 text-sage border-sage/40',
      'DID': 'bg-clay/50 text-charcoal border-clay',
      'MDD': 'bg-charcoal/10 text-charcoal border-charcoal/20',
    };
    return colors[type] || 'bg-clay/30 text-charcoal border-charcoal/20';
  };

  return (
    <div className="bg-cream border border-charcoal/10 rounded-xl shadow-sm hover:shadow-md transition-all overflow-hidden card-hover">
      {/* Disorder badge */}
      <div className="px-6 pt-6 pb-3">
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium font-['Outfit'] ${getDisorderColor(template.disorder_type)}`}>
          {template.disorder_type.replace(/_/g, ' ')}
        </span>
      </div>

      {/* Template info */}
      <div className="px-6 pb-6">
        <h3 className="text-lg font-semibold text-charcoal mb-2 font-['Crimson_Pro']">
          {template.name}
        </h3>
        <p className="text-sm text-sage line-clamp-3 mb-4 font-['Outfit']">
          {template.description}
        </p>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-charcoal font-['Crimson_Pro']">{template.experience_count}</div>
            <div className="text-xs text-sage font-['Outfit']">Experiences</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-charcoal font-['Crimson_Pro']">{template.intervention_count}</div>
            <div className="text-xs text-sage font-['Outfit']">Interventions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-charcoal font-['Crimson_Pro']">{template.remix_suggestion_count}</div>
            <div className="text-xs text-sage font-['Outfit']">Remixes</div>
          </div>
        </div>

        {/* Baseline age */}
        <div className="flex items-center text-sm text-sage mb-4 font-['Outfit']">
          <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Baseline age: {template.baseline_age} years
        </div>

        {/* View button - using custom btn-primary class */}
        <button
          onClick={onSelect}
          className="btn-primary w-full"
        >
          View Details
        </button>
      </div>
    </div>
  );
}



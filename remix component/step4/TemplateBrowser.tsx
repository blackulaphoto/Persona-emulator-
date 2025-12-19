/**
 * Template Browser Component
 * 
 * Displays list of clinical templates with filtering by disorder type.
 * User can view details and create personas from templates.
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

  // Load templates and disorder types on mount
  useEffect(() => {
    loadData();
  }, [selectedDisorder]);

  async function loadData() {
    setLoading(true);
    setError(null);

    try {
      // Load disorder types if not loaded
      if (disorderTypes.length === 0) {
        const types = await templatesAPI.getDisorderTypes();
        setDisorderTypes(types);
      }

      // Load templates (with optional filter)
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

  // Format disorder type for display
  function formatDisorderType(type: string): string {
    return type.replace(/_/g, ' ');
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Loading templates...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start">
          <svg className="h-5 w-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading templates</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
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
          <h2 className="text-2xl font-bold text-gray-900">Clinical Templates</h2>
          <p className="mt-1 text-sm text-gray-600">
            Evidence-based disorder development pathways
          </p>
        </div>

        {/* Disorder type filter */}
        <div className="flex items-center space-x-3">
          <label className="text-sm font-medium text-gray-700">Filter:</label>
          <select
            value={selectedDisorder}
            onChange={(e) => setSelectedDisorder(e.target.value)}
            className="rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
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
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No templates found</h3>
          <p className="mt-1 text-sm text-gray-500">
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
  // Color scheme based on disorder type
  const getDisorderColor = (type: string) => {
    const colors: Record<string, string> = {
      'BPD': 'bg-purple-100 text-purple-800 border-purple-200',
      'C-PTSD': 'bg-red-100 text-red-800 border-red-200',
      'Social_Anxiety': 'bg-blue-100 text-blue-800 border-blue-200',
      'DID': 'bg-indigo-100 text-indigo-800 border-indigo-200',
      'MDD': 'bg-gray-100 text-gray-800 border-gray-200',
    };
    return colors[type] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {/* Disorder badge */}
      <div className="px-6 pt-6 pb-3">
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${getDisorderColor(template.disorder_type)}`}>
          {template.disorder_type.replace(/_/g, ' ')}
        </span>
      </div>

      {/* Template info */}
      <div className="px-6 pb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {template.name}
        </h3>
        <p className="text-sm text-gray-600 line-clamp-3 mb-4">
          {template.description}
        </p>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{template.experience_count}</div>
            <div className="text-xs text-gray-500">Experiences</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{template.intervention_count}</div>
            <div className="text-xs text-gray-500">Interventions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{template.remix_suggestion_count}</div>
            <div className="text-xs text-gray-500">Remixes</div>
          </div>
        </div>

        {/* Baseline age */}
        <div className="flex items-center text-sm text-gray-600 mb-4">
          <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Baseline age: {template.baseline_age} years
        </div>

        {/* View button */}
        <button
          onClick={onSelect}
          className="w-full bg-blue-600 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          View Details
        </button>
      </div>
    </div>
  );
}

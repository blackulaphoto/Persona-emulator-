/**
 * Template Details Modal
 * 
 * Full-screen modal showing complete template information:
 * - Clinical rationale
 * - Baseline configuration
 * - All experiences
 * - Suggested interventions
 * - Expected outcomes
 * - Research citations
 * - Remix suggestions
 */
'use client';

import { useState, useEffect } from 'react';
import { templatesAPI, TemplateDetails, APIError } from '@/lib/api/templates';

interface TemplateDetailsModalProps {
  templateId: string;
  onClose: () => void;
  onCreatePersona: (templateId: string, templateName: string) => void;
}

export default function TemplateDetailsModal({
  templateId,
  onClose,
  onCreatePersona,
}: TemplateDetailsModalProps) {
  const [template, setTemplate] = useState<TemplateDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'experiences' | 'interventions' | 'outcomes' | 'research'>('overview');

  useEffect(() => {
    loadTemplate();
  }, [templateId]);

  async function loadTemplate() {
    setLoading(true);
    setError(null);

    try {
      const data = await templatesAPI.get(templateId);
      setTemplate(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load template');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading template...</p>
        </div>
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md">
          <h3 className="text-lg font-semibold text-red-900 mb-2">Error</h3>
          <p className="text-red-700 mb-4">{error || 'Template not found'}</p>
          <button
            onClick={onClose}
            className="w-full bg-gray-600 text-white rounded-lg px-4 py-2 hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                {template.disorder_type.replace(/_/g, ' ')}
              </span>
              <span className="text-sm text-gray-500">Baseline Age: {template.baseline_age}</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">{template.name}</h2>
            <p className="mt-1 text-sm text-gray-600">{template.description}</p>
          </div>
          <button
            onClick={onClose}
            className="ml-4 text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 px-6">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'experiences', label: `Experiences (${template.predefined_experiences.length})` },
              { id: 'interventions', label: `Interventions (${template.predefined_interventions?.length || 0})` },
              { id: 'outcomes', label: 'Expected Outcomes' },
              { id: 'research', label: 'Research' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {activeTab === 'overview' && <OverviewTab template={template} />}
          {activeTab === 'experiences' && <ExperiencesTab experiences={template.predefined_experiences} />}
          {activeTab === 'interventions' && <InterventionsTab interventions={template.predefined_interventions || []} />}
          {activeTab === 'outcomes' && <OutcomesTab outcomes={template.expected_outcomes} />}
          {activeTab === 'research' && <ResearchTab template={template} />}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 flex justify-between items-center bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:text-gray-900"
          >
            Close
          </button>
          <button
            onClick={() => onCreatePersona(template.id, template.name)}
            className="bg-blue-600 text-white rounded-lg px-6 py-2 font-medium hover:bg-blue-700 transition-colors"
          >
            Create Persona from Template
          </button>
        </div>
      </div>
    </div>
  );
}

// Tab Components

function OverviewTab({ template }: { template: TemplateDetails }) {
  return (
    <div className="space-y-6">
      {/* Clinical Rationale */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Clinical Rationale</h3>
        <p className="text-gray-700 leading-relaxed whitespace-pre-line">
          {template.clinical_rationale}
        </p>
      </section>

      {/* Baseline Configuration */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Baseline Configuration</h3>
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <div>
            <span className="text-sm font-medium text-gray-700">Age:</span>
            <span className="ml-2 text-sm text-gray-900">{template.baseline_age} years</span>
          </div>
          {template.baseline_gender && (
            <div>
              <span className="text-sm font-medium text-gray-700">Gender:</span>
              <span className="ml-2 text-sm text-gray-900">{template.baseline_gender}</span>
            </div>
          )}
          <div>
            <span className="text-sm font-medium text-gray-700">Attachment Style:</span>
            <span className="ml-2 text-sm text-gray-900">{template.baseline_attachment_style}</span>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-700 block mb-2">Background:</span>
            <p className="text-sm text-gray-900">{template.baseline_background}</p>
          </div>
        </div>
      </section>

      {/* Baseline Personality */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Baseline Personality (Big Five)</h3>
        <div className="space-y-3">
          {Object.entries(template.baseline_personality).map(([trait, value]) => (
            <div key={trait}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-gray-700 capitalize">{trait}</span>
                <span className="text-sm text-gray-600">{(value * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${value * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Remix Suggestions Preview */}
      {template.remix_suggestions && template.remix_suggestions.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Available Remix Scenarios</h3>
          <div className="space-y-2">
            {template.remix_suggestions.slice(0, 3).map((suggestion, idx) => (
              <div key={idx} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <h4 className="text-sm font-medium text-blue-900">{suggestion.title}</h4>
              </div>
            ))}
            {template.remix_suggestions.length > 3 && (
              <p className="text-sm text-gray-600 italic">
                +{template.remix_suggestions.length - 3} more remix suggestions
              </p>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

function ExperiencesTab({ experiences }: { experiences: TemplateDetails['predefined_experiences'] }) {
  return (
    <div className="space-y-4">
      {experiences.map((exp, idx) => (
        <div key={idx} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 text-sm font-semibold">
                {idx + 1}
              </span>
              <div>
                <span className="text-sm font-medium text-gray-900">Age {exp.age}</span>
                <span className="mx-2 text-gray-300">•</span>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  exp.valence === 'negative' ? 'bg-red-100 text-red-800' :
                  exp.valence === 'positive' ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {exp.category}
                </span>
              </div>
            </div>
            <span className={`text-xs px-2 py-1 rounded-full ${
              exp.intensity === 'severe' ? 'bg-red-100 text-red-800' :
              exp.intensity === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
              'bg-blue-100 text-blue-800'
            }`}>
              {exp.intensity}
            </span>
          </div>
          <p className="text-sm text-gray-700 mb-3">{exp.description}</p>
          {exp.clinical_note && (
            <div className="bg-purple-50 border-l-4 border-purple-400 p-3">
              <p className="text-xs text-purple-900">
                <span className="font-semibold">Clinical Note:</span> {exp.clinical_note}
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function InterventionsTab({ interventions }: { interventions: TemplateDetails['predefined_interventions'] }) {
  if (interventions.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No predefined interventions for this template.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {interventions.map((intv, idx) => (
        <div key={idx} className="border border-gray-200 rounded-lg p-4 bg-green-50">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h4 className="text-lg font-semibold text-gray-900">{intv.therapy_type}</h4>
              <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
                <span>Age {intv.age}</span>
                <span>•</span>
                <span>{intv.duration.replace(/_/g, ' ')}</span>
                <span>•</span>
                <span className="capitalize">{intv.intensity}</span>
              </div>
            </div>
          </div>
          <p className="text-sm text-gray-700">{intv.rationale}</p>
        </div>
      ))}
    </div>
  );
}

function OutcomesTab({ outcomes }: { outcomes: Record<string, any> }) {
  return (
    <div className="space-y-6">
      {Object.entries(outcomes).map(([scenarioKey, scenario]) => (
        <div key={scenarioKey} className="border border-gray-200 rounded-lg p-5">
          <h4 className="text-lg font-semibold text-gray-900 mb-4">
            {scenarioKey.replace(/_/g, ' ').replace(/age/i, 'Age')}
          </h4>
          
          {/* Personality outcome */}
          {scenario.personality && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 mb-2">Personality Profile</h5>
              <div className="grid grid-cols-5 gap-3">
                {Object.entries(scenario.personality).map(([trait, value]: [string, any]) => (
                  <div key={trait} className="text-center">
                    <div className="text-2xl font-bold text-gray-900">{(value * 100).toFixed(0)}</div>
                    <div className="text-xs text-gray-600 capitalize">{trait.slice(0, 4)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Symptoms */}
          {scenario.symptoms && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-700 mb-2">Symptoms Present</h5>
              <div className="flex flex-wrap gap-2">
                {scenario.symptoms.map((symptom: string, idx: number) => (
                  <span key={idx} className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">
                    {symptom.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Note */}
          {scenario.note && (
            <div className="bg-blue-50 border-l-4 border-blue-400 p-3">
              <p className="text-sm text-blue-900">{scenario.note}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function ResearchTab({ template }: { template: TemplateDetails }) {
  return (
    <div className="space-y-6">
      {/* Citations */}
      {template.citations && template.citations.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Research Citations</h3>
          <ol className="space-y-3">
            {template.citations.map((citation, idx) => (
              <li key={idx} className="text-sm text-gray-700 pl-6 relative">
                <span className="absolute left-0 font-medium text-gray-900">{idx + 1}.</span>
                {citation}
              </li>
            ))}
          </ol>
        </section>
      )}

      {/* Remix Suggestions */}
      {template.remix_suggestions && template.remix_suggestions.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Remix Suggestions ("What If" Scenarios)</h3>
          <div className="space-y-4">
            {template.remix_suggestions.map((suggestion, idx) => (
              <div key={idx} className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                <h4 className="font-semibold text-blue-900 mb-2">{suggestion.title}</h4>
                <div className="mb-3">
                  <p className="text-sm font-medium text-blue-800 mb-1">Changes:</p>
                  <ul className="list-disc list-inside space-y-1">
                    {suggestion.changes.map((change, cidx) => (
                      <li key={cidx} className="text-sm text-blue-700">{change}</li>
                    ))}
                  </ul>
                </div>
                <div className="bg-blue-100 border-l-4 border-blue-400 p-3">
                  <p className="text-sm text-blue-900">
                    <span className="font-semibold">Hypothesis:</span> {suggestion.hypothesis}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

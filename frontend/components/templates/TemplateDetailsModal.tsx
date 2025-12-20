/**
 * Template Details Modal - RESTYLED FOR CUSTOM DESIGN SYSTEM
 * 
 * Updated to match existing UI with cream/moss/sage palette
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
      <div className="fixed inset-0 bg-charcoal/50 flex items-center justify-center z-50">
        <div className="bg-cream rounded-xl p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-moss mx-auto"></div>
          <p className="mt-4 text-sage font-['Outfit']">Loading template...</p>
        </div>
      </div>
    );
  }

  if (error || !template) {
    return (
      <div className="fixed inset-0 bg-charcoal/50 flex items-center justify-center z-50">
        <div className="bg-cream rounded-xl p-8 max-w-md">
          <h3 className="text-lg font-semibold text-terracotta mb-2 font-['Crimson_Pro']">Error</h3>
          <p className="text-sage mb-4 font-['Outfit']">{error || 'Template not found'}</p>
          <button
            onClick={onClose}
            className="btn-secondary w-full"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-charcoal/50 flex items-center justify-center z-50 p-4">
      <div className="bg-cream rounded-xl shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b border-charcoal/10 px-6 py-4 flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-terracotta/20 text-terracotta font-['Outfit']">
                {template.disorder_type.replace(/_/g, ' ')}
              </span>
              <span className="text-sm text-sage font-['Outfit']">Baseline Age: {template.baseline_age}</span>
            </div>
            <h2 className="text-2xl font-bold text-charcoal font-['Crimson_Pro']">{template.name}</h2>
            <p className="mt-1 text-sm text-sage font-['Outfit']">{template.description}</p>
          </div>
          <button
            onClick={onClose}
            className="ml-4 text-sage hover:text-charcoal"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-charcoal/10 px-6">
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
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors font-['Outfit'] ${
                  activeTab === tab.id
                    ? 'border-moss text-moss'
                    : 'border-transparent text-sage hover:text-charcoal hover:border-charcoal/20'
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
        <div className="border-t border-charcoal/10 px-6 py-4 flex justify-between items-center bg-clay/20">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sage hover:text-charcoal font-['Outfit']"
          >
            Close
          </button>
          <button
            onClick={() => onCreatePersona(template.id, template.name)}
            className="btn-primary"
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
        <h3 className="text-lg font-semibold text-charcoal mb-3 font-['Crimson_Pro']">Clinical Rationale</h3>
        <p className="text-sage leading-relaxed whitespace-pre-line font-['Outfit']">
          {template.clinical_rationale}
        </p>
      </section>

      {/* Baseline Configuration */}
      <section>
        <h3 className="text-lg font-semibold text-charcoal mb-3 font-['Crimson_Pro']">Baseline Configuration</h3>
        <div className="bg-clay/20 rounded-xl p-4 space-y-3">
          <div>
            <span className="text-sm font-medium text-charcoal font-['Outfit']">Age:</span>
            <span className="ml-2 text-sm text-sage font-['Outfit']">{template.baseline_age} years</span>
          </div>
          {template.baseline_gender && (
            <div>
              <span className="text-sm font-medium text-charcoal font-['Outfit']">Gender:</span>
              <span className="ml-2 text-sm text-sage font-['Outfit']">{template.baseline_gender}</span>
            </div>
          )}
          <div>
            <span className="text-sm font-medium text-charcoal font-['Outfit']">Attachment Style:</span>
            <span className="ml-2 text-sm text-sage font-['Outfit']">{template.baseline_attachment_style}</span>
          </div>
          <div>
            <span className="text-sm font-medium text-charcoal block mb-2 font-['Outfit']">Background:</span>
            <p className="text-sm text-sage font-['Outfit']">{template.baseline_background}</p>
          </div>
        </div>
      </section>

      {/* Baseline Personality */}
      <section>
        <h3 className="text-lg font-semibold text-charcoal mb-3 font-['Crimson_Pro']">Baseline Personality (Big Five)</h3>
        <div className="space-y-3">
          {Object.entries(template.baseline_personality).map(([trait, value]) => (
            <div key={trait}>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-charcoal capitalize font-['Outfit']">{trait}</span>
                <span className="text-sm text-sage font-['Outfit']">{(value * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-clay/30 rounded-full h-2">
                <div
                  className="bg-moss h-2 rounded-full transition-all"
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
          <h3 className="text-lg font-semibold text-charcoal mb-3 font-['Crimson_Pro']">Available Remix Scenarios</h3>
          <div className="space-y-2">
            {template.remix_suggestions.slice(0, 3).map((suggestion, idx) => (
              <div key={idx} className="bg-sage/20 border border-sage/30 rounded-xl p-3">
                <h4 className="text-sm font-medium text-moss font-['Outfit']">{suggestion.title}</h4>
              </div>
            ))}
            {template.remix_suggestions.length > 3 && (
              <p className="text-sm text-sage italic font-['Outfit']">
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
        <div key={idx} className="border border-charcoal/10 rounded-xl p-4">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-moss/20 text-moss text-sm font-semibold font-['Outfit']">
                {idx + 1}
              </span>
              <div>
                <span className="text-sm font-medium text-charcoal font-['Outfit']">Age {exp.age}</span>
                <span className="mx-2 text-clay">•</span>
                <span className={`text-xs px-2 py-1 rounded-full font-['Outfit'] ${
                  exp.valence === 'negative' ? 'bg-terracotta/20 text-terracotta' :
                  exp.valence === 'positive' ? 'bg-sage/30 text-sage' :
                  'bg-clay/30 text-charcoal'
                }`}>
                  {exp.category}
                </span>
              </div>
            </div>
            <span className={`text-xs px-2 py-1 rounded-full font-['Outfit'] ${
              exp.intensity === 'severe' ? 'bg-terracotta/20 text-terracotta' :
              exp.intensity === 'moderate' ? 'bg-clay/50 text-charcoal' :
              'bg-sage/20 text-sage'
            }`}>
              {exp.intensity}
            </span>
          </div>
          <p className="text-sm text-sage mb-3 font-['Outfit']">{exp.description}</p>
          {exp.clinical_note && (
            <div className="bg-terracotta/10 border-l-4 border-terracotta p-3">
              <p className="text-xs text-charcoal font-['Outfit']">
                <span className="font-semibold">Clinical Note:</span> {exp.clinical_note}
              </p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function InterventionsTab({ interventions = [] }: { interventions?: TemplateDetails['predefined_interventions'] }) {
  if (interventions.length === 0) {
    return (
      <div className="text-center py-12 text-sage font-['Outfit']">
        No predefined interventions for this template.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {interventions.map((intv, idx) => (
        <div key={idx} className="border border-charcoal/10 rounded-xl p-4 bg-sage/10">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h4 className="text-lg font-semibold text-charcoal font-['Crimson_Pro']">{intv.therapy_type}</h4>
              <div className="flex items-center gap-3 mt-1 text-sm text-sage font-['Outfit']">
                <span>Age {intv.age}</span>
                <span>•</span>
                <span>{intv.duration.replace(/_/g, ' ')}</span>
                <span>•</span>
                <span className="capitalize">{intv.intensity}</span>
              </div>
            </div>
          </div>
          <p className="text-sm text-sage font-['Outfit']">{intv.rationale}</p>
        </div>
      ))}
    </div>
  );
}

function OutcomesTab({ outcomes }: { outcomes: Record<string, any> }) {
  return (
    <div className="space-y-6">
      {Object.entries(outcomes).map(([scenarioKey, scenario]) => (
        <div key={scenarioKey} className="border border-charcoal/10 rounded-xl p-5">
          <h4 className="text-lg font-semibold text-charcoal mb-4 font-['Crimson_Pro']">
            {scenarioKey.replace(/_/g, ' ').replace(/age/i, 'Age')}
          </h4>
          
          {/* Personality outcome */}
          {scenario.personality && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-charcoal mb-2 font-['Outfit']">Personality Profile</h5>
              <div className="grid grid-cols-5 gap-3">
                {Object.entries(scenario.personality).map(([trait, value]: [string, any]) => (
                  <div key={trait} className="text-center">
                    <div className="text-2xl font-bold text-charcoal font-['Crimson_Pro']">{(value * 100).toFixed(0)}</div>
                    <div className="text-xs text-sage capitalize font-['Outfit']">{trait.slice(0, 4)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Symptoms */}
          {scenario.symptoms && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-charcoal mb-2 font-['Outfit']">Symptoms Present</h5>
              <div className="flex flex-wrap gap-2">
                {scenario.symptoms.map((symptom: string, idx: number) => (
                  <span key={idx} className="px-2 py-1 bg-terracotta/20 text-terracotta rounded text-xs font-['Outfit']">
                    {symptom.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Note */}
          {scenario.note && (
            <div className="bg-sage/20 border-l-4 border-sage p-3">
              <p className="text-sm text-charcoal font-['Outfit']">{scenario.note}</p>
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
          <h3 className="text-lg font-semibold text-charcoal mb-3 font-['Crimson_Pro']">Research Citations</h3>
          <ol className="space-y-3">
            {template.citations.map((citation, idx) => (
              <li key={idx} className="text-sm text-sage pl-6 relative font-['Outfit']">
                <span className="absolute left-0 font-medium text-charcoal">{idx + 1}.</span>
                {citation}
              </li>
            ))}
          </ol>
        </section>
      )}

      {/* Remix Suggestions */}
      {template.remix_suggestions && template.remix_suggestions.length > 0 && (
        <section>
          <h3 className="text-lg font-semibold text-charcoal mb-3 font-['Crimson_Pro']">Remix Suggestions ("What If" Scenarios)</h3>
          <div className="space-y-4">
            {template.remix_suggestions.map((suggestion, idx) => (
              <div key={idx} className="border border-sage/30 rounded-xl p-4 bg-sage/10">
                <h4 className="font-semibold text-moss mb-2 font-['Outfit']">{suggestion.title}</h4>
                <div className="mb-3">
                  <p className="text-sm font-medium text-charcoal mb-1 font-['Outfit']">Changes:</p>
                  <ul className="list-disc list-inside space-y-1">
                    {suggestion.changes.map((change, cidx) => (
                      <li key={cidx} className="text-sm text-sage font-['Outfit']">{change}</li>
                    ))}
                  </ul>
                </div>
                <div className="bg-moss/20 border-l-4 border-moss p-3">
                  <p className="text-sm text-charcoal font-['Outfit']">
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



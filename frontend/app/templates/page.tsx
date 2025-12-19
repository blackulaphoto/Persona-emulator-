/**
 * Clinical Templates Page - RESTYLED FOR CUSTOM DESIGN SYSTEM
 * 
 * Updated with cream/moss/sage/charcoal palette to match existing UI
 */
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import TemplateBrowser from '@/components/templates/TemplateBrowser';
import TemplateDetailsModal from '@/components/templates/TemplateDetailsModal';
import { templatesAPI } from '@/lib/api/templates';

export default function TemplatesPage() {
  const router = useRouter();
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [creatingPersona, setCreatingPersona] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [createdPersona, setCreatedPersona] = useState<{
    id: string;
    name: string;
    templateName: string;
    experienceCount: number;
  } | null>(null);

  async function handleCreatePersona(templateId: string, templateName: string) {
    setCreatingPersona(true);
    setCreateError(null);

    try {
      const result = await templatesAPI.createPersona(templateId);
      
      setCreatedPersona({
        id: result.persona_id,
        name: result.persona_name,
        templateName: result.template_name,
        experienceCount: result.predefined_experiences_available,
      });
      
      setSelectedTemplateId(null);
      setShowSuccessModal(true);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create persona');
    } finally {
      setCreatingPersona(false);
    }
  }

  function handleViewPersona(personaId: string) {
    setShowSuccessModal(false);
    router.push(`/persona/${personaId}`);
  }

  function handleApplyExperiences(personaId: string) {
    setShowSuccessModal(false);
    // Navigate to persona page where user can apply experiences
    router.push(`/persona/${personaId}`);
  }

  return (
    <div className="min-h-screen bg-cream">
      {/* Header - matching existing page header style */}
      <header className="bg-cream/80 border-b border-charcoal/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-charcoal font-['Crimson_Pro']">Clinical Templates</h1>
              <p className="mt-1 text-sm text-sage font-['Outfit']">
                Evidence-based disorder development pathways for psychological research and education
              </p>
            </div>
            <button
              onClick={() => router.push('/')}
              className="flex items-center gap-2 px-4 py-2 text-sage hover:text-charcoal transition-colors font-['Outfit']"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Home
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TemplateBrowser onSelectTemplate={setSelectedTemplateId} />
      </main>

      {/* Template Details Modal */}
      {selectedTemplateId && (
        <TemplateDetailsModal
          templateId={selectedTemplateId}
          onClose={() => {
            setSelectedTemplateId(null);
            setCreateError(null);
          }}
          onCreatePersona={handleCreatePersona}
        />
      )}

      {/* Creating Persona Loading Modal */}
      {creatingPersona && (
        <div className="fixed inset-0 bg-charcoal/50 flex items-center justify-center z-50">
          <div className="bg-cream rounded-xl p-8 max-w-md">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-moss mx-auto"></div>
            <p className="mt-4 text-center text-sage font-['Outfit']">Creating persona from template...</p>
          </div>
        </div>
      )}

      {/* Success Modal */}
      {showSuccessModal && createdPersona && (
        <SuccessModal
          persona={createdPersona}
          onViewPersona={handleViewPersona}
          onApplyExperiences={handleApplyExperiences}
          onClose={() => setShowSuccessModal(false)}
        />
      )}

      {/* Error Display - Toast notification */}
      {createError && (
        <div className="fixed bottom-4 right-4 bg-terracotta/10 border border-terracotta/30 rounded-xl p-4 shadow-lg max-w-md z-50">
          <div className="flex items-start">
            <svg className="h-5 w-5 text-terracotta mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-terracotta font-['Outfit']">Failed to create persona</h3>
              <p className="mt-1 text-sm text-sage font-['Outfit']">{createError}</p>
            </div>
            <button
              onClick={() => setCreateError(null)}
              className="ml-4 text-sage hover:text-charcoal"
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Success Modal Component
interface SuccessModalProps {
  persona: {
    id: string;
    name: string;
    templateName: string;
    experienceCount: number;
  };
  onViewPersona: (id: string) => void;
  onApplyExperiences: (id: string) => void;
  onClose: () => void;
}

function SuccessModal({ persona, onViewPersona, onApplyExperiences, onClose }: SuccessModalProps) {
  return (
    <div className="fixed inset-0 bg-charcoal/50 flex items-center justify-center z-50 p-4">
      <div className="bg-cream rounded-xl shadow-xl max-w-lg w-full p-6">
        {/* Success icon */}
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-sage/30 rounded-full">
          <svg className="h-6 w-6 text-sage" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        {/* Content */}
        <div className="mt-4 text-center">
          <h3 className="text-lg font-semibold text-charcoal font-['Crimson_Pro']">Persona Created Successfully!</h3>
          <p className="mt-2 text-sm text-sage font-['Outfit']">
            "{persona.name}" has been created from the template "{persona.templateName}".
          </p>
        </div>

        {/* Info box */}
        <div className="mt-6 bg-sage/20 border border-sage/30 rounded-xl p-4">
          <div className="flex items-start">
            <svg className="h-5 w-5 text-sage mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="ml-3 flex-1">
              <h4 className="text-sm font-medium text-moss font-['Outfit']">Next Steps</h4>
              <p className="mt-1 text-sm text-charcoal font-['Outfit']">
                The persona has been created with the baseline configuration. You have <strong>{persona.experienceCount} predefined experiences</strong> available to apply.
              </p>
              <p className="mt-2 text-sm text-charcoal font-['Outfit']">
                You can apply these experiences all at once or manually add them one by one.
              </p>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 grid grid-cols-2 gap-3">
          <button
            onClick={() => onViewPersona(persona.id)}
            className="btn-secondary"
          >
            View Persona
          </button>
          <button
            onClick={() => onApplyExperiences(persona.id)}
            className="btn-primary"
          >
            View Persona
          </button>
        </div>

        {/* Close */}
        <div className="mt-4 text-center">
          <button
            onClick={onClose}
            className="text-sm text-sage hover:text-charcoal font-['Outfit']"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}


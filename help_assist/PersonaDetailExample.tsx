/**
 * EXAMPLE: Persona Detail Page with Complete Help System
 * 
 * This shows how to add help to your existing persona detail page
 */

'use client';

import { SectionHelp, TraitHelp, ButtonWithHelp, PageHelpBanner, QuickTip } from '@/components/PageHelpComponents';
import { Tooltip } from '@/components/HelpComponents';

export function PersonaDetailPageWithHelp({ persona }: { persona: any }) {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Page-level help banner */}
      <PageHelpBanner pageKey="personaDetail" />
      
      {/* Header with persona info */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-serif text-text-primary">{persona.name}</h1>
          <p className="text-text-secondary mt-1">
            Age {persona.age} • {persona.experiences.length} experiences • {persona.interventions.length} interventions
          </p>
        </div>
        
        <div className="flex gap-3">
          <ButtonWithHelp
            buttonText="+ Experience"
            helpKey="experience"
            onClick={() => {/* open modal */}}
          />
          <ButtonWithHelp
            buttonText="🔬 Therapy"
            helpKey="intervention"
            onClick={() => {/* open modal */}}
          />
          <ButtonWithHelp
            buttonText="📸 Save Snapshot"
            helpKey="snapshot"
            onClick={() => {/* save snapshot */}}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Big Five Personality - WITH HELP */}
        <div className="card">
          <SectionHelp title="Big Five Personality" helpKey="personaDetail.bigFive" />
          
          <div className="space-y-4 mt-4">
            {/* Openness */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <span className="text-sm font-medium text-text-primary">Openness</span>
                  <TraitHelp trait="openness" score={persona.openness} />
                </div>
                <span className="text-sm text-text-tertiary">{persona.openness}%</span>
              </div>
              <div className="w-full h-3 bg-primary-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-accent-500 transition-all"
                  style={{ width: `${persona.openness}%` }}
                />
              </div>
            </div>
            
            {/* Conscientiousness */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <span className="text-sm font-medium text-text-primary">Conscientiousness</span>
                  <TraitHelp trait="conscientiousness" score={persona.conscientiousness} />
                </div>
                <span className="text-sm text-text-tertiary">{persona.conscientiousness}%</span>
              </div>
              <div className="w-full h-3 bg-primary-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-success"
                  style={{ width: `${persona.conscientiousness}%` }}
                />
              </div>
            </div>
            
            {/* Extraversion */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <span className="text-sm font-medium text-text-primary">Extraversion</span>
                  <TraitHelp trait="extraversion" score={persona.extraversion} />
                </div>
                <span className="text-sm text-text-tertiary">{persona.extraversion}%</span>
              </div>
              <div className="w-full h-3 bg-primary-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-warning"
                  style={{ width: `${persona.extraversion}%` }}
                />
              </div>
            </div>
            
            {/* Agreeableness */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <span className="text-sm font-medium text-text-primary">Agreeableness</span>
                  <TraitHelp trait="agreeableness" score={persona.agreeableness} />
                </div>
                <span className="text-sm text-text-tertiary">{persona.agreeableness}%</span>
              </div>
              <div className="w-full h-3 bg-primary-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary-400"
                  style={{ width: `${persona.agreeableness}%` }}
                />
              </div>
            </div>
            
            {/* Neuroticism */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <span className="text-sm font-medium text-text-primary">Neuroticism</span>
                  <TraitHelp trait="neuroticism" score={persona.neuroticism} />
                </div>
                <span className="text-sm text-text-tertiary">{persona.neuroticism}%</span>
              </div>
              <div className="w-full h-3 bg-primary-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-text-primary"
                  style={{ width: `${persona.neuroticism}%` }}
                />
              </div>
            </div>
          </div>
          
          <div className="mt-4">
            <QuickTip tip="Hover over ? icons to understand each trait" />
          </div>
        </div>
        
        {/* Current Symptoms - WITH HELP */}
        <div className="card">
          <SectionHelp title="Current Symptoms" helpKey="personaDetail.symptoms" />
          
          {persona.symptoms.length > 0 ? (
            <div className="flex flex-wrap gap-2 mt-4">
              {persona.symptoms.map((symptom: any) => (
                <div key={symptom.id} className="relative group">
                  <div className="badge badge-primary cursor-pointer">
                    {symptom.name}
                  </div>
                  
                  {/* Hover tooltip with details */}
                  <div className="absolute z-50 hidden group-hover:block w-64 p-3 bg-white border border-border rounded-lg shadow-xl left-0 top-8">
                    <p className="text-sm font-medium text-text-primary mb-1">{symptom.name}</p>
                    <p className="text-xs text-text-secondary mb-2">
                      Severity: {(symptom.severity * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-text-secondary">
                      Onset: Age {symptom.onset_age}
                    </p>
                    {symptom.category && (
                      <p className="text-xs text-accent-600 mt-1">{symptom.category}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-4 text-center py-8">
              <p className="text-sm text-text-tertiary mb-2">No symptoms yet</p>
              <QuickTip tip="Add experiences to generate symptom profiles" type="info" />
            </div>
          )}
        </div>
      </div>
      
      {/* Timeline Section - WITH HELP */}
      <div className="card mt-6">
        <SectionHelp title="Evolution Timeline" helpKey="personaDetail.timeline" />
        
        {/* Timeline visualization */}
        <div className="mt-6">
          {/* Your timeline component here */}
        </div>
      </div>
      
      {/* Tabs: Timeline & Snapshots | Narrative */}
      <div className="mt-6">
        <div className="flex gap-4 border-b border-border">
          <button className="tab tab-active flex items-center gap-2">
            <span>Timeline & Snapshots</span>
            <Tooltip content="View experiences and captured psychological states over time" />
          </button>
          <button className="tab tab-inactive flex items-center gap-2">
            <span>Narrative</span>
            <Tooltip content="AI-generated comprehensive psychological report" />
          </button>
        </div>
        
        <div className="mt-6">
          {/* Tab content here */}
        </div>
      </div>
      
      {/* Chat Button - WITH HELP */}
      <div className="fixed bottom-6 right-6">
        <ButtonWithHelp
          buttonText="💬 Chat with {persona.name}"
          helpKey="chat"
          onClick={() => {/* open chat */}}
          variant="primary"
        />
      </div>
    </div>
  );
}

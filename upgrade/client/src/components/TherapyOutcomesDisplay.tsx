/**
 * TherapyOutcomesDisplay Component
 * Design: Empathetic Modernism - Comprehensive therapy outcomes visualization
 * Shows therapy details, measurable improvements with before/after comparisons
 */

import { TrendingUp, CheckCircle2, ArrowUpRight, Heart } from 'lucide-react';

interface TherapyOutcome {
  metric: string;
  improvement: number;
}

interface PersonalityChange {
  trait: string;
  before: number;
  after: number;
}

interface Symptom {
  name: string;
  severity: number;
}

interface TherapyOutcomesDisplayProps {
  therapyApproach?: string;
  sessionCount?: number;
  therapyOutcomes?: TherapyOutcome[];
  personalityChanges?: PersonalityChange[];
  symptoms?: Symptom[];
}

export default function TherapyOutcomesDisplay({ 
  therapyApproach, 
  sessionCount, 
  therapyOutcomes,
  personalityChanges,
  symptoms
}: TherapyOutcomesDisplayProps) {
  if (!therapyApproach && !sessionCount && (!therapyOutcomes || therapyOutcomes.length === 0)) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Heart className="w-5 h-5" style={{ color: 'var(--deep-purple)' }} />
        <h4 className="font-semibold text-lg">Therapeutic Journey & Outcomes</h4>
      </div>

      {/* Therapy Details Card */}
      <div 
        className="p-5 rounded-xl space-y-4 border-2"
        style={{ 
          backgroundColor: 'var(--light-lavender)',
          borderColor: 'var(--periwinkle)'
        }}
      >
        <div className="flex items-center gap-2 pb-2 border-b" style={{ borderColor: 'var(--periwinkle)' }}>
          <TrendingUp className="w-5 h-5" style={{ color: 'var(--deep-purple)' }} />
          <h5 className="font-semibold">Treatment Details</h5>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Therapy Approach */}
          {therapyApproach && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Approach</p>
              <p className="text-sm font-semibold">{therapyApproach}</p>
            </div>
          )}

          {/* Session Count */}
          {sessionCount && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Duration</p>
              <p className="text-sm font-semibold">{sessionCount} sessions</p>
            </div>
          )}
        </div>
      </div>

      {/* Measurable Improvements Section */}
      {therapyOutcomes && therapyOutcomes.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" style={{ color: 'var(--sage-green)' }} />
            <h5 className="font-semibold">Measurable Improvements</h5>
          </div>

          <div className="grid gap-3">
            {therapyOutcomes.map((outcome, index) => (
              <div 
                key={index} 
                className="p-4 rounded-lg border-l-4"
                style={{ 
                  backgroundColor: 'rgba(139, 195, 74, 0.05)',
                  borderLeftColor: 'var(--sage-green)'
                }}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{outcome.metric}</span>
                  <div className="flex items-center gap-1">
                    <ArrowUpRight className="w-4 h-4" style={{ color: 'var(--sage-green)' }} />
                    <span 
                      className="text-lg font-bold"
                      style={{ color: 'var(--sage-green)' }}
                    >
                      {outcome.improvement}%
                    </span>
                  </div>
                </div>
                
                {/* Progress Bar */}
                <div className="w-full h-2 rounded-full bg-gray-200">
                  <div 
                    className="h-full rounded-full transition-all duration-500"
                    style={{ 
                      width: `${outcome.improvement}%`,
                      backgroundColor: 'var(--sage-green)'
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Personality Changes Section */}
      {personalityChanges && personalityChanges.length > 0 && (
        <div className="space-y-3">
          <h5 className="font-semibold">Personality Trait Changes</h5>
          <div className="space-y-3">
            {personalityChanges.map((change, index) => {
              const difference = change.after - change.before;
              const isImprovement = difference > 0;
              
              return (
                <div key={index} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{change.trait}</span>
                    <span 
                      className="text-sm font-semibold"
                      style={{ color: isImprovement ? 'var(--sage-green)' : 'var(--muted-coral)' }}
                    >
                      {isImprovement ? '+' : ''}{difference} points
                    </span>
                  </div>
                  
                  {/* Before/After Comparison Bars */}
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground w-12">Before</span>
                      <div className="flex-1 h-2 rounded-full bg-gray-200">
                        <div 
                          className="h-full rounded-full"
                          style={{ 
                            width: `${change.before}%`,
                            backgroundColor: 'var(--muted-coral)'
                          }}
                        />
                      </div>
                      <span className="text-xs font-medium w-8 text-right">{change.before}%</span>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground w-12">After</span>
                      <div className="flex-1 h-2 rounded-full bg-gray-200">
                        <div 
                          className="h-full rounded-full"
                          style={{ 
                            width: `${change.after}%`,
                            backgroundColor: 'var(--sage-green)'
                          }}
                        />
                      </div>
                      <span className="text-xs font-medium w-8 text-right">{change.after}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Current Symptoms (if any) */}
      {symptoms && symptoms.length > 0 && (
        <div className="space-y-3">
          <h5 className="font-semibold">Current Status</h5>
          <div className="flex flex-wrap gap-2">
            {symptoms.map((symptom, index) => (
              <div 
                key={index}
                className="px-3 py-1.5 rounded-full text-sm"
                style={{ 
                  backgroundColor: 'var(--light-lavender)',
                  color: 'var(--deep-purple)'
                }}
              >
                {symptom.name}: {symptom.severity}/10
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Educational Note */}
      <div 
        className="p-4 rounded-lg border-l-4"
        style={{ 
          backgroundColor: 'rgba(103, 58, 183, 0.05)',
          borderLeftColor: 'var(--deep-purple)'
        }}
      >
        <p className="text-xs text-muted-foreground italic leading-relaxed">
          💡 <strong>Clinical Note:</strong> Therapeutic interventions during formative years can significantly 
          influence personality development and symptom reduction. The improvements shown reflect measurable 
          changes observed through evidence-based assessment tools and clinical observation.
        </p>
      </div>
    </div>
  );
}

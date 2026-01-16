/*
 * CurrentExperiences Component
 * Design: Empathetic Modernism - Reframe symptoms as human experiences
 * De-emphasize clinical terminology, focus on lived experience
 */

import { Heart } from 'lucide-react';
import type { Symptom } from '@/lib/mockData';

interface CurrentExperiencesProps {
  symptoms: Symptom[];
  personaName: string;
}

export default function CurrentExperiences({ symptoms, personaName }: CurrentExperiencesProps) {
  const getSeverityLabel = (severity: number): string => {
    if (severity >= 8) return 'Significantly';
    if (severity >= 6) return 'Moderately';
    if (severity >= 4) return 'Somewhat';
    return 'Mildly';
  };

  const getSeverityColor = (severity: number): string => {
    if (severity >= 8) return 'var(--muted-coral)';
    if (severity >= 6) return 'var(--warm-rose)';
    return 'var(--periwinkle)';
  };

  return (
    <div className="bg-card rounded-lg p-6 space-y-4" style={{ boxShadow: 'var(--shadow-sm)' }}>
      {/* Header */}
      <div className="flex items-start gap-3">
        <div 
          className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
          style={{ background: 'rgba(252, 129, 129, 0.15)' }}
        >
          <Heart className="w-5 h-5" style={{ color: 'var(--muted-coral)' }} />
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-foreground mb-1">
            What They're Experiencing
          </h3>
          <p className="text-sm text-muted-foreground">
            Current emotional and psychological challenges {personaName} is navigating
          </p>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-[var(--lavender)] bg-opacity-20 rounded-lg p-3 border border-[var(--lavender)]">
        <p className="text-xs text-foreground flex items-start gap-2">
          <span className="shrink-0 mt-0.5">ℹ️</span>
          <span>
            These experiences are generated based on {personaName}'s background and life events. 
            They reflect common psychological responses to their circumstances.
          </span>
        </p>
      </div>

      {/* Experiences List */}
      {symptoms.length > 0 ? (
        <div className="space-y-3">
          {symptoms.map((symptom, index) => (
            <div 
              key={index}
              className="flex items-center justify-between p-3 rounded-lg border border-border hover:border-[var(--muted-coral)] transition-colors"
              style={{ background: 'rgba(252, 129, 129, 0.05)' }}
            >
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-foreground mb-1">
                  {symptom.name}
                </h4>
                <p className="text-xs text-muted-foreground">
                  {getSeverityLabel(symptom.severity)} impacting daily life
                </p>
              </div>
              
              <div className="flex items-center gap-2">
                <div className="flex gap-0.5">
                  {Array.from({ length: 10 }).map((_, i) => (
                    <div
                      key={i}
                      className="w-1.5 h-6 rounded-full transition-all"
                      style={{
                        background: i < symptom.severity 
                          ? getSeverityColor(symptom.severity)
                          : 'var(--soft-gray)',
                        opacity: i < symptom.severity ? 1 : 0.3
                      }}
                    />
                  ))}
                </div>
                <span 
                  className="text-xs font-bold w-8 text-right"
                  style={{ color: getSeverityColor(symptom.severity) }}
                >
                  {symptom.severity}/10
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-muted-foreground">
          <p className="text-sm">No significant concerns at this time</p>
        </div>
      )}

      {/* Footer Note */}
      <div className="pt-4 border-t border-border">
        <p className="text-xs text-muted-foreground">
          <strong>Note:</strong> These are simulated experiences for educational purposes. 
          Real clinical assessment requires professional evaluation.
        </p>
      </div>
    </div>
  );
}

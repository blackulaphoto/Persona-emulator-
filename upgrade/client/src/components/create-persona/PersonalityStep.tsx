/*
 * PersonalityStep Component
 * Design: Empathetic Modernism - Interactive sliders with human descriptions
 */

import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { PersonaFormData } from '@/pages/CreatePersona';

interface PersonalityStepProps {
  formData: PersonaFormData;
  updateFormData: (data: Partial<PersonaFormData>) => void;
}

const PERSONALITY_TRAITS = [
  {
    key: 'openness' as keyof PersonaFormData,
    label: 'Openness',
    description: 'Curiosity and willingness to try new experiences',
    low: 'Prefers routine and familiar experiences',
    high: 'Highly curious and open to new experiences',
  },
  {
    key: 'conscientiousness' as keyof PersonaFormData,
    label: 'Conscientiousness',
    description: 'Organization, responsibility, and self-discipline',
    low: 'Spontaneous and flexible',
    high: 'Highly organized and disciplined',
  },
  {
    key: 'extraversion' as keyof PersonaFormData,
    label: 'Extraversion',
    description: 'Social energy and preference for interaction',
    low: 'Introverted, prefers solitude',
    high: 'Extraverted, energized by social interaction',
  },
  {
    key: 'agreeableness' as keyof PersonaFormData,
    label: 'Agreeableness',
    description: 'Cooperation, empathy, and trust in others',
    low: 'Skeptical and independent',
    high: 'Trusting and cooperative',
  },
  {
    key: 'emotionalSensitivity' as keyof PersonaFormData,
    label: 'Emotional Sensitivity',
    description: 'Tendency to experience negative emotions',
    low: 'Emotionally stable and resilient',
    high: 'Highly sensitive to stress and emotions',
  },
];

export default function PersonalityStep({ formData, updateFormData }: PersonalityStepProps) {
  const getDescription = (value: number, low: string, high: string) => {
    if (value < 35) return low;
    if (value > 65) return high;
    return 'Moderate - balanced between extremes';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Core Personality Tendencies
        </h2>
        <p className="text-sm text-muted-foreground">
          These traits are based on the Big Five personality model (OCEAN). They're relatively stable 
          but can shift with major life experiences.
        </p>
      </div>

      {/* Info Box */}
      <div className="bg-[var(--lavender)] bg-opacity-20 rounded-lg p-4 border border-[var(--lavender)]">
        <p className="text-sm text-foreground flex items-start gap-2">
          <span className="text-lg shrink-0">💡</span>
          <span>
            <strong>Remember:</strong> These are starting points, not fixed labels. Life experiences 
            will influence how these traits express themselves over time.
          </span>
        </p>
      </div>

      {/* Personality Sliders */}
      <div className="space-y-8">
        {PERSONALITY_TRAITS.map((trait) => {
          const value = formData[trait.key] as number;
          
          return (
            <div key={trait.key} className="space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <Label className="text-sm font-medium text-foreground">
                    {trait.label}
                  </Label>
                  <p className="text-xs text-muted-foreground mt-1">
                    {trait.description}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-lg font-bold text-foreground">{value}%</span>
                </div>
              </div>

              <Slider
                value={[value]}
                onValueChange={(values) => updateFormData({ [trait.key]: values[0] })}
                min={0}
                max={100}
                step={5}
                className="w-full"
              />

              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">{trait.low}</span>
                <span className="text-muted-foreground">{trait.high}</span>
              </div>

              <div className="bg-muted rounded-lg p-3">
                <p className="text-sm text-foreground">
                  <strong>Current:</strong> {getDescription(value, trait.low, trait.high)}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Note */}
      <div className="bg-muted rounded-lg p-4 text-center">
        <p className="text-xs text-muted-foreground italic">
          These percentages represent tendencies, not absolutes. A person at 60% extraversion 
          might still enjoy alone time, and someone at 40% might be social in comfortable settings.
        </p>
      </div>
    </div>
  );
}

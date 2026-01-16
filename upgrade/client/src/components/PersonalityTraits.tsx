/*
 * PersonalityTraits Component
 * Design: Empathetic Modernism - Present traits as patterns, not scores
 * Uses human descriptions and soft visual meters
 */

import { HelpCircle } from 'lucide-react';
import type { PersonalityTrait } from '@/lib/mockData';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface PersonalityTraitsProps {
  traits: PersonalityTrait[];
}

export default function PersonalityTraits({ traits }: PersonalityTraitsProps) {
  return (
    <div className="bg-card rounded-lg p-6 space-y-6" style={{ boxShadow: 'var(--shadow-sm)' }}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-xl font-bold text-foreground mb-1">
            Core Personality Tendencies
          </h3>
          <p className="text-sm text-muted-foreground">
            These patterns shape how they experience and respond to the world
          </p>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-[var(--lavender)] bg-opacity-20 rounded-lg p-3 border border-[var(--lavender)]">
        <p className="text-xs text-foreground flex items-start gap-2">
          <span className="shrink-0 mt-0.5">💡</span>
          <span>
            These traits are relatively stable but can shift with major life experiences. 
            They help us understand patterns, not predict every behavior.
          </span>
        </p>
      </div>

      {/* Traits List */}
      <div className="space-y-5">
        {traits.map((trait, index) => (
          <div key={index} className="space-y-2">
            {/* Trait Header */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-semibold text-foreground">
                  {trait.name}
                </h4>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <button className="text-muted-foreground hover:text-foreground transition-colors">
                        <HelpCircle className="w-4 h-4" />
                      </button>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <p className="text-xs">{trait.description}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <span className="text-sm font-medium text-foreground">
                {trait.value}%
              </span>
            </div>

            {/* Visual Meter */}
            <div className="personality-meter">
              <div 
                className="personality-meter-fill"
                style={{ width: `${trait.value}%` }}
              />
            </div>

            {/* Description */}
            <p className="text-xs text-muted-foreground">
              {trait.description}
            </p>
          </div>
        ))}
      </div>

      {/* Footer Note */}
      <div className="pt-4 border-t border-border">
        <p className="text-xs text-muted-foreground italic">
          Personality assessments provide insights but don't define a person completely. 
          Context, relationships, and experiences all play crucial roles.
        </p>
      </div>
    </div>
  );
}

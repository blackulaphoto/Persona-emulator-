/**
 * PersonalityEvolution Component
 * 
 * Design Philosophy: Empathetic Modernism
 * - Visualizes personality trait changes with before/after comparisons
 * - Uses color coding: green for growth, coral for decline
 * - Animated transitions to show change direction
 */

import { ArrowDown, ArrowUp, Minus } from 'lucide-react';

interface PersonalityChange {
  trait: string;
  before: number;
  after: number;
}

interface PersonalityEvolutionProps {
  changes: PersonalityChange[];
}

export default function PersonalityEvolution({ changes }: PersonalityEvolutionProps) {
  if (!changes || changes.length === 0) {
    return null;
  }

  const getChangeColor = (before: number, after: number) => {
    if (after > before) return 'text-sage-green';
    if (after < before) return 'text-muted-coral';
    return 'text-periwinkle';
  };

  const getChangeIcon = (before: number, after: number) => {
    if (after > before) return <ArrowUp className="w-4 h-4" />;
    if (after < before) return <ArrowDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  const getChangeLabel = (before: number, after: number) => {
    const diff = after - before;
    if (diff > 0) return `+${diff}%`;
    if (diff < 0) return `${diff}%`;
    return 'No change';
  };

  const getBarColor = (before: number, after: number) => {
    if (after > before) return 'bg-sage-green';
    if (after < before) return 'bg-muted-coral';
    return 'bg-periwinkle';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <div className="w-2 h-2 rounded-full bg-gradient-to-r from-primary to-accent" />
        <span>How this event shaped their personality</span>
      </div>

      <div className="space-y-4">
        {changes.map((change, index) => {
          const diff = change.after - change.before;
          const changeColor = getChangeColor(change.before, change.after);
          const barColor = getBarColor(change.before, change.after);

          return (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-foreground">
                  {change.trait}
                </span>
                <div className={`flex items-center gap-1 text-sm font-semibold ${changeColor}`}>
                  {getChangeIcon(change.before, change.after)}
                  <span>{getChangeLabel(change.before, change.after)}</span>
                </div>
              </div>

              {/* Before/After Comparison Bars */}
              <div className="space-y-1">
                {/* Before */}
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground w-12">Before</span>
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-muted-foreground/30 transition-all duration-500"
                      style={{ width: `${change.before}%` }}
                    />
                  </div>
                  <span className="text-xs text-muted-foreground w-10 text-right">
                    {change.before}%
                  </span>
                </div>

                {/* After */}
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground w-12">After</span>
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full ${barColor} transition-all duration-500`}
                      style={{ width: `${change.after}%` }}
                    />
                  </div>
                  <span className={`text-xs font-semibold w-10 text-right ${changeColor}`}>
                    {change.after}%
                  </span>
                </div>
              </div>

              {/* Change description */}
              <p className="text-xs text-muted-foreground italic">
                {diff > 0 && `Increased by ${diff} points - showing growth in this area`}
                {diff < 0 && `Decreased by ${Math.abs(diff)} points - reflecting the challenge's impact`}
                {diff === 0 && 'Remained stable through this experience'}
              </p>
            </div>
          );
        })}
      </div>

      {/* Summary note */}
      <div className="mt-6 p-3 bg-muted/50 rounded-lg border border-border/50">
        <p className="text-xs text-muted-foreground leading-relaxed">
          <span className="font-semibold text-foreground">Note:</span> These changes reflect 
          how life events can reshape personality patterns. While traits are relatively stable, 
          significant experiences—especially during formative years—can create lasting shifts 
          in how someone experiences and responds to the world.
        </p>
      </div>
    </div>
  );
}

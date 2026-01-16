/*
 * PersonaCard Component
 * Design: Empathetic Modernism - Clean card with purple accent, human-friendly labels
 * Shows persona as a life snapshot, not a database entry
 */

import { Link } from 'wouter';
import { User, Calendar, TrendingUp } from 'lucide-react';
import type { Persona } from '@/lib/mockData';

interface PersonaCardProps {
  persona: Persona;
}

export default function PersonaCard({ persona }: PersonaCardProps) {
  const initials = persona.name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <Link href={`/persona/${persona.id}`}>
      <div className="persona-card group cursor-pointer">
        {/* Avatar and Name */}
        <div className="flex items-start gap-4 mb-4">
          <div 
            className="w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-lg shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))' }}
          >
            {initials}
          </div>
          
          <div className="flex-1 min-w-0">
            <h3 className="text-xl font-bold text-foreground mb-1 group-hover:text-[var(--deep-purple)] transition-colors">
              {persona.name}
            </h3>
            <p className="text-sm text-muted-foreground italic">
              {persona.tagline}
            </p>
          </div>
        </div>

        {/* Metadata */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-4">
          <div className="flex items-center gap-1.5">
            <Calendar className="w-4 h-4" />
            <span>Age {persona.age}</span>
          </div>
          
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4" />
            <span>{persona.lifeEvents.length} life events</span>
          </div>
        </div>

        {/* Emotional Stability Indicator */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Emotional Well-being</span>
            <span className="font-medium text-foreground">{persona.emotionalStability}%</span>
          </div>
          <div className="personality-meter">
            <div 
              className="personality-meter-fill"
              style={{ width: `${persona.emotionalStability}%` }}
            />
          </div>
        </div>

        {/* Current Concerns */}
        {persona.currentSymptoms.length > 0 && (
          <div className="mt-4 pt-4 border-t border-border">
            <p className="text-xs text-muted-foreground mb-2">Currently navigating:</p>
            <div className="flex flex-wrap gap-2">
              {persona.currentSymptoms.slice(0, 3).map((symptom, idx) => (
                <span 
                  key={idx}
                  className="badge badge-coral text-xs"
                >
                  {symptom.name}
                </span>
              ))}
              {persona.currentSymptoms.length > 3 && (
                <span className="badge badge-purple text-xs">
                  +{persona.currentSymptoms.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </Link>
  );
}

/*
 * NarrativeView Component
 * Design: Empathetic Modernism - Present narrative as a story, not a clinical report
 * Clean typography with generous spacing and pull quotes
 */

import { BookOpen, Clock } from 'lucide-react';

interface NarrativeViewProps {
  narrative: string;
  personaName: string;
  age: number;
}

export default function NarrativeView({ narrative, personaName, age }: NarrativeViewProps) {
  // Calculate reading time (average 200 words per minute)
  const wordCount = narrative.split(/\s+/).length;
  const readingTime = Math.ceil(wordCount / 200);

  // Split narrative into paragraphs
  const paragraphs = narrative.split('\n\n').filter(p => p.trim());

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-card rounded-lg p-6" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <div className="flex items-start gap-4">
          <div 
            className="w-12 h-12 rounded-full flex items-center justify-center shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))' }}
          >
            <BookOpen className="w-6 h-6 text-white" />
          </div>
          
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-foreground mb-2">
              {personaName}'s Story
            </h2>
            <p className="text-sm text-muted-foreground mb-3">
              A comprehensive psychological summary generated from their life experiences
            </p>
            
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                <span>{readingTime} min read</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span>•</span>
                <span>{wordCount} words</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span>•</span>
                <span>Age {age}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-[var(--lavender)] bg-opacity-20 rounded-lg p-4 border border-[var(--lavender)]">
        <p className="text-sm text-foreground flex items-start gap-2">
          <span className="text-lg shrink-0">✨</span>
          <span>
            This narrative synthesizes {personaName}'s background, experiences, and psychological profile 
            into a cohesive story. It's designed to help understand their development holistically.
          </span>
        </p>
      </div>

      {/* Narrative Content */}
      <div className="bg-card rounded-lg p-8" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <article className="prose prose-slate max-w-none">
          {paragraphs.map((paragraph, index) => (
            <div key={index} className="mb-6 last:mb-0">
              <p className="text-base leading-relaxed text-foreground">
                {paragraph}
              </p>
              
              {/* Add subtle divider between paragraphs (except last) */}
              {index < paragraphs.length - 1 && (
                <div className="mt-6 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
              )}
            </div>
          ))}
        </article>
      </div>

      {/* Footer */}
      <div className="bg-card rounded-lg p-4 border border-border">
        <p className="text-xs text-muted-foreground text-center">
          <strong>Educational Tool:</strong> This narrative is generated for learning purposes. 
          Real psychological assessment requires professional clinical evaluation and should never 
          rely solely on automated analysis.
        </p>
      </div>
    </div>
  );
}

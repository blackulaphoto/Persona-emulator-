/*
 * BackgroundStep Component
 * Design: Empathetic Modernism - Comprehensive background collection with guidance
 */

import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { PersonaFormData } from '@/pages/CreatePersona';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';

interface BackgroundStepProps {
  formData: PersonaFormData;
  updateFormData: (data: Partial<PersonaFormData>) => void;
}

export default function BackgroundStep({ formData, updateFormData }: BackgroundStepProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Their Life Story
        </h2>
        <p className="text-sm text-muted-foreground">
          Provide comprehensive background information about their childhood, family, environment, 
          and experiences. This context helps understand their psychological development.
        </p>
      </div>

      {/* Pro Tip */}
      <div className="bg-[var(--lavender)] bg-opacity-20 rounded-lg p-4 border border-[var(--lavender)]">
        <p className="text-sm text-foreground flex items-start gap-2">
          <span className="text-lg shrink-0">💡</span>
          <span>
            <strong>Pro Tip:</strong> Include both challenges AND strengths! Mention supportive 
            relationships, coping skills, and positive experiences alongside difficulties.
          </span>
        </p>
      </div>

      {/* Main Background Story */}
      <div className="space-y-2">
        <Label htmlFor="backgroundStory" className="text-sm font-medium">
          Background Story <span className="text-red-500">*</span>
        </Label>
        <Textarea
          id="backgroundStory"
          placeholder="Provide a comprehensive overview of their life story, including key events, relationships, and circumstances that shaped who they are today..."
          value={formData.backgroundStory}
          onChange={(e) => updateFormData({ backgroundStory: e.target.value })}
          rows={6}
          className="text-base"
        />
        <p className="text-xs text-muted-foreground">
          A holistic summary that will appear on their persona overview
        </p>
      </div>

      {/* Essential Information Accordion */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">
          Essential Information
        </h3>
        <p className="text-xs text-muted-foreground mb-3">
          Expand each section to provide detailed context (optional but recommended)
        </p>

        <Accordion type="single" collapsible className="space-y-2">
          {/* Family Background */}
          <AccordionItem value="family" className="border rounded-lg px-4">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <span>👨‍👩‍👧‍👦</span>
                <span>Family Background & Parenting</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-3">
              <Textarea
                placeholder="Describe family structure, parenting style, sibling relationships, family dynamics, cultural background, socioeconomic status..."
                value={formData.familyBackground}
                onChange={(e) => updateFormData({ familyBackground: e.target.value })}
                rows={4}
                className="text-sm"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Who raised them? What was the home environment like? Any significant family events?
              </p>
            </AccordionContent>
          </AccordionItem>

          {/* Early Childhood */}
          <AccordionItem value="childhood" className="border rounded-lg px-4">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <span>🧸</span>
                <span>Early Childhood Experiences</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-3">
              <Textarea
                placeholder="Describe early developmental experiences, attachment patterns, school experiences, peer relationships, early trauma or adversity..."
                value={formData.earlyChildhood}
                onChange={(e) => updateFormData({ earlyChildhood: e.target.value })}
                rows={4}
                className="text-sm"
              />
              <p className="text-xs text-muted-foreground mt-2">
                What were their formative years like? Any significant events before age 10?
              </p>
            </AccordionContent>
          </AccordionItem>

          {/* Protective Factors */}
          <AccordionItem value="protective" className="border rounded-lg px-4">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              <div className="flex items-center gap-2">
                <span>🛡️</span>
                <span>Protective Factors & Strengths</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-3">
              <Textarea
                placeholder="Describe supportive relationships, coping skills, talents, interests, community connections, resilience factors..."
                value={formData.protectiveFactors}
                onChange={(e) => updateFormData({ protectiveFactors: e.target.value })}
                rows={4}
                className="text-sm"
              />
              <p className="text-xs text-muted-foreground mt-2">
                What helps them cope? Who supports them? What are their strengths?
              </p>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>

      {/* Common Questions */}
      <div className="bg-muted rounded-lg p-4">
        <h3 className="text-sm font-semibold text-foreground mb-2">Common Questions:</h3>
        <Accordion type="single" collapsible className="space-y-1">
          <AccordionItem value="detail" className="border-none">
            <AccordionTrigger className="text-xs font-medium py-2 hover:no-underline">
              How much detail should I include?
            </AccordionTrigger>
            <AccordionContent className="text-xs text-muted-foreground pb-2">
              Include enough to understand their context. A paragraph or two for the main story is 
              good. The detailed sections can be brief bullet points or fuller narratives—whatever 
              helps you remember the important context.
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="real" className="border-none">
            <AccordionTrigger className="text-xs font-medium py-2 hover:no-underline">
              Can I use real client information?
            </AccordionTrigger>
            <AccordionContent className="text-xs text-muted-foreground pb-2">
              If using real cases, always anonymize thoroughly. Change names, ages, locations, and 
              identifying details. This tool is for learning and case conceptualization, not record-keeping.
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="unknown" className="border-none">
            <AccordionTrigger className="text-xs font-medium py-2 hover:no-underline">
              What if I don't know all the details?
            </AccordionTrigger>
            <AccordionContent className="text-xs text-muted-foreground pb-2">
              That's okay! Include what you know and make reasonable assumptions based on typical 
              developmental patterns. You can always edit later as you learn more.
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </div>
  );
}

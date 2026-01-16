/*
 * InitialExperienceStep Component
 * Design: Empathetic Modernism - Optional first life event with clear guidance
 */

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { PersonaFormData } from '@/pages/CreatePersona';
import { Sparkles, Heart, AlertCircle } from 'lucide-react';

interface InitialExperienceStepProps {
  formData: PersonaFormData;
  updateFormData: (data: Partial<PersonaFormData>) => void;
}

export default function InitialExperienceStep({ formData, updateFormData }: InitialExperienceStepProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Add a First Life Event (Optional)
        </h2>
        <p className="text-sm text-muted-foreground">
          You can add an initial life experience now, or skip this and add events later. 
          This is useful if there's a significant event that shaped their current state.
        </p>
      </div>

      {/* Info Box */}
      <div className="bg-[var(--lavender)] bg-opacity-20 rounded-lg p-4 border border-[var(--lavender)]">
        <p className="text-sm text-foreground flex items-start gap-2">
          <span className="text-lg shrink-0">✨</span>
          <span>
            <strong>Optional Step:</strong> You can create the persona without any events and add 
            them later through the timeline interface. This is just a convenient starting point.
          </span>
        </p>
      </div>

      {/* Add Experience Toggle */}
      <div className="space-y-4">
        <Label className="text-sm font-medium">
          Would you like to add an initial life experience?
        </Label>
        
        <RadioGroup
          value={formData.hasInitialExperience ? 'yes' : 'no'}
          onValueChange={(value) => updateFormData({ hasInitialExperience: value === 'yes' })}
          className="grid grid-cols-2 gap-4"
        >
          <div>
            <RadioGroupItem value="no" id="no" className="peer sr-only" />
            <Label
              htmlFor="no"
              className="flex flex-col items-center justify-between rounded-lg border-2 border-muted bg-card p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-[var(--deep-purple)] cursor-pointer transition-all"
            >
              <Sparkles className="mb-3 h-6 w-6" />
              <span className="text-sm font-semibold">Skip for now</span>
              <span className="text-xs text-muted-foreground text-center mt-1">
                I'll add events later
              </span>
            </Label>
          </div>

          <div>
            <RadioGroupItem value="yes" id="yes" className="peer sr-only" />
            <Label
              htmlFor="yes"
              className="flex flex-col items-center justify-between rounded-lg border-2 border-muted bg-card p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-[var(--deep-purple)] cursor-pointer transition-all"
            >
              <Heart className="mb-3 h-6 w-6" />
              <span className="text-sm font-semibold">Add an event</span>
              <span className="text-xs text-muted-foreground text-center mt-1">
                Start with a key experience
              </span>
            </Label>
          </div>
        </RadioGroup>
      </div>

      {/* Experience Form (conditional) */}
      {formData.hasInitialExperience && (
        <div className="space-y-6 pt-4 border-t border-border">
          <h3 className="text-lg font-semibold text-foreground">
            Describe the Experience
          </h3>

          {/* Age and Type Row */}
          <div className="grid grid-cols-2 gap-4">
            {/* Age */}
            <div className="space-y-2">
              <Label htmlFor="experienceAge" className="text-sm font-medium">
                Age when it happened
              </Label>
              <Input
                id="experienceAge"
                type="number"
                min="0"
                max={formData.age}
                value={formData.experienceAge || ''}
                onChange={(e) => updateFormData({ experienceAge: parseInt(e.target.value) || undefined })}
                placeholder="e.g., 12"
                className="text-base"
              />
            </div>

            {/* Type */}
            <div className="space-y-2">
              <Label htmlFor="experienceType" className="text-sm font-medium">
                Type of experience
              </Label>
              <RadioGroup
                value={formData.experienceType || 'challenge'}
                onValueChange={(value: 'growth' | 'challenge') => updateFormData({ experienceType: value })}
                className="flex gap-4 pt-2"
              >
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="growth" id="growth" />
                  <Label htmlFor="growth" className="text-sm font-normal cursor-pointer flex items-center gap-1.5">
                    <Heart className="w-4 h-4 text-green-600" />
                    Growth
                  </Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="challenge" id="challenge" />
                  <Label htmlFor="challenge" className="text-sm font-normal cursor-pointer flex items-center gap-1.5">
                    <AlertCircle className="w-4 h-4 text-red-600" />
                    Challenge
                  </Label>
                </div>
              </RadioGroup>
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="experienceTitle" className="text-sm font-medium">
              Event Title
            </Label>
            <Input
              id="experienceTitle"
              placeholder="e.g., Parents' divorce, Started therapy, Lost a parent"
              value={formData.experienceTitle || ''}
              onChange={(e) => updateFormData({ experienceTitle: e.target.value })}
              className="text-base"
            />
            <p className="text-xs text-muted-foreground">
              A brief, descriptive title for the event
            </p>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="experienceDescription" className="text-sm font-medium">
              What happened?
            </Label>
            <Textarea
              id="experienceDescription"
              placeholder="Describe the experience in detail. What happened? How did it affect them? What changed?"
              value={formData.experienceDescription || ''}
              onChange={(e) => updateFormData({ experienceDescription: e.target.value })}
              rows={5}
              className="text-base"
            />
            <p className="text-xs text-muted-foreground">
              Provide context and details about the experience and its impact
            </p>
          </div>

          {/* Examples */}
          <div className="bg-muted rounded-lg p-4">
            <h4 className="text-sm font-semibold text-foreground mb-2">Examples:</h4>
            <div className="space-y-2 text-sm text-muted-foreground">
              <div className="flex items-start gap-2">
                <Heart className="w-4 h-4 text-green-600 mt-0.5 shrink-0" />
                <div>
                  <strong>Growth:</strong> "Started therapy at age 14 after parents' divorce. 
                  Learned healthy coping strategies and began processing emotions."
                </div>
              </div>
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 shrink-0" />
                <div>
                  <strong>Challenge:</strong> "Father died suddenly in car accident at age 7. 
                  Experienced profound grief and developed anxiety about losing other loved ones."
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer Note */}
      <div className="bg-card rounded-lg p-4 border border-border">
        <p className="text-xs text-muted-foreground text-center">
          <strong>Remember:</strong> You can always add, edit, or remove life events later through 
          the timeline interface. This is just a starting point.
        </p>
      </div>
    </div>
  );
}

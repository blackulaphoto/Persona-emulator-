/*
 * BasicInfoStep Component
 * Design: Empathetic Modernism - Simple, clear form with helpful guidance
 */

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { PersonaFormData } from '@/pages/CreatePersona';

interface BasicInfoStepProps {
  formData: PersonaFormData;
  updateFormData: (data: Partial<PersonaFormData>) => void;
}

export default function BasicInfoStep({ formData, updateFormData }: BasicInfoStepProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Let's Start with the Basics
        </h2>
        <p className="text-sm text-muted-foreground">
          Think of this as creating a character profile. Include both their challenges and strengths 
          to create a well-rounded persona.
        </p>
      </div>

      {/* Pro Tip */}
      <div className="bg-[var(--lavender)] bg-opacity-20 rounded-lg p-4 border border-[var(--lavender)]">
        <p className="text-sm text-foreground flex items-start gap-2">
          <span className="text-lg shrink-0">💡</span>
          <span>
            <strong>Pro Tip:</strong> Think of this as writing a client intake form. Include both 
            challenges AND strengths! A well-rounded persona helps understand the full picture.
          </span>
        </p>
      </div>

      {/* Form Fields */}
      <div className="space-y-6">
        {/* Name */}
        <div className="space-y-2">
          <Label htmlFor="name" className="text-sm font-medium">
            Name <span className="text-red-500">*</span>
          </Label>
          <Input
            id="name"
            placeholder="e.g., Emma, Alex, Jordan"
            value={formData.name}
            onChange={(e) => updateFormData({ name: e.target.value })}
            className="text-base"
          />
          <p className="text-xs text-muted-foreground">
            Choose a name that feels right for this persona
          </p>
        </div>

        {/* Age and Gender Row */}
        <div className="grid grid-cols-2 gap-4">
          {/* Baseline Age */}
          <div className="space-y-2">
            <Label htmlFor="age" className="text-sm font-medium">
              Baseline Age <span className="text-red-500">*</span>
            </Label>
            <Input
              id="age"
              type="number"
              min="1"
              max="100"
              value={formData.age}
              onChange={(e) => updateFormData({ age: parseInt(e.target.value) || 10 })}
              className="text-base"
            />
            <p className="text-xs text-muted-foreground">
              Their current age in your simulation
            </p>
          </div>

          {/* Gender */}
          <div className="space-y-2">
            <Label htmlFor="gender" className="text-sm font-medium">
              Gender
            </Label>
            <Select value={formData.gender} onValueChange={(value) => updateFormData({ gender: value })}>
              <SelectTrigger id="gender">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="female">Female</SelectItem>
                <SelectItem value="male">Male</SelectItem>
                <SelectItem value="non-binary">Non-binary</SelectItem>
                <SelectItem value="other">Other</SelectItem>
                <SelectItem value="prefer-not-to-say">Prefer not to say</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Tagline */}
        <div className="space-y-2">
          <Label htmlFor="tagline" className="text-sm font-medium">
            Tagline <span className="text-red-500">*</span>
          </Label>
          <Textarea
            id="tagline"
            placeholder="e.g., Learning to trust again, Navigating loss and instability, Finding strength through adversity"
            value={formData.tagline}
            onChange={(e) => updateFormData({ tagline: e.target.value })}
            rows={2}
            className="text-base resize-none"
          />
          <p className="text-xs text-muted-foreground">
            A brief phrase that captures their current journey (shown on persona card)
          </p>
        </div>
      </div>

      {/* Examples Section */}
      <div className="bg-muted rounded-lg p-4">
        <h3 className="text-sm font-semibold text-foreground mb-2">Examples:</h3>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li className="flex items-start gap-2">
            <span className="shrink-0">•</span>
            <span><strong>Emma, 15:</strong> "Learning to trust again" - Navigating parental divorce</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="shrink-0">•</span>
            <span><strong>Marcus, 28:</strong> "Building resilience after trauma" - Processing combat-related PTSD</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="shrink-0">•</span>
            <span><strong>Sofia, 42:</strong> "Rediscovering herself" - Life transitions and identity exploration</span>
          </li>
        </ul>
      </div>
    </div>
  );
}

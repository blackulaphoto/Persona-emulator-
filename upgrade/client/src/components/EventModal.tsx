/**
 * Design: Empathetic Modernism - Modal for adding/editing life events
 * Purple accent buttons, human-friendly form labels, clear validation
 */

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { X, Heart, AlertTriangle, Sparkles, TrendingUp } from 'lucide-react';
import type { LifeEvent } from '@/lib/mockData';

interface EventModalProps {
  open: boolean;
  onClose: () => void;
  onSave: (event: LifeEvent) => void;
  event?: LifeEvent | null;
  currentAge: number;
}

export default function EventModal({ open, onClose, onSave, event, currentAge }: EventModalProps) {
  const [formData, setFormData] = useState<Partial<LifeEvent>>({
    age: currentAge,
    title: '',
    description: '',
    type: 'challenge',
    impact: '',
    personalityChanges: [],
    symptoms: [],
    therapyApproach: '',
    sessionCount: undefined,
    therapyOutcomes: []
  });

  const [newSymptom, setNewSymptom] = useState({ name: '', severity: 5 });
  const [newPersonalityChange, setNewPersonalityChange] = useState({ trait: '', before: 50, after: 50 });

  useEffect(() => {
    if (event) {
      setFormData(event);
    } else {
      setFormData({
        age: currentAge,
        title: '',
        description: '',
        type: 'challenge',
        impact: '',
        personalityChanges: [],
        symptoms: [],
        therapyApproach: '',
        sessionCount: undefined,
        therapyOutcomes: []
      });
    }
  }, [event, currentAge, open]);

  const handleSave = () => {
    if (!formData.title || !formData.description) {
      return;
    }

    const eventToSave: LifeEvent = {
      id: event?.id || `event-${Date.now()}`,
      age: formData.age || currentAge,
      title: formData.title,
      description: formData.description,
      type: formData.type || 'challenge',
      impact: formData.impact || formData.description,
      personalityChanges: formData.personalityChanges || [],
      symptoms: formData.symptoms || [],
      ...(formData.type === 'therapy' && {
        therapyApproach: formData.therapyApproach,
        sessionCount: formData.sessionCount,
        therapyOutcomes: formData.therapyOutcomes
      })
    };

    onSave(eventToSave);
    onClose();
  };

  const addSymptom = () => {
    if (!newSymptom.name.trim()) return;
    
    setFormData(prev => ({
      ...prev,
      symptoms: [...(prev.symptoms || []), { ...newSymptom }]
    }));
    setNewSymptom({ name: '', severity: 5 });
  };

  const removeSymptom = (index: number) => {
    setFormData(prev => ({
      ...prev,
      symptoms: prev.symptoms?.filter((_, i) => i !== index) || []
    }));
  };

  const addPersonalityChange = () => {
    if (!newPersonalityChange.trait.trim()) return;
    
    setFormData(prev => ({
      ...prev,
      personalityChanges: [...(prev.personalityChanges || []), { ...newPersonalityChange }]
    }));
    setNewPersonalityChange({ trait: '', before: 50, after: 50 });
  };

  const removePersonalityChange = (index: number) => {
    setFormData(prev => ({
      ...prev,
      personalityChanges: prev.personalityChanges?.filter((_, i) => i !== index) || []
    }));
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold" style={{ color: 'var(--deep-purple)' }}>
            {event ? 'Edit Life Event' : 'Add Life Event'}
          </DialogTitle>
          <DialogDescription>
            Document a significant experience that shaped this persona's psychological development.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Age */}
          <div>
            <Label htmlFor="event-age" className="text-sm font-semibold mb-2 block">
              Age when this occurred *
            </Label>
            <Input
              id="event-age"
              type="number"
              min={0}
              max={120}
              value={formData.age}
              onChange={(e) => setFormData(prev => ({ ...prev, age: parseInt(e.target.value) || 0 }))}
              className="max-w-[120px]"
            />
          </div>

          {/* Event Type */}
          <div>
            <Label htmlFor="event-type" className="text-sm font-semibold mb-2 block">
              Event Type *
            </Label>
            <Select 
              value={formData.type} 
              onValueChange={(value: 'growth' | 'challenge' | 'therapy') => setFormData(prev => ({ ...prev, type: value }))}
            >
              <SelectTrigger id="event-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="challenge">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-500" />
                    <span>Challenge - Difficult experience</span>
                  </div>
                </SelectItem>
                <SelectItem value="growth">
                  <div className="flex items-center gap-2">
                    <Heart className="w-4 h-4 text-green-500" />
                    <span>Growth - Positive development</span>
                  </div>
                </SelectItem>
                <SelectItem value="therapy">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" style={{ color: 'var(--deep-purple)' }} />
                    <span>Therapy - Therapeutic intervention</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Title */}
          <div>
            <Label htmlFor="event-title" className="text-sm font-semibold mb-2 block">
              Event Title *
            </Label>
            <Input
              id="event-title"
              placeholder="e.g., Loss of a parent, Starting therapy, Moving to new city"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
            />
            <p className="text-xs text-muted-foreground mt-1">
              A brief, clear description of what happened
            </p>
          </div>

          {/* Description */}
          <div>
            <Label htmlFor="event-description" className="text-sm font-semibold mb-2 block">
              Detailed Description *
            </Label>
            <Textarea
              id="event-description"
              placeholder="Describe the event and its context. What happened? Who was involved? What was the immediate impact?"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={4}
            />
          </div>

          {/* Therapy-Specific Fields */}
          {formData.type === 'therapy' && (
            <div className="border rounded-lg p-4" style={{ backgroundColor: 'var(--light-lavender)', borderColor: 'var(--deep-purple)' }}>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5" style={{ color: 'var(--deep-purple)' }} />
                <h3 className="font-semibold" style={{ color: 'var(--deep-purple)' }}>Therapy Details</h3>
              </div>

              {/* Therapy Approach */}
              <div className="mb-4">
                <Label htmlFor="therapy-approach" className="text-sm font-semibold mb-2 block">
                  Therapy Approach
                </Label>
                <Select 
                  value={formData.therapyApproach} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, therapyApproach: value }))}
                >
                  <SelectTrigger id="therapy-approach">
                    <SelectValue placeholder="Select therapy type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CBT">Cognitive Behavioral Therapy (CBT)</SelectItem>
                    <SelectItem value="DBT">Dialectical Behavior Therapy (DBT)</SelectItem>
                    <SelectItem value="Psychodynamic">Psychodynamic Therapy</SelectItem>
                    <SelectItem value="EMDR">Eye Movement Desensitization (EMDR)</SelectItem>
                    <SelectItem value="Family">Family Therapy</SelectItem>
                    <SelectItem value="Group">Group Therapy</SelectItem>
                    <SelectItem value="Play">Play Therapy</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Session Count */}
              <div>
                <Label htmlFor="session-count" className="text-sm font-semibold mb-2 block">
                  Number of Sessions
                </Label>
                <Input
                  id="session-count"
                  type="number"
                  min={1}
                  placeholder="e.g., 12"
                  value={formData.sessionCount || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, sessionCount: parseInt(e.target.value) || undefined }))}
                  className="max-w-[150px]"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Total or ongoing session count
                </p>
              </div>
            </div>
          )}

          {/* Personality Changes Section */}
          <div className="border-t pt-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-5 h-5" style={{ color: 'var(--deep-purple)' }} />
              <h3 className="font-semibold">Personality Evolution</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Track how this event shaped personality traits (optional)
            </p>

            {/* Existing Personality Changes */}
            {formData.personalityChanges && formData.personalityChanges.length > 0 && (
              <div className="space-y-2 mb-4">
                {formData.personalityChanges.map((change, index) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg"
                    style={{ backgroundColor: 'var(--light-lavender)' }}
                  >
                    <div className="flex-1">
                      <span className="font-medium">{change.trait}</span>
                      <span className="text-sm text-muted-foreground ml-2">
                        {change.before}% → {change.after}%
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removePersonalityChange(index)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Add New Personality Change */}
            <div className="space-y-3 p-4 rounded-lg border">
              <div>
                <Label htmlFor="trait-name" className="text-sm mb-2 block">
                  Personality Trait
                </Label>
                <Input
                  id="trait-name"
                  placeholder="e.g., Emotional Stability, Trust, Openness"
                  value={newPersonalityChange.trait}
                  onChange={(e) => setNewPersonalityChange(prev => ({ ...prev, trait: e.target.value }))}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="before-value" className="text-sm mb-2 block">
                    Before: {newPersonalityChange.before}%
                  </Label>
                  <Slider
                    id="before-value"
                    min={0}
                    max={100}
                    step={5}
                    value={[newPersonalityChange.before]}
                    onValueChange={(value) => setNewPersonalityChange(prev => ({ ...prev, before: value[0] }))}
                  />
                </div>
                <div>
                  <Label htmlFor="after-value" className="text-sm mb-2 block">
                    After: {newPersonalityChange.after}%
                  </Label>
                  <Slider
                    id="after-value"
                    min={0}
                    max={100}
                    step={5}
                    value={[newPersonalityChange.after]}
                    onValueChange={(value) => setNewPersonalityChange(prev => ({ ...prev, after: value[0] }))}
                  />
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={addPersonalityChange}
                disabled={!newPersonalityChange.trait.trim()}
              >
                Add Personality Change
              </Button>
            </div>
          </div>

          {/* Symptoms Section */}
          <div className="border-t pt-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5" style={{ color: 'var(--deep-purple)' }} />
              <h3 className="font-semibold">What They Were Experiencing</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Add symptoms or challenges they faced during this time (optional)
            </p>

            {/* Existing Symptoms */}
            {formData.symptoms && formData.symptoms.length > 0 && (
              <div className="space-y-2 mb-4">
                {formData.symptoms.map((symptom, index) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg"
                    style={{ backgroundColor: 'var(--light-lavender)' }}
                  >
                    <div className="flex-1">
                      <span className="font-medium">{symptom.name}</span>
                      <span className="text-sm text-muted-foreground ml-2">
                        Severity: {symptom.severity}/10
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeSymptom(index)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Add New Symptom */}
            <div className="space-y-3 p-4 rounded-lg border">
              <div>
                <Label htmlFor="symptom-name" className="text-sm mb-2 block">
                  Symptom or Challenge
                </Label>
                <Input
                  id="symptom-name"
                  placeholder="e.g., Anxiety, Sleep disruption, Trust issues"
                  value={newSymptom.name}
                  onChange={(e) => setNewSymptom(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="symptom-severity" className="text-sm mb-2 block">
                  Severity: {newSymptom.severity}/10
                </Label>
                <Slider
                  id="symptom-severity"
                  min={1}
                  max={10}
                  step={1}
                  value={[newSymptom.severity]}
                  onValueChange={(value) => setNewSymptom(prev => ({ ...prev, severity: value[0] }))}
                />
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={addSymptom}
                disabled={!newSymptom.name.trim()}
              >
                Add Symptom
              </Button>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!formData.title || !formData.description}
            style={{
              background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))',
              color: 'white'
            }}
          >
            {event ? 'Save Changes' : 'Add Event'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

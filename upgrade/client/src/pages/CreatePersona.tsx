/*
 * CreatePersona Page
 * Design: Empathetic Modernism - Multi-step form with progressive disclosure
 * Guides users through persona creation with helpful tips
 */

import { useState } from 'react';
import { Link, useLocation } from 'wouter';
import { ArrowLeft, ArrowRight, Check, User, Brain, Calendar, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import BasicInfoStep from '@/components/create-persona/BasicInfoStep';
import PersonalityStep from '@/components/create-persona/PersonalityStep';
import BackgroundStep from '@/components/create-persona/BackgroundStep';
import InitialExperienceStep from '@/components/create-persona/InitialExperienceStep';
import { toast } from 'sonner';

export interface PersonaFormData {
  // Basic Info
  name: string;
  age: number;
  gender: string;
  tagline: string;
  
  // Personality Traits
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  emotionalSensitivity: number;
  
  // Background
  backgroundStory: string;
  familyBackground: string;
  earlyChildhood: string;
  protectiveFactors: string;
  
  // Initial Experience (optional)
  hasInitialExperience: boolean;
  experienceAge?: number;
  experienceType?: 'growth' | 'challenge';
  experienceTitle?: string;
  experienceDescription?: string;
}

const STEPS = [
  { id: 1, title: 'Basic Info', icon: User, description: 'Name, age, and starting point' },
  { id: 2, title: 'Personality', icon: Brain, description: 'Core personality tendencies' },
  { id: 3, title: 'Background', icon: Calendar, description: 'Life story and context' },
  { id: 4, title: 'First Experience', icon: Sparkles, description: 'Optional initial event' },
];

export default function CreatePersona() {
  const [, setLocation] = useLocation();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<PersonaFormData>({
    name: '',
    age: 10,
    gender: 'female',
    tagline: '',
    openness: 50,
    conscientiousness: 50,
    extraversion: 50,
    agreeableness: 50,
    emotionalSensitivity: 50,
    backgroundStory: '',
    familyBackground: '',
    earlyChildhood: '',
    protectiveFactors: '',
    hasInitialExperience: false,
  });

  const updateFormData = (data: Partial<PersonaFormData>) => {
    setFormData(prev => ({ ...prev, ...data }));
  };

  const handleNext = () => {
    // Validate current step
    if (currentStep === 1) {
      if (!formData.name.trim()) {
        toast.error('Please enter a name');
        return;
      }
      if (!formData.tagline.trim()) {
        toast.error('Please enter a tagline');
        return;
      }
    }
    
    if (currentStep === 3) {
      if (!formData.backgroundStory.trim()) {
        toast.error('Please provide a background story');
        return;
      }
    }
    
    if (currentStep < STEPS.length) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSubmit = () => {
    // In a real app, this would save to a database
    console.log('Creating persona:', formData);
    
    toast.success('Persona created!', {
      description: `${formData.name} has been added to your collection`
    });
    
    // Navigate back to home
    setTimeout(() => {
      setLocation('/');
    }, 1000);
  };

  const progress = (currentStep / STEPS.length) * 100;
  const currentStepData = STEPS[currentStep - 1];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-10" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <div className="container py-4">
          <Link href="/">
            <button className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4">
              <ArrowLeft className="w-4 h-4" />
              Back to Personas
            </button>
          </Link>

          <div className="flex items-center gap-4">
            <div 
              className="w-12 h-12 rounded-lg flex items-center justify-center shrink-0"
              style={{ background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))' }}
            >
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-foreground">
                Create New Persona
              </h1>
              <p className="text-sm text-muted-foreground">
                Step {currentStep} of {STEPS.length}: {currentStepData.title}
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <Progress value={progress} className="h-2" />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-8">
        <div className="max-w-4xl mx-auto">
          {/* Step Indicators */}
          <div className="mb-8 grid grid-cols-4 gap-4">
            {STEPS.map((step) => {
              const Icon = step.icon;
              const isCompleted = currentStep > step.id;
              const isCurrent = currentStep === step.id;
              
              return (
                <div
                  key={step.id}
                  className={`flex flex-col items-center text-center transition-all ${
                    isCurrent ? 'opacity-100' : isCompleted ? 'opacity-100' : 'opacity-40'
                  }`}
                >
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all ${
                      isCompleted
                        ? 'bg-[var(--deep-purple)] text-white'
                        : isCurrent
                        ? 'bg-[var(--lavender)] text-[var(--deep-purple)]'
                        : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    {isCompleted ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                  </div>
                  <p className="text-xs font-medium text-foreground">{step.title}</p>
                  <p className="text-xs text-muted-foreground hidden sm:block">{step.description}</p>
                </div>
              );
            })}
          </div>

          {/* Step Content */}
          <Card className="p-8" style={{ boxShadow: 'var(--shadow-md)' }}>
            {currentStep === 1 && (
              <BasicInfoStep formData={formData} updateFormData={updateFormData} />
            )}
            {currentStep === 2 && (
              <PersonalityStep formData={formData} updateFormData={updateFormData} />
            )}
            {currentStep === 3 && (
              <BackgroundStep formData={formData} updateFormData={updateFormData} />
            )}
            {currentStep === 4 && (
              <InitialExperienceStep formData={formData} updateFormData={updateFormData} />
            )}
          </Card>

          {/* Navigation Buttons */}
          <div className="mt-6 flex items-center justify-between">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={currentStep === 1}
              className="gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Previous
            </Button>

            {currentStep < STEPS.length ? (
              <Button
                onClick={handleNext}
                className="gap-2"
                style={{ 
                  background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))',
                  color: 'white'
                }}
              >
                Next Step
                <ArrowRight className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                className="gap-2"
                style={{ 
                  background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))',
                  color: 'white'
                }}
              >
                <Check className="w-4 h-4" />
                Create Persona
              </Button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

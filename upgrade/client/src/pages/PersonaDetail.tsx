/*
 * PersonaDetail Page
 * Design: Empathetic Modernism - Tabbed interface with human-centered content
 * Shows persona overview, interactive timeline, and narrative
 */

import { useState } from 'react';
import { useRoute, Link } from 'wouter';
import { ArrowLeft, Calendar, BookOpen, User, TrendingUp, Plus, Save, Shuffle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import PersonalityTraits from '@/components/PersonalityTraits';
import CurrentExperiences from '@/components/CurrentExperiences';
import InteractiveTimeline from '@/components/InteractiveTimeline';
import PersonalityEvolutionChart from '@/components/PersonalityEvolutionChart';
import NarrativeView from '@/components/NarrativeView';
import { getPersonaById } from '@/lib/mockData';
import { toast } from 'sonner';

export default function PersonaDetail() {
  const [, params] = useRoute('/persona/:id');
  const persona = params?.id ? getPersonaById(params.id) : undefined;
  const [activeTab, setActiveTab] = useState('overview');

  if (!persona) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-foreground mb-2">Persona not found</h2>
          <p className="text-muted-foreground mb-6">
            The persona you're looking for doesn't exist.
          </p>
          <Link href="/">
            <Button>Return Home</Button>
          </Link>
        </div>
      </div>
    );
  }

  const handleAddExperience = () => {
    toast.info('Feature coming soon', {
      description: 'Add life experience functionality will be available soon'
    });
  };

  const handleSaveSnapshot = () => {
    toast.success('Snapshot saved', {
      description: `Saved current state of ${persona.name}`
    });
  };

  const handleRemix = () => {
    toast.info('Feature coming soon', {
      description: 'Remix persona functionality will be available soon'
    });
  };

  const initials = persona.name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-10" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <div className="container py-4">
          {/* Back Button */}
          <Link href="/">
            <button className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4">
              <ArrowLeft className="w-4 h-4" />
              Back to Personas
            </button>
          </Link>

          {/* Persona Header */}
          <div className="flex items-start justify-between gap-6">
            <div className="flex items-start gap-4 flex-1 min-w-0">
              <div 
                className="w-16 h-16 rounded-full flex items-center justify-center text-white font-bold text-2xl shrink-0"
                style={{ background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))' }}
              >
                {initials}
              </div>
              
              <div className="flex-1 min-w-0">
                <h1 className="text-3xl font-bold text-foreground mb-1">
                  {persona.name}
                </h1>
                <p className="text-sm text-muted-foreground italic mb-3">
                  {persona.tagline}
                </p>
                
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-4 h-4" />
                    <span>Age {persona.age}</span>
                  </div>
                  <span>•</span>
                  <div className="flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4" />
                    <span>{persona.lifeEvents.length} life events</span>
                  </div>
                  <span>•</span>
                  <span>{persona.gender}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 shrink-0">
              <Button 
                variant="outline" 
                size="sm" 
                className="gap-2"
                onClick={handleAddExperience}
              >
                <Plus className="w-4 h-4" />
                Add Experience
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="gap-2"
                onClick={handleSaveSnapshot}
              >
                <Save className="w-4 h-4" />
                Save Snapshot
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="gap-2"
                onClick={handleRemix}
              >
                <Shuffle className="w-4 h-4" />
                Remix
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          {/* Tabs Navigation */}
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="overview" className="gap-2">
              <User className="w-4 h-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="timeline" className="gap-2">
              <TrendingUp className="w-4 h-4" />
              Life Journey
            </TabsTrigger>
            <TabsTrigger value="narrative" className="gap-2">
              <BookOpen className="w-4 h-4" />
              Their Story
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Background Story */}
            <div className="bg-card rounded-lg p-6" style={{ boxShadow: 'var(--shadow-sm)' }}>
              <h3 className="text-lg font-bold text-foreground mb-3">Background</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {persona.backgroundStory}
              </p>
            </div>

            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Personality Traits */}
              <PersonalityTraits traits={persona.personalityTraits} />
              
              {/* Current Experiences */}
              <CurrentExperiences 
                symptoms={persona.currentSymptoms} 
                personaName={persona.name}
              />
            </div>
          </TabsContent>

          {/* Timeline Tab */}
          <TabsContent value="timeline" className="space-y-8">
            {/* Personality Evolution Chart */}
            <div className="bg-card rounded-lg p-6" style={{ boxShadow: 'var(--shadow-sm)' }}>
              <PersonalityEvolutionChart 
                events={persona.lifeEvents}
                baselineTraits={{
                  openness: persona.personalityTraits.find(t => t.name.toLowerCase().includes('openness'))?.value || 50,
                  conscientiousness: persona.personalityTraits.find(t => t.name.toLowerCase().includes('conscientiousness'))?.value || 50,
                  extraversion: persona.personalityTraits.find(t => t.name.toLowerCase().includes('extraversion'))?.value || 50,
                  agreeableness: persona.personalityTraits.find(t => t.name.toLowerCase().includes('agreeableness'))?.value || 50,
                  emotionalStability: persona.personalityTraits.find(t => t.name.toLowerCase().includes('emotional'))?.value || 50
                }}
              />
            </div>

            {/* Interactive Timeline */}
            <InteractiveTimeline 
              events={persona.lifeEvents} 
              personaName={persona.name}
              currentAge={persona.age}
              onEventsChange={(updatedEvents) => {
                // In a real app, this would update the backend
                console.log('Events updated:', updatedEvents);
              }}
            />
          </TabsContent>

          {/* Narrative Tab */}
          <TabsContent value="narrative">
            {persona.narrative ? (
              <NarrativeView 
                narrative={persona.narrative}
                personaName={persona.name}
                age={persona.age}
              />
            ) : (
              <div className="bg-card rounded-lg p-12 text-center" style={{ boxShadow: 'var(--shadow-sm)' }}>
                <BookOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  No narrative yet
                </h3>
                <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
                  Generate a comprehensive psychological narrative to understand {persona.name}'s 
                  story holistically.
                </p>
                <Button 
                  size="lg"
                  style={{ 
                    background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))',
                    color: 'white'
                  }}
                >
                  Generate Narrative
                </Button>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

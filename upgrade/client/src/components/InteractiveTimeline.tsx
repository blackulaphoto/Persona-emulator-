/*
 * InteractiveTimeline Component
 * Design: Empathetic Modernism - Vertical timeline with smooth interactions
 * Visualizes life journey as a story arc, not a data chart
 * Now supports adding, editing, and deleting events
 */

import { useState } from 'react';
import { ChevronDown, ChevronUp, Sparkles, CloudRain, Circle, Plus, Edit, Trash2, TrendingUp } from 'lucide-react';
import type { LifeEvent } from '@/lib/mockData';
import PersonalityEvolution from './PersonalityEvolution';
import TherapyOutcomesDisplay from './TherapyOutcomesDisplay';
import { getEventTypeLabel } from '@/lib/mockData';
import EventModal from './EventModal';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface InteractiveTimelineProps {
  events: LifeEvent[];
  personaName: string;
  currentAge: number;
  onEventsChange?: (events: LifeEvent[]) => void;
}

export default function InteractiveTimeline({ events, personaName, currentAge, onEventsChange }: InteractiveTimelineProps) {
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<LifeEvent | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [eventToDelete, setEventToDelete] = useState<string | null>(null);

  const toggleEvent = (eventId: string) => {
    setExpandedEventId(expandedEventId === eventId ? null : eventId);
  };

  const handleAddEvent = () => {
    setEditingEvent(null);
    setModalOpen(true);
  };

  const handleEditEvent = (event: LifeEvent, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingEvent(event);
    setModalOpen(true);
  };

  const handleDeleteClick = (eventId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEventToDelete(eventId);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (eventToDelete && onEventsChange) {
      const updatedEvents = events.filter(e => e.id !== eventToDelete);
      onEventsChange(updatedEvents);
    }
    setDeleteDialogOpen(false);
    setEventToDelete(null);
  };

  const handleSaveEvent = (event: LifeEvent) => {
    if (!onEventsChange) return;

    const existingIndex = events.findIndex(e => e.id === event.id);
    let updatedEvents;
    
    if (existingIndex >= 0) {
      // Edit existing
      updatedEvents = [...events];
      updatedEvents[existingIndex] = event;
    } else {
      // Add new
      updatedEvents = [...events, event];
    }
    
    // Sort by age
    updatedEvents.sort((a, b) => a.age - b.age);
    onEventsChange(updatedEvents);
  };

  const getEventIcon = (type: 'growth' | 'challenge' | 'neutral' | 'therapy') => {
    switch (type) {
      case 'growth':
        return <Sparkles className="w-4 h-4" />;
      case 'challenge':
        return <CloudRain className="w-4 h-4" />;
      case 'therapy':
        return <TrendingUp className="w-4 h-4" />;
      case 'neutral':
        return <Circle className="w-4 h-4" />;
    }
  };

  const getEventColorClass = (type: 'growth' | 'challenge' | 'neutral' | 'therapy') => {
    switch (type) {
      case 'growth':
        return 'event-growth';
      case 'challenge':
        return 'event-challenge';
      case 'neutral':
        return 'event-neutral';
    }
  };

  const getEventBgColor = (type: 'growth' | 'challenge' | 'neutral' | 'therapy') => {
    switch (type) {
      case 'growth':
        return 'rgba(154, 230, 180, 0.1)';
      case 'challenge':
        return 'rgba(252, 129, 129, 0.1)';
      case 'therapy':
        return 'rgba(124, 58, 237, 0.1)'; // purple tint
      case 'neutral':
        return 'rgba(183, 148, 244, 0.1)';
    }
  };

  const getEventIconColor = (type: 'growth' | 'challenge' | 'neutral' | 'therapy') => {
    switch (type) {
      case 'growth':
        return 'var(--sage-green)';
      case 'challenge':
        return 'var(--muted-coral)';
      case 'therapy':
        return 'var(--deep-purple)';
      case 'neutral':
        return 'var(--periwinkle)';
    }
  };

  // Sort events by age
  const sortedEvents = [...events].sort((a, b) => a.age - b.age);

  return (
    <div className="space-y-6">
      <EventModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveEvent}
        event={editingEvent}
        currentAge={currentAge}
      />

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this event?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently remove this life event from the timeline. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete Event
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Timeline Header */}
      <div className="bg-[var(--lavender)] bg-opacity-20 rounded-lg p-4 border border-[var(--lavender)]">
        <p className="text-sm text-foreground flex items-start gap-2">
          <span className="text-lg">📖</span>
          <span>
            The timeline shows key experiences in chronological order, helping you understand 
            how {personaName}'s psychological development unfolded.
          </span>
        </p>
      </div>

      {/* Add Event Button */}
      {onEventsChange && (
        <div className="flex justify-center">
          <Button
            onClick={handleAddEvent}
            size="lg"
            className="gap-2"
            style={{
              background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))',
              color: 'white'
            }}
          >
            <Plus className="w-5 h-5" />
            Add Life Event
          </Button>
        </div>
      )}

      {/* Timeline Events */}
      <div className="relative">
        {sortedEvents.map((event, index) => {
          const isExpanded = expandedEventId === event.id;
          const isLast = index === sortedEvents.length - 1;

          return (
            <div 
              key={event.id} 
              className={`relative pl-12 ${!isLast ? 'pb-8' : ''}`}
            >
              {/* Timeline Line */}
              {!isLast && (
                <div 
                  className="absolute left-[1.125rem] top-8 bottom-0 w-0.5"
                  style={{
                    background: 'linear-gradient(to bottom, var(--lavender), var(--periwinkle))'
                  }}
                />
              )}

              {/* Age Marker */}
              <div 
                className="absolute left-0 top-0 w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm text-white"
                style={{
                  background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))',
                  boxShadow: '0 0 0 4px var(--background)'
                }}
              >
                {event.age}
              </div>

              {/* Event Card */}
              <div 
                className={`bg-card rounded-lg border-l-4 ${getEventColorClass(event.type)} transition-all duration-200 overflow-hidden`}
                style={{
                  boxShadow: 'var(--shadow-sm)',
                  backgroundColor: getEventBgColor(event.type)
                }}
              >
                {/* Event Header */}
                <div className="p-4">
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <button
                      onClick={() => toggleEvent(event.id)}
                      className="flex-1 text-left hover:opacity-80 transition-opacity focus-ring min-w-0"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span style={{ color: getEventIconColor(event.type) }}>
                          {getEventIcon(event.type)}
                        </span>
                        <span 
                          className="text-xs font-semibold uppercase tracking-wide"
                          style={{ color: getEventIconColor(event.type) }}
                        >
                          {getEventTypeLabel(event.type)}
                        </span>
                      </div>
                      
                      <h4 className="text-lg font-bold text-foreground mb-1">
                        {event.title}
                      </h4>
                      
                      <p className="text-sm text-muted-foreground">
                        {event.description}
                      </p>
                    </button>

                    <div className="shrink-0 flex items-center gap-2">
                      {onEventsChange && (
                        <>
                          <button
                            onClick={(e) => handleEditEvent(event, e)}
                            className="p-2 hover:bg-purple-50 rounded-lg transition-colors"
                            title="Edit event"
                          >
                            <Edit className="w-4 h-4" style={{ color: 'var(--deep-purple)' }} />
                          </button>
                          <button
                            onClick={(e) => handleDeleteClick(event.id, e)}
                            className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                            title="Delete event"
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => toggleEvent(event.id)}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-5 h-5" />
                        ) : (
                          <ChevronDown className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-4 pb-4 space-y-4 border-t border-border">
                    {/* Therapy Details (if therapy event) */}
                    {event.type === 'therapy' && (
                      <div className="pt-4">
                        <TherapyOutcomesDisplay 
                          therapyApproach={event.therapyApproach}
                          sessionCount={event.sessionCount}
                          therapyOutcomes={event.therapyOutcomes}
                          personalityChanges={event.personalityChanges}
                          symptoms={event.symptoms}
                        />
                      </div>
                    )}

                    {/* Impact */}
                    {event.impact && (
                      <div className="pt-4">
                        <h5 className="text-sm font-semibold text-foreground mb-2">
                          Impact on Development
                        </h5>
                        <p className="text-sm text-muted-foreground">
                          {event.impact}
                        </p>
                      </div>
                    )}

                    {/* Personality Changes */}
                    {event.personalityChanges && event.personalityChanges.length > 0 && (
                      <div className="space-y-3 pt-4">
                        <div className="flex items-center gap-2">
                          <TrendingUp className="w-5 h-5 text-primary" />
                          <h5 className="text-sm font-semibold text-foreground">
                            Personality Evolution
                          </h5>
                        </div>
                        <PersonalityEvolution changes={event.personalityChanges} />
                      </div>
                    )}

                    {/* Symptoms */}
                    {event.symptoms && event.symptoms.length > 0 && (
                      <div>
                        <h5 className="text-sm font-semibold text-foreground mb-2">
                          What They Were Experiencing
                        </h5>
                        <div className="flex flex-wrap gap-2">
                          {event.symptoms.map((symptom, idx) => (
                            <span 
                              key={idx}
                              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
                              style={{
                                background: 'rgba(252, 129, 129, 0.15)',
                                color: '#C53030'
                              }}
                            >
                              {symptom.name}
                              <span className="opacity-70">({symptom.severity}/10)</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

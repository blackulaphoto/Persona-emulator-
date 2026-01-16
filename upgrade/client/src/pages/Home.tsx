/*
 * Home Page - Personas List
 * Design: Empathetic Modernism - Grid of persona cards, not a database table
 * Human-friendly language throughout
 */

import { Plus, Users } from 'lucide-react';
import { Link } from 'wouter';
import { Button } from '@/components/ui/button';
import PersonaCard from '@/components/PersonaCard';
import { getAllPersonas } from '@/lib/mockData';

export default function Home() {
  const personas = getAllPersonas();

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <div className="container py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div 
                className="w-12 h-12 rounded-lg flex items-center justify-center"
                style={{ background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))' }}
              >
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-foreground">
                  Persona Evolution
                </h1>
                <p className="text-sm text-muted-foreground">
                  Explore psychological transformation through life experiences
                </p>
              </div>
            </div>
            
            <Link href="/create">
              <Button 
                size="lg"
                className="gap-2"
                style={{ 
                  background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))',
                  color: 'white'
                }}
              >
                <Plus className="w-5 h-5" />
                Create New Persona
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-8">
        {/* Info Banner */}
        <div className="mb-8 bg-[var(--lavender)] bg-opacity-20 rounded-lg p-6 border border-[var(--lavender)]">
          <div className="flex items-start gap-3">
            <span className="text-2xl shrink-0">👋</span>
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-1">
                Your Personas
              </h2>
              <p className="text-sm text-muted-foreground">
                Manage your collection of psychological personas. Create new personas from scratch, 
                use clinical templates, or explore different developmental pathways. Each persona 
                represents a unique journey through life experiences and therapy.
              </p>
            </div>
          </div>
        </div>

        {/* Personas Grid */}
        {personas.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {personas.map(persona => (
              <PersonaCard key={persona.id} persona={persona} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div 
              className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4"
              style={{ background: 'var(--soft-gray)' }}
            >
              <Users className="w-10 h-10 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              No personas yet
            </h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-md mx-auto">
              Create your first persona to start exploring psychological development 
              and transformation through life experiences.
            </p>
            <Link href="/create">
              <Button 
                size="lg"
                className="gap-2"
                style={{ 
                  background: 'linear-gradient(135deg, var(--deep-purple), var(--soft-purple))',
                  color: 'white'
                }}
              >
                <Plus className="w-5 h-5" />
                Create Your First Persona
              </Button>
            </Link>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-16">
        <div className="container py-6">
          <p className="text-xs text-center text-muted-foreground">
            Persona Evolution is an educational tool for understanding psychological development. 
            Not a substitute for professional clinical assessment.
          </p>
        </div>
      </footer>
    </div>
  );
}

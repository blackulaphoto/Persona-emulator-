/**
 * Design: Empathetic Modernism - Interactive line chart for personality trait evolution
 * Shows how Big Five traits change across life events with smooth animations
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp } from 'lucide-react';
import type { LifeEvent } from '@/lib/mockData';

interface PersonalityEvolutionChartProps {
  events: LifeEvent[];
  baselineTraits: {
    openness: number;
    conscientiousness: number;
    extraversion: number;
    agreeableness: number;
    emotionalStability: number;
  };
}

export default function PersonalityEvolutionChart({ events, baselineTraits }: PersonalityEvolutionChartProps) {
  // Calculate trait values at each point in time
  const calculateTraitEvolution = () => {
    // Sort events by age
    const sortedEvents = [...events].sort((a, b) => a.age - b.age);
    
    // Start with baseline at age 0 (or earliest event age - 1)
    const startAge = sortedEvents.length > 0 ? Math.max(0, sortedEvents[0].age - 1) : 0;
    
    const data = [
      {
        age: startAge,
        label: 'Baseline',
        openness: baselineTraits.openness,
        conscientiousness: baselineTraits.conscientiousness,
        extraversion: baselineTraits.extraversion,
        agreeableness: baselineTraits.agreeableness,
        emotionalStability: baselineTraits.emotionalStability,
      }
    ];

    // Track current trait values
    let currentTraits = { ...baselineTraits };

    // Process each event
    sortedEvents.forEach((event) => {
      if (event.personalityChanges && event.personalityChanges.length > 0) {
        // Apply personality changes from this event
        event.personalityChanges.forEach((change) => {
          const traitKey = change.trait.toLowerCase().replace(/\s+/g, '');
          
          // Map trait names to our keys
          if (traitKey.includes('openness')) {
            currentTraits.openness = change.after;
          } else if (traitKey.includes('conscientiousness')) {
            currentTraits.conscientiousness = change.after;
          } else if (traitKey.includes('extraversion')) {
            currentTraits.extraversion = change.after;
          } else if (traitKey.includes('agreeableness')) {
            currentTraits.agreeableness = change.after;
          } else if (traitKey.includes('emotional') || traitKey.includes('stability')) {
            currentTraits.emotionalStability = change.after;
          } else if (traitKey.includes('trust')) {
            // Map trust to emotional stability for visualization
            currentTraits.emotionalStability = change.after;
          }
        });

        data.push({
          age: event.age,
          label: event.title,
          openness: currentTraits.openness,
          conscientiousness: currentTraits.conscientiousness,
          extraversion: currentTraits.extraversion,
          agreeableness: currentTraits.agreeableness,
          emotionalStability: currentTraits.emotionalStability,
        });
      }
    });

    return data;
  };

  const chartData = calculateTraitEvolution();

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload;
      return (
        <div 
          className="p-4 rounded-lg shadow-lg border"
          style={{ 
            backgroundColor: 'var(--card)',
            borderColor: 'var(--border)'
          }}
        >
          <p className="font-semibold mb-2">
            Age {label}: {dataPoint.label}
          </p>
          <div className="space-y-1">
            {payload.map((entry: any) => (
              <div key={entry.name} className="flex items-center justify-between gap-4">
                <span className="text-sm capitalize" style={{ color: entry.color }}>
                  {entry.name.replace(/([A-Z])/g, ' $1').trim()}:
                </span>
                <span className="text-sm font-medium">
                  {entry.value}%
                </span>
              </div>
            ))}
          </div>
        </div>
      );
    }
    return null;
  };

  if (chartData.length <= 1) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No personality evolution data available yet.</p>
        <p className="text-sm mt-2">Add personality changes to life events to see trait evolution over time.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <TrendingUp className="w-5 h-5" style={{ color: 'var(--deep-purple)' }} />
        <h3 className="text-lg font-semibold">Personality Trait Evolution Over Time</h3>
      </div>
      
      <div 
        className="p-4 rounded-lg"
        style={{ backgroundColor: 'var(--light-lavender)' }}
      >
        <p className="text-sm text-muted-foreground">
          This chart shows how the Big Five personality traits have evolved through life experiences. 
          Each point represents a significant event that shaped their psychological development.
        </p>
      </div>

      <div className="w-full h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              dataKey="age" 
              label={{ value: 'Age', position: 'insideBottom', offset: -5 }}
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              label={{ value: 'Trait Level (%)', angle: -90, position: 'insideLeft' }}
              domain={[0, 100]}
              style={{ fontSize: '12px' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ paddingTop: '20px' }}
              formatter={(value) => value.replace(/([A-Z])/g, ' $1').trim()}
            />
            
            {/* Lines for each trait */}
            <Line 
              type="monotone" 
              dataKey="openness" 
              stroke="#8b5cf6" 
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Openness"
            />
            <Line 
              type="monotone" 
              dataKey="conscientiousness" 
              stroke="#3b82f6" 
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Conscientiousness"
            />
            <Line 
              type="monotone" 
              dataKey="extraversion" 
              stroke="#10b981" 
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Extraversion"
            />
            <Line 
              type="monotone" 
              dataKey="agreeableness" 
              stroke="#f59e0b" 
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Agreeableness"
            />
            <Line 
              type="monotone" 
              dataKey="emotionalStability" 
              stroke="#ef4444" 
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Emotional Stability"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="text-xs text-muted-foreground italic">
        Note: This visualization helps identify patterns in personality development. 
        Traits can shift significantly during formative years based on experiences and interventions.
      </div>
    </div>
  );
}

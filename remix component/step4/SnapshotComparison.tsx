/**
 * Snapshot Comparison Component
 * 
 * Side-by-side comparison of two timeline snapshots showing:
 * - Personality trait differences
 * - Symptom changes
 * - Severity improvements
 * - Natural language summary
 */
'use client';

import { useState, useEffect } from 'react';
import { remixAPI, SnapshotComparison } from '@/lib/api/templates';

interface SnapshotComparisonProps {
  snapshotId1: string;
  snapshotId2: string;
  onClose: () => void;
}

export default function SnapshotComparisonView({
  snapshotId1,
  snapshotId2,
  onClose,
}: SnapshotComparisonProps) {
  const [comparison, setComparison] = useState<SnapshotComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadComparison();
  }, [snapshotId1, snapshotId2]);

  async function loadComparison() {
    setLoading(true);
    setError(null);

    try {
      const data = await remixAPI.compareSnapshots(snapshotId1, snapshotId2);
      setComparison(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare snapshots');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">Comparing snapshots...</span>
      </div>
    );
  }

  if (error || !comparison) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-red-900 mb-2">Comparison Error</h3>
        <p className="text-red-700">{error || 'Failed to load comparison'}</p>
        <button
          onClick={onClose}
          className="mt-4 bg-red-600 text-white rounded-lg px-4 py-2 hover:bg-red-700"
        >
          Close
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Summary</h3>
        <p className="text-blue-800 leading-relaxed">{comparison.summary}</p>
      </div>

      {/* Side-by-side snapshot info */}
      <div className="grid grid-cols-2 gap-6">
        <SnapshotCard
          label={comparison.snapshot_1.label}
          personality={comparison.snapshot_1.personality}
          symptoms={comparison.snapshot_1.symptoms}
          symptomSeverity={comparison.snapshot_1.symptom_severity}
          variant="baseline"
        />
        <SnapshotCard
          label={comparison.snapshot_2.label}
          personality={comparison.snapshot_2.personality}
          symptoms={comparison.snapshot_2.symptoms}
          symptomSeverity={comparison.snapshot_2.symptom_severity}
          variant="comparison"
        />
      </div>

      {/* Personality Changes */}
      <section className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Personality Changes</h3>
        <div className="space-y-4">
          {Object.entries(comparison.personality_differences).map(([trait, diff]) => (
            <div key={trait}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700 capitalize">{trait}</span>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-600">
                    {(diff.snapshot_1 * 100).toFixed(0)}% → {(diff.snapshot_2 * 100).toFixed(0)}%
                  </span>
                  <span className={`text-sm font-semibold ${
                    diff.difference > 0 ? 'text-red-600' :
                    diff.difference < 0 ? 'text-green-600' :
                    'text-gray-600'
                  }`}>
                    {diff.difference > 0 ? '+' : ''}{(diff.difference * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="relative h-3">
                {/* Background bars */}
                <div className="absolute inset-0 flex gap-1">
                  <div 
                    className="bg-blue-200 rounded-l"
                    style={{ width: `${diff.snapshot_1 * 50}%` }}
                  />
                  <div 
                    className="bg-purple-200 rounded-r"
                    style={{ width: `${diff.snapshot_2 * 50}%` }}
                  />
                </div>
                {/* Difference indicator */}
                <div className="absolute inset-y-0 left-1/2 w-0.5 bg-gray-400" />
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Baseline</span>
                <span>Modified</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Symptom Changes */}
      <section className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Symptom Changes</h3>
        
        <div className="space-y-4">
          {/* Resolved symptoms */}
          {comparison.symptom_differences.only_in_snapshot_1.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-green-800 mb-2 flex items-center">
                <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Resolved ({comparison.symptom_differences.only_in_snapshot_1.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {comparison.symptom_differences.only_in_snapshot_1.map((symptom, idx) => (
                  <span key={idx} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                    {symptom.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* New symptoms */}
          {comparison.symptom_differences.only_in_snapshot_2.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-red-800 mb-2 flex items-center">
                <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                New Symptoms ({comparison.symptom_differences.only_in_snapshot_2.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {comparison.symptom_differences.only_in_snapshot_2.map((symptom, idx) => (
                  <span key={idx} className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">
                    {symptom.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Persisting symptoms */}
          {comparison.symptom_differences.in_both.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v2H7a1 1 0 100 2h2v2a1 1 0 102 0v-2h2a1 1 0 100-2h-2V7z" clipRule="evenodd" />
                </svg>
                Persisting ({comparison.symptom_differences.in_both.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {comparison.symptom_differences.in_both.map((symptom, idx) => (
                  <span key={idx} className="px-3 py-1 bg-gray-200 text-gray-800 rounded-full text-sm">
                    {symptom.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Severity Changes */}
      <section className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Symptom Severity Changes</h3>
        <div className="space-y-3">
          {Object.entries(comparison.symptom_severity_differences)
            .filter(([_, diff]) => diff.snapshot_1 > 0 || diff.snapshot_2 > 0)
            .map(([symptom, diff]) => (
              <div key={symptom} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <span className="text-sm font-medium text-gray-700 capitalize flex-1">
                  {symptom.replace(/_/g, ' ')}
                </span>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">Before:</span>
                    <span className="text-sm font-semibold text-gray-900 w-6 text-right">{diff.snapshot_1}</span>
                  </div>
                  <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">After:</span>
                    <span className="text-sm font-semibold text-gray-900 w-6 text-right">{diff.snapshot_2}</span>
                  </div>
                  <span className={`text-sm font-bold w-12 text-right ${
                    diff.difference < 0 ? 'text-green-600' :
                    diff.difference > 0 ? 'text-red-600' :
                    'text-gray-600'
                  }`}>
                    {diff.difference > 0 ? '+' : ''}{diff.difference}
                  </span>
                </div>
              </div>
            ))}
        </div>
      </section>

      {/* Close button */}
      <div className="flex justify-end">
        <button
          onClick={onClose}
          className="bg-gray-600 text-white rounded-lg px-6 py-2 hover:bg-gray-700"
        >
          Close Comparison
        </button>
      </div>
    </div>
  );
}

// Snapshot Card Component
interface SnapshotCardProps {
  label: string;
  personality: Record<string, number>;
  symptoms: string[];
  symptomSeverity: Record<string, number>;
  variant: 'baseline' | 'comparison';
}

function SnapshotCard({ label, personality, symptoms, symptomSeverity, variant }: SnapshotCardProps) {
  const borderColor = variant === 'baseline' ? 'border-blue-300' : 'border-purple-300';
  const bgColor = variant === 'baseline' ? 'bg-blue-50' : 'bg-purple-50';
  const textColor = variant === 'baseline' ? 'text-blue-900' : 'text-purple-900';

  return (
    <div className={`border-2 ${borderColor} ${bgColor} rounded-lg p-5`}>
      <h3 className={`text-lg font-semibold ${textColor} mb-4`}>{label}</h3>
      
      {/* Personality summary */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Personality</h4>
        <div className="grid grid-cols-5 gap-2">
          {Object.entries(personality).map(([trait, value]) => (
            <div key={trait} className="text-center">
              <div className="text-lg font-bold text-gray-900">{(value * 100).toFixed(0)}</div>
              <div className="text-xs text-gray-600 capitalize">{trait.slice(0, 4)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Symptoms count */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">
          Symptoms ({symptoms.length})
        </h4>
        <div className="flex flex-wrap gap-1">
          {symptoms.slice(0, 5).map((symptom, idx) => (
            <span key={idx} className="px-2 py-0.5 bg-white text-gray-700 rounded text-xs">
              {symptom.replace(/_/g, ' ')}
            </span>
          ))}
          {symptoms.length > 5 && (
            <span className="px-2 py-0.5 bg-gray-200 text-gray-600 rounded text-xs">
              +{symptoms.length - 5} more
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

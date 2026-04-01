import { useState, useCallback } from 'react';
import ClaimCard from './ClaimCard';

export default function PredictStep({ claims, onSubmit, logEvent }) {
  // Map of claim_id -> { prediction: 'accurate' | 'neutral' | 'false' }
  const [selections, setSelections] = useState(() =>
    Object.fromEntries(claims.map(c => [c.id, { prediction: 'neutral' }]))
  );
  // Track whether the student has interacted with at least one button
  const [hasInteracted, setHasInteracted] = useState(false);

  const handlePredictionChange = useCallback((claimId, prediction) => {
    setSelections(prev => ({
      ...prev,
      [claimId]: { prediction },
    }));
    setHasInteracted(true);
  }, []);

  const handleExpand = useCallback((claimId) => {
    logEvent('claim_expanded', { claim_id: claimId, time_spent_ms: 0 });
  }, [logEvent]);

  const handleLinkClick = useCallback((claimId, url) => {
    logEvent('evidence_link_clicked', { claim_id: claimId, url });
  }, [logEvent]);

  const handleReveal = () => {
    const predictions = claims.map(c => ({
      claim_id: c.id,
      predicted_inaccurate: (selections[c.id]?.prediction ?? 'neutral') === 'false',
      prediction_label: selections[c.id]?.prediction ?? 'neutral',
      reasoning: '',
    }));
    onSubmit(predictions);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 pt-4 pb-3 border-b border-gray-200 bg-gray-50">
        <h2 className="text-sm font-semibold text-gray-800">
          We found {claims.length} claim{claims.length !== 1 ? 's' : ''} to verify.
        </h2>
        <p className="text-xs text-gray-500 mt-1 leading-snug">
          Rate each claim: do you think it's accurate, false, or are you unsure?
          You can review the sources below to make an informed prediction.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
        {claims.map(claim => (
          <ClaimCard
            key={claim.id}
            mode="predict"
            claim={claim}
            prediction={selections[claim.id]?.prediction ?? 'neutral'}
            onPredictionChange={handlePredictionChange}
            onExpand={handleExpand}
            onLinkClick={handleLinkClick}
          />
        ))}
      </div>

      <div className="px-4 py-3 border-t border-gray-200 bg-white">
        {!hasInteracted && (
          <p className="text-xs text-gray-400 mb-2">
            Rate at least one claim to continue.
          </p>
        )}
        <button
          onClick={handleReveal}
          disabled={!hasInteracted}
          className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          Reveal Results &rarr;
        </button>
      </div>
    </div>
  );
}

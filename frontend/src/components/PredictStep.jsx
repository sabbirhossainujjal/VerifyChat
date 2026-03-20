import { useState, useCallback } from 'react';
import ClaimCard from './ClaimCard';

export default function PredictStep({ claims, onSubmit, logEvent }) {
  // Map of claim_id -> { checked: bool, reasoning: string }
  const [selections, setSelections] = useState(() =>
    Object.fromEntries(claims.map(c => [c.id, { checked: false, reasoning: '' }]))
  );
  // Track whether the student has interacted with at least one checkbox
  const [hasInteracted, setHasInteracted] = useState(false);

  const handleCheckChange = useCallback((claimId, checked) => {
    setSelections(prev => ({
      ...prev,
      [claimId]: { ...prev[claimId], checked },
    }));
    setHasInteracted(true);
  }, []);

  const handleReasoningChange = useCallback((claimId, value) => {
    setSelections(prev => ({
      ...prev,
      [claimId]: { ...prev[claimId], reasoning: value },
    }));
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
      predicted_inaccurate: selections[c.id]?.checked ?? false,
      reasoning: selections[c.id]?.reasoning ?? '',
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
          Before seeing results, which claims do <strong>you</strong> think might be inaccurate?
          You can review the sources below to make an informed prediction.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
        {claims.map(claim => (
          <ClaimCard
            key={claim.id}
            mode="predict"
            claim={claim}
            checked={selections[claim.id]?.checked ?? false}
            reasoning={selections[claim.id]?.reasoning ?? ''}
            onCheckChange={handleCheckChange}
            onReasoningChange={handleReasoningChange}
            onExpand={handleExpand}
            onLinkClick={handleLinkClick}
          />
        ))}
      </div>

      <div className="px-4 py-3 border-t border-gray-200 bg-white">
        {!hasInteracted && (
          <p className="text-xs text-gray-400 mb-2">
            Interact with at least one checkbox to continue (selecting none is valid).
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

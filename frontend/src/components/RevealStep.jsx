import ClaimCard from './ClaimCard';

function AccuracySummary({ accuracy, verdicts, predictions }) {
  if (!accuracy && !verdicts) return null;

  // Compute counts from verdicts if accuracy object is present
  const total = verdicts?.length ?? 0;
  const correct = accuracy?.correct_predictions ?? null;
  const precision = accuracy?.precision != null ? (accuracy.precision * 100).toFixed(0) : null;
  const recall = accuracy?.recall != null ? (accuracy.recall * 100).toFixed(0) : null;
  const f1 = accuracy?.f1 != null ? accuracy.f1.toFixed(2) : null;

  return (
    <div className="px-4 pt-4 pb-3 border-b border-gray-200 bg-gray-50">
      <h2 className="text-sm font-semibold text-gray-800 mb-1">Results</h2>
      {correct !== null && total > 0 && (
        <p className="text-sm text-gray-700">
          Your accuracy: <strong>{correct}/{total}</strong> claims correctly identified
        </p>
      )}
      {(precision !== null || recall !== null || f1 !== null) && (
        <div className="mt-2 flex gap-4 text-xs text-gray-500">
          {precision !== null && (
            <span>
              <span className="font-medium text-gray-700">Precision:</span> {precision}%
            </span>
          )}
          {recall !== null && (
            <span>
              <span className="font-medium text-gray-700">Recall:</span> {recall}%
            </span>
          )}
          {f1 !== null && (
            <span>
              <span className="font-medium text-gray-700">F1:</span> {f1}
            </span>
          )}
        </div>
      )}
      {precision !== null && (
        <p className="text-xs text-gray-400 mt-1.5 leading-snug">
          Precision = how often your flagged claims were truly inaccurate.
          Recall = how many inaccurate claims you caught.
        </p>
      )}
    </div>
  );
}

export default function RevealStep({ claims, verdicts, accuracy, predictions = [], logEvent }) {
  // Build a lookup: claim_id -> verdict
  const verdictMap = Object.fromEntries((verdicts || []).map(v => [v.claim_id, v]));
  // Build a lookup: claim_id -> studentPredicted (bool)
  const predictionMap = Object.fromEntries((predictions || []).map(p => [p.claim_id, p.predicted_inaccurate]));

  return (
    <div className="flex flex-col h-full">
      <AccuracySummary accuracy={accuracy} verdicts={verdicts} predictions={predictions} />

      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
        {claims.map(claim => (
          <ClaimCard
            key={claim.id}
            mode="reveal"
            claim={claim}
            verdict={verdictMap[claim.id]}
            studentPredicted={predictionMap[claim.id] ?? false}
            logEvent={logEvent}
          />
        ))}
      </div>

      <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
        <p className="text-xs text-gray-400 text-center">
          Send another message to continue the conversation.
        </p>
      </div>
    </div>
  );
}

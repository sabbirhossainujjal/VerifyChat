import ClaimCard from './ClaimCard';

const SCORE_TIERS = [
  {
    min: 0.6,
    emoji: '🌟',
    message: 'Excellent critical thinking!',
    pill: 'bg-green-100 border-green-200 text-green-900',
    num: 'text-green-700',
  },
  {
    min: 0.35,
    emoji: '👍',
    message: 'Good effort — keep analyzing!',
    pill: 'bg-amber-100 border-amber-200 text-amber-900',
    num: 'text-amber-700',
  },
  {
    min: 0,
    emoji: '📚',
    message: 'Review the evidence below to learn more.',
    pill: 'bg-red-100 border-red-200 text-red-900',
    num: 'text-red-700',
  },
];

function metricTileClass(val) {
  if (val >= 0.6) return 'bg-green-100 text-green-800';
  if (val >= 0.35) return 'bg-amber-100 text-amber-800';
  return 'bg-red-100 text-red-800';
}

function AccuracySummary({ accuracy, verdicts, predictionMap }) {
  if (!accuracy || !verdicts) return null;

  const correct = accuracy.correct_predictions ?? 0;
  const precision = accuracy.precision ?? 0;
  const recall = accuracy.recall ?? 0;
  const f1 = accuracy.f1 ?? 0;

  // Denominator: claims the student rated (non-neutral) where verdict was definitive
  const ratedDefinitive = verdicts.filter(v => {
    const pred = predictionMap[v.claim_id] || 'neutral';
    return pred !== 'neutral' && v.verdict !== 'insufficient_evidence';
  }).length;
  const scoredTotal = ratedDefinitive || verdicts.length;

  const pct = scoredTotal > 0 ? correct / scoredTotal : 0;
  const tier = SCORE_TIERS.find(t => pct >= t.min) || SCORE_TIERS[SCORE_TIERS.length - 1];

  const metrics = [
    { label: 'Precision', value: precision, display: `${(precision * 100).toFixed(0)}%` },
    { label: 'Recall', value: recall, display: `${(recall * 100).toFixed(0)}%` },
    { label: 'F1 Score', value: f1, display: f1.toFixed(2) },
  ];

  return (
    <div className="px-4 pt-4 pb-3 border-b border-gray-200 bg-gray-50 shrink-0">
      <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">Results</h2>

      {/* Main score card */}
      <div className={`flex items-center gap-4 rounded-xl border px-4 py-3 mb-3 ${tier.pill}`}>
        <span className="text-3xl leading-none">{tier.emoji}</span>
        <div className="flex-1 min-w-0">
          <div className={`text-2xl font-bold tabular-nums leading-none ${tier.num}`}>
            {correct}
            <span className="text-base font-normal opacity-60"> / {scoredTotal}</span>
          </div>
          <div className="text-xs font-medium mt-0.5 opacity-80">
            {tier.message}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-xs font-semibold opacity-60 uppercase tracking-wide">correctly</div>
          <div className="text-xs font-semibold opacity-60 uppercase tracking-wide">identified</div>
        </div>
      </div>

      {/* Metric tiles */}
      <div className="flex gap-2">
        {metrics.map(({ label, value, display }) => (
          <div
            key={label}
            className={`flex-1 rounded-lg px-2 py-2 text-center ${metricTileClass(value)}`}
          >
            <div className="text-sm font-bold tabular-nums leading-none">{display}</div>
            <div className="text-xs mt-0.5 opacity-70">{label}</div>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-400 mt-2 leading-snug">
        Precision = accuracy of your flags &bull; Recall = how many false claims you caught
      </p>
    </div>
  );
}

export default function RevealStep({ claims, verdicts, accuracy, predictions = [], logEvent }) {
  // Build a lookup: claim_id -> verdict
  const verdictMap = Object.fromEntries((verdicts || []).map(v => [v.claim_id, v]));
  // Build a lookup: claim_id -> prediction label string
  const predictionMap = Object.fromEntries(
    (predictions || []).map(p => [p.claim_id, p.prediction_label || (p.predicted_inaccurate ? 'false' : 'neutral')])
  );

  return (
    <div className="flex flex-col h-full">
      <AccuracySummary accuracy={accuracy} verdicts={verdicts} predictionMap={predictionMap} />

      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
        {claims.map(claim => (
          <ClaimCard
            key={claim.id}
            mode="reveal"
            claim={claim}
            verdict={verdictMap[claim.id]}
            studentPrediction={predictionMap[claim.id] ?? 'neutral'}
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

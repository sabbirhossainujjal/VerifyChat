import { useState, useRef } from 'react';

const VERDICT_CONFIG = {
  supported: {
    icon: '\u2705',
    label: 'Supported',
    textClass: 'text-green-600',
    bgClass: 'bg-green-50',
    borderClass: 'border-green-200',
  },
  unsupported: {
    icon: '\u274c',
    label: 'Unsupported',
    textClass: 'text-red-600',
    bgClass: 'bg-red-50',
    borderClass: 'border-red-200',
  },
  insufficient_evidence: {
    icon: '\u26a0\ufe0f',
    label: 'Insufficient Evidence',
    textClass: 'text-amber-500',
    bgClass: 'bg-amber-50',
    borderClass: 'border-amber-200',
  },
};

// Predict mode: shows claim + sources + 3-way prediction toggle
function PredictCard({ claim, prediction, onPredictionChange, onExpand, onLinkClick }) {
  // Track whether onExpand has been fired for this card
  const expandedRef = useRef(false);

  const handleButtonClick = (value) => {
    if (!expandedRef.current && value !== 'neutral') {
      expandedRef.current = true;
      onExpand(claim.id);
    }
    onPredictionChange(claim.id, value);
  };

  const handleLinkClick = (url) => {
    onLinkClick(claim.id, url);
  };

  const buttons = [
    { value: 'accurate', label: 'Accurate', selectedClass: 'bg-green-100 text-green-700 border-green-300' },
    { value: 'neutral',  label: 'Neutral',  selectedClass: 'bg-gray-100 text-gray-600' },
    { value: 'false',    label: 'False',    selectedClass: 'bg-red-100 text-red-700 border-red-300' },
  ];

  return (
    <div className="rounded-lg border border-gray-200 p-4 bg-white">
      <p className="text-sm text-gray-800 leading-relaxed mb-3">{claim.text}</p>

      {claim.source_url && (
        <div className="mb-3">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Sources</p>
          <div className="flex flex-col gap-1">
            <a
              href={claim.source_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => handleLinkClick(claim.source_url)}
              className="text-xs text-blue-600 hover:text-blue-800 hover:underline truncate"
              title={claim.source_title || claim.source_url}
            >
              {claim.source_title || claim.source_url}
            </a>
          </div>
        </div>
      )}

      <div className="flex rounded-lg overflow-hidden border border-gray-200 mt-3">
        {buttons.map((btn, idx) => {
          const isSelected = prediction === btn.value;
          const isLast = idx === buttons.length - 1;
          return (
            <button
              key={btn.value}
              type="button"
              onClick={() => handleButtonClick(btn.value)}
              className={[
                'flex-1 py-1.5 text-xs font-medium transition-colors',
                isSelected ? btn.selectedClass : 'bg-white text-gray-400 hover:bg-gray-50',
                !isLast ? 'border-r border-gray-200' : '',
              ].join(' ')}
            >
              {btn.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// Reveal mode: shows verdict + explanation + prediction match
function RevealCard({ claim, verdict, studentPrediction, logEvent }) {
  const [expanded, setExpanded] = useState(false);
  const config = VERDICT_CONFIG[verdict?.verdict] || VERDICT_CONFIG['insufficient_evidence'];

  const handleExpand = () => {
    if (!expanded) {
      logEvent('verdict_expanded', { claim_id: claim.id });
    }
    setExpanded(prev => !prev);
  };

  // No badge for: neutral prediction, or insufficient_evidence verdict (system couldn't determine truth)
  const studentWasCorrect =
    verdict && studentPrediction !== 'neutral' && verdict.verdict !== 'insufficient_evidence'
      ? (studentPrediction === 'false'
          ? verdict.verdict === 'unsupported'
          : verdict.verdict === 'supported')
      : null;

  return (
    <div className={`rounded-lg border p-4 ${config.bgClass} ${config.borderClass}`}>
      <div className="flex items-start gap-3">
        <span className="text-lg leading-none mt-0.5" aria-label={config.label}>
          {config.icon}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-semibold uppercase tracking-wide ${config.textClass}`}>
              {config.label}
            </span>
            {verdict?.confidence != null && (
              <span className="text-xs text-gray-400 tabular-nums">
                {Math.round(verdict.confidence * 100)}% confident
              </span>
            )}
            {studentWasCorrect !== null && (
              <span className={`text-xs font-semibold ml-auto px-2 py-0.5 rounded-full ${studentWasCorrect ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                {studentWasCorrect ? '\u2713 correct' : '\u2717 incorrect'}
              </span>
            )}
          </div>

          {studentPrediction !== 'neutral' && (
            <p className="text-xs text-gray-500 mb-1">
              You said: {studentPrediction === 'accurate' ? 'Accurate' : 'False'}
            </p>
          )}

          <p className="text-sm text-gray-800 leading-relaxed">{claim.text}</p>

          {verdict?.explanation && (
            <button
              onClick={handleExpand}
              className="mt-2 text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
            >
              <span>{expanded ? '\u25be' : '\u25b8'}</span>
              <span>{expanded ? 'Hide explanation' : 'Show explanation'}</span>
            </button>
          )}

          {expanded && verdict?.explanation && (
            <p className="mt-2 text-xs text-gray-600 leading-relaxed border-t border-gray-200 pt-2">
              {verdict.explanation}
            </p>
          )}

          {verdict?.sources && verdict.sources.length > 0 && (
            <div className="mt-2 flex flex-col gap-0.5">
              {verdict.sources.map((source) => (
                <a
                  key={source.url}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:text-blue-800 hover:underline truncate"
                  title={source.title || source.url}
                >
                  {source.title || source.url}
                </a>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ClaimCard({
  mode = 'predict',
  claim,
  // predict mode
  prediction = 'neutral',
  onPredictionChange,
  onExpand,
  onLinkClick,
  // reveal mode
  verdict,
  studentPrediction = 'neutral',
  logEvent,
}) {
  if (mode === 'predict') {
    return (
      <PredictCard
        claim={claim}
        prediction={prediction}
        onPredictionChange={onPredictionChange || (() => {})}
        onExpand={onExpand || (() => {})}
        onLinkClick={onLinkClick || (() => {})}
      />
    );
  }

  return (
    <RevealCard
      claim={claim}
      verdict={verdict}
      studentPrediction={studentPrediction}
      logEvent={logEvent || (() => {})}
    />
  );
}

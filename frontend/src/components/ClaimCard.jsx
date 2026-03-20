import { useState, useEffect, useRef } from 'react';

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

// Predict mode: shows claim + sources + checkbox for prediction
function PredictCard({ claim, checked, reasoning, onCheckChange, onReasoningChange, onExpand, onLinkClick }) {
  const expandedRef = useRef(false);

  const handleCheckChange = (e) => {
    if (!expandedRef.current) {
      expandedRef.current = true;
      onExpand(claim.id);
    }
    onCheckChange(claim.id, e.target.checked);
  };

  const handleLinkClick = (url) => {
    onLinkClick(claim.id, url);
  };

  return (
    <div className="rounded-lg border border-gray-200 p-4 bg-white">
      <p className="text-sm text-gray-800 leading-relaxed mb-3">{claim.text}</p>

      {claim.sources && claim.sources.length > 0 && (
        <div className="mb-3">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Sources</p>
          <div className="flex flex-col gap-1">
            {claim.sources.map((source, idx) => (
              <a
                key={idx}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => handleLinkClick(source.url)}
                className="text-xs text-blue-600 hover:text-blue-800 hover:underline truncate"
                title={source.title || source.url}
              >
                {source.title || source.url}
              </a>
            ))}
          </div>
        </div>
      )}

      <label className="flex items-start gap-2 cursor-pointer group">
        <input
          type="checkbox"
          checked={checked}
          onChange={handleCheckChange}
          className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
        />
        <span className="text-sm text-gray-700 group-hover:text-gray-900 select-none">
          I think this claim might be inaccurate
        </span>
      </label>

      {checked && (
        <div className="mt-2 ml-6">
          <textarea
            value={reasoning}
            onChange={(e) => onReasoningChange(claim.id, e.target.value)}
            placeholder="Optional: why do you think this is inaccurate?"
            rows={2}
            className="w-full resize-none rounded border border-gray-200 px-2 py-1.5 text-xs text-gray-700 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 placeholder-gray-400"
          />
        </div>
      )}
    </div>
  );
}

// Reveal mode: shows verdict + explanation + prediction match
function RevealCard({ claim, verdict, studentPredicted, logEvent }) {
  const [expanded, setExpanded] = useState(false);
  const config = VERDICT_CONFIG[verdict?.verdict] || VERDICT_CONFIG['insufficient_evidence'];

  const handleExpand = () => {
    if (!expanded) {
      logEvent('verdict_expanded', { claim_id: claim.id });
    }
    setExpanded(prev => !prev);
  };

  const studentWasCorrect = verdict
    ? (studentPredicted === (verdict.verdict === 'unsupported'))
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
            {studentWasCorrect !== null && (
              <span className={`text-xs font-medium ml-auto ${studentWasCorrect ? 'text-green-700' : 'text-red-600'}`}>
                {studentWasCorrect ? '\u2713 correct prediction' : '\u2717 incorrect prediction'}
              </span>
            )}
          </div>
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

          {claim.sources && claim.sources.length > 0 && (
            <div className="mt-2 flex flex-col gap-0.5">
              {claim.sources.map((source, idx) => (
                <a
                  key={idx}
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
  checked = false,
  reasoning = '',
  onCheckChange,
  onReasoningChange,
  onExpand,
  onLinkClick,
  // reveal mode
  verdict,
  studentPredicted = false,
  logEvent,
}) {
  if (mode === 'predict') {
    return (
      <PredictCard
        claim={claim}
        checked={checked}
        reasoning={reasoning}
        onCheckChange={onCheckChange}
        onReasoningChange={onReasoningChange}
        onExpand={onExpand || (() => {})}
        onLinkClick={onLinkClick || (() => {})}
      />
    );
  }

  return (
    <RevealCard
      claim={claim}
      verdict={verdict}
      studentPredicted={studentPredicted}
      logEvent={logEvent || (() => {})}
    />
  );
}

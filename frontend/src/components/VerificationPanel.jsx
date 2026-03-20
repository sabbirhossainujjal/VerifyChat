import PredictStep from './PredictStep';
import RevealStep from './RevealStep';

function Spinner() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 text-gray-500 py-8">
      <div className="h-7 w-7 rounded-full border-2 border-gray-300 border-t-blue-500 animate-spin" />
      <span className="text-sm">Analyzing claims...</span>
    </div>
  );
}

export default function VerificationPanel({
  state,
  claims,
  verdicts,
  accuracy,
  predictions,
  error,
  onSubmitPredictions,
  logEvent,
}) {
  return (
    <div className="w-[420px] border-l border-gray-200 flex flex-col overflow-hidden bg-white">
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 shrink-0">
        <h1 className="text-xs font-semibold uppercase tracking-widest text-gray-500">
          Fact Verification
        </h1>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col">
        {state === 'IDLE' && (
          <div className="flex items-center justify-center h-full px-6">
            <p className="text-sm text-gray-400 text-center leading-relaxed">
              Verification results will appear here after you ask a question.
            </p>
          </div>
        )}

        {state === 'ANALYZING' && <Spinner />}

        {error && (
          <div className="mx-4 mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2">
            <p className="text-xs text-red-600">{error}</p>
          </div>
        )}

        {state === 'PREDICT' && claims.length > 0 && (
          <PredictStep
            claims={claims}
            onSubmit={onSubmitPredictions}
            logEvent={logEvent}
          />
        )}

        {state === 'REVEAL' && (
          <RevealStep
            claims={claims}
            verdicts={verdicts}
            accuracy={accuracy}
            predictions={predictions}
            logEvent={logEvent}
          />
        )}
      </div>
    </div>
  );
}

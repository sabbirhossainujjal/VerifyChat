export default function SessionBar({ participantId, sessionId }) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5 bg-gray-800 text-white shrink-0">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold tracking-tight">VerifyChat</span>
        <span className="text-xs text-gray-400 hidden sm:inline">
          &mdash; HCI Study
        </span>
      </div>
      {participantId && (
        <div className="flex items-center gap-3 text-xs text-gray-400">
          <span>
            Participant: <span className="text-gray-200 font-medium">{participantId}</span>
          </span>
          {sessionId && (
            <span>
              Session: <span className="text-gray-200 font-mono">{sessionId.slice(0, 8)}&hellip;</span>
            </span>
          )}
        </div>
      )}
    </div>
  );
}

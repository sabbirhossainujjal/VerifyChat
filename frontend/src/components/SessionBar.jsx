export default function SessionBar({ participantId, sessionId, onLogout }) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5 bg-gray-800 text-white shrink-0">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold tracking-tight">VerifyChat</span>
      </div>
      <div className="flex items-center gap-4">
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
        {onLogout && (
          <button
            onClick={onLogout}
            className="text-xs text-gray-400 hover:text-white border border-gray-600 hover:border-gray-400 rounded px-2.5 py-1 transition-colors"
          >
            Log out
          </button>
        )}
      </div>
    </div>
  );
}

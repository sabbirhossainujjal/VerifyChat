import { useState, useCallback, useRef } from 'react';
import { createSession } from './services/api';
import { useEventLogger } from './hooks/useEventLogger';
import { useChat } from './hooks/useChat';
import { useVerification } from './hooks/useVerification';
import SessionBar from './components/SessionBar';
import ChatPanel from './components/ChatPanel';
import VerificationPanel from './components/VerificationPanel';

// Entry form shown before a session is created
function SessionForm({ onStart }) {
  const [participantId, setParticipantId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = participantId.trim();
    if (!trimmed) {
      setError('Please enter a participant ID.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const session = await createSession(trimmed);
      onStart(trimmed, session.session_id);
    } catch (err) {
      setError('Could not connect to the server. Make sure the backend is running.');
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="w-full max-w-sm bg-white rounded-xl border border-gray-200 shadow-sm p-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">VerifyChat</h1>
        <p className="text-sm text-gray-500 mb-6">
          HCI Study &mdash; Stevens Institute of Technology
        </p>

        <form onSubmit={handleSubmit} noValidate>
          <label htmlFor="participant-id" className="block text-sm font-medium text-gray-700 mb-1.5">
            Participant ID
          </label>
          <input
            id="participant-id"
            type="text"
            value={participantId}
            onChange={(e) => setParticipantId(e.target.value)}
            placeholder="e.g. P001"
            autoFocus
            disabled={loading}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 disabled:bg-gray-50 mb-3"
          />

          {error && (
            <p className="text-xs text-red-600 mb-3">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !participantId.trim()}
            className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Starting session...' : 'Start Session'}
          </button>
        </form>

        <p className="text-xs text-gray-400 mt-4 text-center leading-snug">
          Your responses will be recorded for research purposes.
        </p>
      </div>
    </div>
  );
}

export default function App() {
  const [participantId, setParticipantId] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  // Tracks the predictions from PREDICT state so REVEAL can display them
  const [lastPredictions, setLastPredictions] = useState([]);

  // Track focus panel for panel_focus events
  const focusTimestampRef = useRef({ panel: null, startMs: null });

  const log = useEventLogger(sessionId);

  const handlePanelFocus = useCallback((panel) => {
    const now = Date.now();
    const { panel: prevPanel, startMs } = focusTimestampRef.current;
    if (prevPanel && startMs && prevPanel !== panel) {
      log('panel_focus', { panel: prevPanel, duration_ms: now - startMs });
    }
    if (focusTimestampRef.current.panel !== panel) {
      focusTimestampRef.current = { panel, startMs: now };
    }
  }, [log]);

  // startVerification needs to exist before useChat, so we use a ref to break the cycle
  const startVerificationRef = useRef(null);

  const stableOnResponseComplete = useCallback((messageId, fullResponse) => {
    if (startVerificationRef.current) {
      startVerificationRef.current(messageId, fullResponse);
    }
  }, []);

  const {
    state: verifyState,
    claims,
    verdicts,
    accuracy,
    error: verifyError,
    startVerification,
    submitPrediction,
    reset: resetVerification,
  } = useVerification(sessionId, log);

  // Keep ref current on every render
  startVerificationRef.current = startVerification;

  const { messages, isStreaming, sendMessage } = useChat(
    sessionId,
    stableOnResponseComplete,
    log
  );

  const handleSend = useCallback((text) => {
    // Reset verification panel when user starts a new question from REVEAL state
    if (verifyState === 'REVEAL') {
      resetVerification();
      setLastPredictions([]);
    }
    sendMessage(text);
  }, [verifyState, resetVerification, sendMessage]);

  const handleSubmitPredictions = useCallback((predictions) => {
    setLastPredictions(predictions);
    submitPrediction(predictions);
  }, [submitPrediction]);

  const handleSessionStart = (pid, sid) => {
    setParticipantId(pid);
    setSessionId(sid);
  };

  if (!sessionId) {
    return <SessionForm onStart={handleSessionStart} />;
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-white">
      <SessionBar participantId={participantId} sessionId={sessionId} />

      <div className="flex flex-1 overflow-hidden">
        <div
          className="flex-1 overflow-hidden flex flex-col"
          onMouseEnter={() => handlePanelFocus('chat')}
        >
          <ChatPanel
            messages={messages}
            isStreaming={isStreaming}
            onSend={handleSend}
          />
        </div>

        <div onMouseEnter={() => handlePanelFocus('verification')}>
          <VerificationPanel
            state={verifyState}
            claims={claims}
            verdicts={verdicts}
            accuracy={accuracy}
            predictions={lastPredictions}
            error={verifyError}
            onSubmitPredictions={handleSubmitPredictions}
            logEvent={log}
          />
        </div>
      </div>
    </div>
  );
}

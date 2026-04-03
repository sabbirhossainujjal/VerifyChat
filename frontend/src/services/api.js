const BASE = import.meta.env.VITE_API_URL || '';

export const createSession = (participantId) =>
  fetch(`${BASE}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ participant_id: participantId })
  }).then(r => r.json());

export const sendChatMessage = (sessionId, message) =>
  fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message })
  });  // returns raw Response for streaming

export const verifyClaims = (sessionId, messageId, aiResponse) =>
  fetch(`${BASE}/api/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, ai_response: aiResponse })
  }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); });

export const submitPredictions = (sessionId, messageId, predictions) =>
  fetch(`${BASE}/api/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, predictions })
  }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); });

export const revealVerdicts = (sessionId, messageId, predictionId) =>
  fetch(`${BASE}/api/reveal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, prediction_id: predictionId })
  }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); });

export const logEvent = (sessionId, eventType, eventData = {}) =>
  fetch(`${BASE}/api/log`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, event_type: eventType, event_data: eventData, timestamp: new Date().toISOString() })
  }).catch(() => {});  // silent failure

export const sendStandardChatMessage = (sessionId, message) =>
  fetch(`${BASE}/api/chat/standard`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message })
  });  // returns raw Response for streaming

export const submitGuess = (sessionId, messageId, guessText) =>
  fetch(`${BASE}/api/guess`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message_id: messageId, guess_text: guessText })
  }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); });

export const setSessionMode = (sessionId, mode) =>
  fetch(`${BASE}/api/session/mode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, mode })
  }).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); });

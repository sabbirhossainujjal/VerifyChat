import { useReducer, useCallback } from 'react';
import { verifyClaims, submitPredictions, revealVerdicts } from '../services/api';

// State machine: IDLE -> ANALYZING -> PREDICT -> REVEAL
const initialState = {
  status: 'IDLE',
  claims: [],
  verdicts: [],
  accuracy: null,
  currentMessageId: null,
  predictionId: null,
  error: null,
};

function reducer(state, action) {
  switch (action.type) {
    case 'START_ANALYZING':
      return { ...state, status: 'ANALYZING', currentMessageId: action.messageId, error: null };
    case 'CLAIMS_READY':
      return { ...state, status: 'PREDICT', claims: action.claims };
    case 'REVEAL_READY':
      return {
        ...state,
        status: 'REVEAL',
        verdicts: action.verdicts,
        accuracy: action.accuracy,
        predictionId: action.predictionId,
      };
    case 'SET_ERROR':
      return { ...state, status: 'IDLE', error: action.error };
    case 'RESET':
      return { ...initialState };
    default:
      return state;
  }
}

export function useVerification(sessionId, logEvent) {
  const [state, dispatch] = useReducer(reducer, initialState);

  const startVerification = useCallback(async (messageId, aiResponse) => {
    dispatch({ type: 'START_ANALYZING', messageId });
    try {
      const result = await verifyClaims(sessionId, messageId, aiResponse);
      const claims = result.claims || [];
      dispatch({ type: 'CLAIMS_READY', claims });
      logEvent('claims_displayed', {
        num_claims: claims.length,
        claim_ids: claims.map(c => c.id),
      });
    } catch (err) {
      logEvent('pipeline_error', { stage: 'verify', error: String(err) });
      dispatch({ type: 'SET_ERROR', error: 'Failed to extract claims. Please try again.' });
    }
  }, [sessionId, logEvent]);

  const submitPrediction = useCallback(async (predictions) => {
    const predictedInaccurate = predictions.filter(p => p.predicted_inaccurate);
    logEvent('prediction_submitted', {
      num_predicted_inaccurate: predictedInaccurate.length,
      claim_ids: predictedInaccurate.map(p => p.claim_id),
    });

    const predictionStartMs = Date.now();

    try {
      const predictResult = await submitPredictions(sessionId, state.currentMessageId, predictions);
      const revealResult = await revealVerdicts(sessionId, state.currentMessageId, predictResult.prediction_id);

      dispatch({
        type: 'REVEAL_READY',
        verdicts: revealResult.verdicts || [],
        accuracy: revealResult.accuracy,
        predictionId: predictResult.prediction_id,
      });

      logEvent('reveal_viewed', {
        time_since_prediction_ms: Date.now() - predictionStartMs,
      });
    } catch (err) {
      logEvent('pipeline_error', { stage: 'reveal', error: String(err) });
      dispatch({ type: 'SET_ERROR', error: 'Failed to submit predictions. Please try again.' });
    }
  }, [sessionId, state.currentMessageId, logEvent]);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  return {
    state: state.status,
    claims: state.claims,
    verdicts: state.verdicts,
    accuracy: state.accuracy,
    error: state.error,
    currentMessageId: state.currentMessageId,
    startVerification,
    submitPrediction,
    reset,
  };
}

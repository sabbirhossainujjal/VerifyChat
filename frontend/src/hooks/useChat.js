import { useState, useCallback, useRef } from 'react';
import { sendChatMessage } from '../services/api';

export function useChat(sessionId, onResponseComplete, logEvent) {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const accRef = useRef('');

  const sendMessage = useCallback(async (text) => {
    if (!sessionId || isStreaming) return;

    logEvent('message_sent', { message_length: text.length });

    setMessages(prev => [
      ...prev,
      { role: 'user', content: text },
      { role: 'assistant', content: '' }
    ]);
    setIsStreaming(true);
    accRef.current = '';

    try {
      const response = await sendChatMessage(sessionId, text);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let lineBuffer = '';
      let messageId = null;
      let fullResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        lineBuffer += decoder.decode(value, { stream: true });
        const lines = lineBuffer.split('\n');
        lineBuffer = lines.pop(); // keep incomplete last line

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          let data;
          try {
            data = JSON.parse(line.slice(6));
          } catch (e) {
            continue; // skip malformed JSON
          }
          if (data.done) {
            messageId = data.message_id;
            fullResponse = data.full_response;
            setIsStreaming(false);
            logEvent('response_received', { response_length: fullResponse.length, message_id: messageId });
            onResponseComplete(messageId, fullResponse);
          } else {
            accRef.current += data.token;
            const snapshot = accRef.current;
            setMessages(prev => {
              const updated = [...prev];
              updated[updated.length - 1] = { ...updated[updated.length - 1], content: snapshot };
              return updated;
            });
          }
        }
      }
    } catch (err) {
      setIsStreaming(false);
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { ...updated[updated.length - 1], content: '[Error: could not get response]' };
        return updated;
      });
    }
  }, [sessionId, isStreaming, onResponseComplete, logEvent]);

  return { messages, isStreaming, sendMessage };
}

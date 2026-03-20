import { useState, useCallback } from 'react';
import { sendChatMessage } from '../services/api';

export function useChat(sessionId, onResponseComplete, logEvent) {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useCallback(async (text) => {
    if (!sessionId || isStreaming) return;

    logEvent('message_sent', { message_length: text.length });

    setMessages(prev => [
      ...prev,
      { role: 'user', content: text },
      { role: 'assistant', content: '' }
    ]);
    setIsStreaming(true);

    try {
      const response = await sendChatMessage(sessionId, text);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      let messageId = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.done) {
              messageId = data.message_id;
              fullResponse = data.full_response;
              setIsStreaming(false);
              logEvent('response_received', { response_length: fullResponse.length, message_id: messageId });
              onResponseComplete(messageId, fullResponse);
            } else {
              fullResponse += data.token;
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { ...updated[updated.length - 1], content: fullResponse };
                return updated;
              });
            }
          } catch (e) { /* ignore parse errors */ }
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

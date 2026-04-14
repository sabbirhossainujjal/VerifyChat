import { useState, useCallback, useRef } from 'react';
import { sendStandardChatMessage } from '../services/api';

export function useStandardChat(sessionId, log) {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [lastMessageId, setLastMessageId] = useState(null);
  const abortRef = useRef(null);

  const sendMessage = useCallback(async (text) => {
    if (!sessionId || !text.trim()) return;

    setLastMessageId(null);  // reset on new message

    setMessages(prev => [
      ...prev,
      { role: 'user', content: text },
      { role: 'assistant', content: '' }
    ]);
    setIsStreaming(true);

    try {
      const resp = await sendStandardChatMessage(sessionId, text);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let inMeta = false;  // suppress <META>...</META> from display

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.done) {
              if (data.full_response) {
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = { role: 'assistant', content: data.full_response };
                  return updated;
                });
              }
              if (data.message_id) setLastMessageId(data.message_id);
            } else if (data.token) {
              let displayToken = data.token;

              // Strip <META>...</META> block from displayed tokens
              if (!inMeta && displayToken.includes('<META>')) {
                displayToken = displayToken.split('<META>')[0];
                inMeta = true;
              } else if (inMeta) {
                displayToken = '';
                if (data.token.includes('</META>')) inMeta = false;
              }

              if (displayToken) {
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    role: 'assistant',
                    content: (updated[updated.length - 1].content || '') + displayToken
                  };
                  return updated;
                });
              }
            }
          } catch {}
        }
      }
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: 'assistant', content: '[Error: could not get response]' };
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  }, [sessionId]);

  return { messages, isStreaming, lastMessageId, sendMessage };
}

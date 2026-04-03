import { useState } from 'react';

export default function GuessInput({ sessionId, messageId, onSubmit }) {
  const [text, setText] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!text.trim() || loading) return;
    setLoading(true);
    try {
      await onSubmit(text.trim());
      setSubmitted(true);
    } catch {}
    setLoading(false);
  };

  if (submitted) {
    return (
      <div className="mx-4 mb-4 rounded-lg border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-500">
        Response recorded.
      </div>
    );
  }

  return (
    <div className="mx-4 mb-4 rounded-lg border border-blue-100 bg-blue-50 p-4">
      <p className="text-xs font-medium text-blue-700 mb-2">
        Did you notice anything that might be inaccurate in the response?
      </p>
      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="Describe anything that seemed incorrect or doubtful..."
        rows={3}
        className="w-full rounded-md border border-blue-200 bg-white px-3 py-2 text-sm text-gray-700 placeholder-gray-400 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400 resize-none"
      />
      <div className="flex justify-end mt-2">
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || loading}
          className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Submitting...' : 'Submit'}
        </button>
      </div>
    </div>
  );
}

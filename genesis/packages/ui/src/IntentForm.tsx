import { FormEvent, useState } from "react";

type IntentFormProps = {
  onSubmit: (message: string) => Promise<void> | void;
  disabled?: boolean;
  initialValue?: string;
};

export function IntentForm({ onSubmit, disabled, initialValue = "" }: IntentFormProps) {
  const [message, setMessage] = useState(initialValue);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!message.trim() || busy || disabled) return;
    setBusy(true);
    try {
      await onSubmit(message.trim());
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="g-intent-form" onSubmit={handleSubmit}>
      <label className="g-label" htmlFor="intent-message">
        Ask Jonathan
      </label>
      <textarea
        id="intent-message"
        className="g-textarea"
        rows={3}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Schedule a meeting with Bob tomorrow at 10"
        disabled={busy || disabled}
      />
      <button className="g-button g-button-primary" type="submit" disabled={busy || disabled || !message.trim()}>
        {busy ? "Sending…" : "Submit intent"}
      </button>
    </form>
  );
}

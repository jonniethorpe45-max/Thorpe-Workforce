import { useEffect, useMemo, useRef, useState } from "react";
import { SafeMarkdown } from "./SafeMarkdown";
import { DEFAULT_WORD_REVEAL_MS, tokenizeForReveal } from "../../lib/wordByWord";

interface WordByWordReplyProps {
  content: string;
  animate: boolean;
  intervalMs?: number;
  onComplete?: () => void;
  onProgress?: () => void;
}

export function WordByWordReply({
  content,
  animate,
  intervalMs = DEFAULT_WORD_REVEAL_MS,
  onComplete,
  onProgress,
}: WordByWordReplyProps) {
  const tokens = useMemo(() => tokenizeForReveal(content), [content]);
  const [visibleCount, setVisibleCount] = useState(() => (animate ? 0 : tokens.length));
  const [isComplete, setIsComplete] = useState(() => !animate);
  const onCompleteRef = useRef(onComplete);
  const onProgressRef = useRef(onProgress);

  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    onProgressRef.current = onProgress;
  }, [onProgress]);

  useEffect(() => {
    if (!animate) {
      setVisibleCount(tokens.length);
      setIsComplete(true);
      return;
    }

    setVisibleCount(0);
    setIsComplete(false);

    if (tokens.length === 0) {
      setIsComplete(true);
      onCompleteRef.current?.();
      return;
    }

    const timer = window.setInterval(() => {
      setVisibleCount((current) => {
        const next = current + 1;
        onProgressRef.current?.();

        if (next >= tokens.length) {
          window.clearInterval(timer);
          setIsComplete(true);
          onCompleteRef.current?.();
        }

        return Math.min(next, tokens.length);
      });
    }, intervalMs);

    return () => window.clearInterval(timer);
  }, [animate, content, intervalMs, tokens.length]);

  const visibleText = tokens.slice(0, visibleCount).join("");

  return (
    <span className="inline">
      <SafeMarkdown content={visibleText} />
      {animate && !isComplete && (
        <span
          className="ml-0.5 inline-block animate-pulse text-thorpe-primary"
          aria-hidden="true"
        >
          ▍
        </span>
      )}
    </span>
  );
}

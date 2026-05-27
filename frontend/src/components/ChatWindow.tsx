import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types/dialogue";
import { IconRobot, IconSpinner } from "./Icons";
import { MessageBubble } from "./MessageBubble";

interface ChatWindowProps {
  messages: ChatMessage[];
  loading: boolean;
  showTechnicalDetails: boolean;
}

export function ChatWindow({
  messages,
  loading,
  showTechnicalDetails,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="chat-window" role="log" aria-live="polite">
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          showTechnicalDetails={showTechnicalDetails}
        />
      ))}
      {loading && (
        <div className="message-row message-row--assistant">
          <div className="message-bubble message-bubble--assistant message-bubble--loading">
            <div className="message-bubble__header">
              <IconRobot className="message-bubble__icon" size={14} />
              <span className="message-bubble__role">VulnAssist</span>
            </div>
            <div className="message-bubble__spinner-row">
              <IconSpinner size={20} />
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

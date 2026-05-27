import type { ChatMessage } from "../types/dialogue";
import { IconRobot, IconUser } from "./Icons";

interface MessageBubbleProps {
  message: ChatMessage;
  showTechnicalDetails: boolean;
}

export function MessageBubble({
  message,
  showTechnicalDetails,
}: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "message-row--user" : "message-row--assistant"}`}>
      <div className={`message-bubble ${isUser ? "message-bubble--user" : "message-bubble--assistant"}`}>
        <div className="message-bubble__header">
          {isUser ? (
            <IconUser className="message-bubble__icon" size={14} />
          ) : (
            <IconRobot className="message-bubble__icon" size={14} />
          )}
          <span className="message-bubble__role">{isUser ? "You" : "VulnAssist"}</span>
        </div>
        <p className="message-bubble__text">{message.text}</p>
        {!isUser && showTechnicalDetails && message.meta && (
          <TechnicalDetails meta={message.meta} />
        )}
      </div>
    </div>
  );
}

function TechnicalDetails({ meta }: { meta: NonNullable<ChatMessage["meta"]> }) {
  const { nlu, dialogue, retrieval } = meta;

  return (
    <details className="technical-details" open>
      <summary>Pipeline details</summary>
      <dl className="technical-details__list">
        <dt>Intent</dt>
        <dd>
          {nlu.intent} ({(nlu.intent_confidence * 100).toFixed(0)}%)
        </dd>
        <dt>Dialogue state</dt>
        <dd>{dialogue.state}</dd>
        {Object.keys(dialogue.slots).length > 0 && (
          <>
            <dt>Slots</dt>
            <dd>{JSON.stringify(dialogue.slots)}</dd>
          </>
        )}
        {nlu.entities.length > 0 && (
          <>
            <dt>Entities</dt>
            <dd>
              {nlu.entities
                .map((e) => `${e.entity_type}: ${e.value}`)
                .join(", ")}
            </dd>
          </>
        )}
        {retrieval && (
          <>
            <dt>Source</dt>
            <dd>{retrieval.source ?? "unknown"}</dd>
            {(retrieval.cves ?? []).slice(0, 3).map((cve) => (
              <div key={cve.cve_id} className="technical-details__cve">
                <dt>{cve.cve_id}</dt>
                <dd>
                  {cve.severity ?? "N/A"}
                  {cve.cvss_score != null ? ` · CVSS ${cve.cvss_score}` : ""}
                </dd>
              </div>
            ))}
          </>
        )}
      </dl>
    </details>
  );
}

import type {
  DialogueMessageRequest,
  DialogueMessageResponse,
} from "../types/dialogue";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export class DialogueApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "DialogueApiError";
  }
}

/** POST /v1/dialogue/message — sole HTTP entry point for the chat UI. */
export async function sendMessage(
  text: string,
  sessionId: string | null,
): Promise<DialogueMessageResponse> {
  const payload: DialogueMessageRequest = { text, session_id: sessionId };

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/v1/dialogue/message`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new DialogueApiError(
      "Cannot reach the API. Start the backend with: uvicorn backend.api.main:app --reload",
    );
  }

  if (!response.ok) {
    throw new DialogueApiError(
      `Request failed (${response.status}). Check that the backend is running.`,
    );
  }

  return (await response.json()) as DialogueMessageResponse;
}

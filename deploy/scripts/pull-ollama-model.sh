#!/bin/sh
# One-shot init: wait for Ollama then pull the configured model tag.
set -e

MODEL="${OLLAMA_MODEL:-llama3.2}"
HOST="${OLLAMA_HOST:-http://ollama:11434}"

echo "Waiting for Ollama at ${HOST}..."
until OLLAMA_HOST="${HOST}" ollama list >/dev/null 2>&1; do
  sleep 2
done

echo "Pulling Ollama model: ${MODEL}"
OLLAMA_HOST="${HOST}" ollama pull "${MODEL}"
echo "Model ${MODEL} ready."

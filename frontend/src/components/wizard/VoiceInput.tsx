"use client";

import { useState, useCallback, useRef } from "react";
import { Mic, MicOff } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  onTranscript: (text: string) => void;
}

type SpeechRecognitionType = {
  start: () => void;
  stop: () => void;
  onresult: ((event: { results: { [key: number]: { transcript: string }[] }; resultIndex: number }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  continuous: boolean;
  interimResults: boolean;
  lang: string;
};

function getSpeechRecognition(): (new () => SpeechRecognitionType) | null {
  if (typeof window === "undefined") return null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const W = window as any;
  return W.SpeechRecognition || W.webkitSpeechRecognition || null;
}

export function VoiceInput({ onTranscript }: Props) {
  const [listening, setListening] = useState(false);
  const [unsupported, setUnsupported] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionType | null>(null);

  const handleClick = useCallback(() => {
    if (listening && recognitionRef.current) {
      recognitionRef.current.stop();
      setListening(false);
      return;
    }

    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition) {
      setUnsupported(true);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      const result = event.results[event.resultIndex];
      if (result?.[0]?.transcript) {
        onTranscript(result[0].transcript);
      }
    };

    recognition.onerror = () => {
      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, [listening, onTranscript]);

  return (
    <div className="inline-flex items-center gap-2">
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={handleClick}
        aria-label={listening ? "Stop voice input" : "Start voice input"}
        className={listening ? "border-destructive text-destructive" : ""}
      >
        {listening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
        <span className="ml-1 text-xs">{listening ? "Stop" : "Voice"}</span>
      </Button>
      {unsupported && (
        <span className="text-xs text-muted-foreground">
          Voice input not supported in this browser
        </span>
      )}
    </div>
  );
}

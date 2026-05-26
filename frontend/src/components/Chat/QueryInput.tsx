/**
 * Query Input Component - Chat interface for entering research queries
 */
import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Mic, MicOff, Paperclip } from 'lucide-react';
import { StopButton } from '../../components/StopButton';
import { classifyQuery } from '../../services/api';
import type { Sector } from '../../types/research';

interface QueryInputProps {
  onQuerySubmit: (query: string, sector: Sector) => void;
  onFileAttach?: (file: File) => void;
  disabled?: boolean;
  hasPlan?: boolean;
  onStartResearch?: () => void;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: (event: SpeechRecognitionEvent) => void;
  onerror: (event: SpeechRecognitionErrorEvent) => void;
  onend: () => void;
}

interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
  message: string;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

export default function QueryInput({ onQuerySubmit, onFileAttach, disabled = false, hasPlan = false, onStartResearch }: QueryInputProps) {

  // Abort controller for ongoing classification request
  const abortControllerRef = useRef<AbortController | null>(null);
  // Component state
  const [query, setQuery] = useState('');
  const [isClassifying, setIsClassifying] = useState(false);
  const [sector, setSector] = useState<Sector | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lastProcessedIndexRef = useRef<number>(0);
  const finalTranscriptRef = useRef<string>('');

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('Speech recognition not supported in this browser');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interimTranscript = '';
      const startIndex = Math.max(event.resultIndex, lastProcessedIndexRef.current);
      
      for (let i = startIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscriptRef.current += transcript + ' ';
          lastProcessedIndexRef.current = i + 1;
        } else {
          interimTranscript += transcript;
        }
      }

      const fullTranscript = finalTranscriptRef.current + interimTranscript;
      setQuery(fullTranscript.trim());
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      lastProcessedIndexRef.current = 0;
      finalTranscriptRef.current = '';
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  useEffect(() => {
    if (textareaRef.current && !query.trim()) {
      textareaRef.current.style.height = '52px';
    }
  }, [query]);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      lastProcessedIndexRef.current = 0;
      finalTranscriptRef.current = '';
    } else {
      try {
        lastProcessedIndexRef.current = 0;
        finalTranscriptRef.current = '';
        recognitionRef.current.start();
        setIsListening(true);
      } catch (error) {
        console.error('Error starting speech recognition:', error);
        setIsListening(false);
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAttachedFile(file);
      if (onFileAttach) {
        onFileAttach(file);
      }
    }
  };

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const removeFile = () => {
    setAttachedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim() || disabled) return;

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    if (hasPlan && onStartResearch) {
      onStartResearch();
      setQuery('');
      lastProcessedIndexRef.current = 0;
      finalTranscriptRef.current = '';
      return;
    }

    setIsClassifying(true);

    // Create a fresh AbortController for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const classification = await classifyQuery({ query, signal: abortController.signal });
      const detectedSector = classification.sector || 'Unknown';
      setSector(detectedSector);
      onQuerySubmit(query, detectedSector);
      setQuery('');
      lastProcessedIndexRef.current = 0;
      finalTranscriptRef.current = '';
    } catch (error) {
      if ((error as any).name === 'AbortError') {
        console.log('Classification aborted by user');
      } else {
        console.error('Error classifying query:', error);
        setSector('Unknown');
        onQuerySubmit(query, 'Unknown');
      }
      setQuery('');
      lastProcessedIndexRef.current = 0;
      finalTranscriptRef.current = '';
    } finally {
      setIsClassifying(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="space-y-2">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              id="query-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={hasPlan ? "Type your answers here and press Enter to start research..." : "Message FinScope AI..."}
              disabled={disabled || isClassifying}
              rows={1}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                if (!target.value.trim()) {
                  target.style.height = '52px';
                } else {
                  target.style.height = 'auto';
                  target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  // Ctrl+Enter or Cmd+Enter -> insert a newline at cursor position
                  if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    const textarea = textareaRef.current;
                    if (textarea) {
                      const { selectionStart, selectionEnd } = textarea;
                      const newValue = query.slice(0, selectionStart) + '\n' + query.slice(selectionEnd);
                      setQuery(newValue);
                      // Move cursor after the inserted newline
                      setTimeout(() => {
                        textarea.selectionStart = textarea.selectionEnd = selectionStart + 1;
                      }, 0);
                    }
                    return;
                  }
                  // Normal Enter (without Shift/Ctrl/Meta) -> submit form
                  if (!e.shiftKey && !e.ctrlKey && !e.metaKey) {
                    e.preventDefault();
                    handleSubmit(e as any);
                  }
                }
              }}
              className={`w-full pl-4 pr-28 py-3.5 bg-fs-card border rounded-2xl text-base text-white resize-none focus:outline-none focus:ring-1 focus:ring-zinc-500 focus:border-zinc-500 disabled:bg-fs-panel disabled:cursor-not-allowed placeholder:text-zinc-400 overflow-hidden ${
                isListening ? 'border-zinc-400 ring-1 ring-zinc-400' : 'border-fs-border'
              }`}
              style={{ maxHeight: '200px', minHeight: '52px', height: query.trim() ? 'auto' : '52px' }}
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.doc,.docx"
                onChange={handleFileSelect}
                className="hidden"
              />
              <button
                type="button"
                onClick={handleFileButtonClick}
                disabled={disabled || isClassifying}
                className="p-1.5 rounded-lg text-zinc-500 hover:bg-fs-elevated hover:text-zinc-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                title="Attach file"
              >
                <Paperclip className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={toggleListening}
                disabled={disabled || isClassifying}
                className={`p-1.5 rounded-lg transition-colors flex items-center justify-center ${
                  isListening
                    ? 'bg-zinc-200 text-zinc-900 hover:bg-white'
                    : 'text-zinc-500 hover:bg-fs-elevated hover:text-zinc-300'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
                title={isListening ? 'Stop recording' : 'Start voice input'}
              >
                {isListening ? (
                  <MicOff className="w-4 h-4" />
                ) : (
                  <Mic className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
          <button
  type="submit"
  disabled={!query.trim() || disabled || isClassifying}
  className="p-3 bg-red-600 text-white rounded-2xl hover:bg-red-700 disabled:bg-fs-elevated disabled:text-zinc-600 disabled:cursor-not-allowed flex items-center justify-center transition-colors flex-shrink-0 shadow-glow"
  title="Send message"
>
  {isClassifying ? (
    <Loader2 className="w-5 h-5 animate-spin" />
  ) : (
    <Send className="w-5 h-5" />
  )}
</button>
{isClassifying && <StopButton onClick={() => abortControllerRef.current?.abort()} className="ml-2" title="Stop" />}
        </div>
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-2">
            {attachedFile && (
              <div className="flex items-center gap-1.5 px-2 py-1 bg-fs-elevated text-zinc-300 rounded-lg text-xs border border-fs-border">
                <Paperclip className="w-3 h-3" />
                <span className="max-w-[200px] truncate">{attachedFile.name}</span>
                <button
                  type="button"
                  onClick={removeFile}
                  className="ml-1 hover:text-fs-highlight"
                  title="Remove file"
                >
                  ×
                </button>
              </div>
            )}
          </div>
          <div className="flex items-center gap-4">
            {isListening && (
              <p className="text-xs text-white flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse"></span>
                Listening...
              </p>
            )}
            {sector && !isListening && (
              <p className="text-xs text-zinc-400">
                Sector: <span className="font-bold text-white">{sector}</span>
              </p>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}

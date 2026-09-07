import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '../types/assessment';
import { api } from '../services/api';
import {
  X,
  Send,
  Sparkles,
  BookOpen,
  Bot,
  User,
  Loader2,
  Mic,
  MicOff,
  Volume2,
  Languages,
  CheckCircle2
} from 'lucide-react';

interface ContextualChatDrawerProps {
  applicationId: string;
  productName: string;
  standardId: string;
  onClose: () => void;
}

const INDIAN_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी (Hindi)' },
  { code: 'mr', label: 'मराठी (Marathi)' },
  { code: 'bn', label: 'বাংলা (Bengali)' },
  { code: 'gu', label: 'ગુજરાતી (Gujarati)' },
  { code: 'ta', label: 'தமிழ் (Tamil)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
  { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
  { code: 'ml', label: 'മലയാളം (Malayalam)' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ (Punjabi)' },
  { code: 'or', label: 'ଓଡ଼ିଆ (Odia)' },
  { code: 'as', label: 'অসমীয়া (Assamese)' },
];

export const ContextualChatDrawer: React.FC<ContextualChatDrawerProps> = ({
  applicationId,
  productName,
  standardId,
  onClose,
}) => {
  const [selectedLang, setSelectedLang] = useState('en');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I am your 12-language grounded BIS certification assistant for **${productName}** evaluated under **${standardId}**. You can speak or ask about compliance gaps, clause mandates, missing documents, or application status in any of the 12 supported Indian languages.`,
      citations: [{ standard_id: standardId, clause: 'Overview', title: 'Scope & Requirements' }],
      created_at: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [activeAudio, setActiveAudio] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const voiceRes = await api.queryVoiceAssistant(applicationId, {
        language_code: selectedLang,
        query_text: text.trim(),
      });

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        content: voiceRes.response,
        citations: voiceRes.citations || [],
        created_at: voiceRes.created_at || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, botMsg]);
      if (voiceRes.audio_data) {
        setActiveAudio(voiceRes.audio_data);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: 'Unable to reach the assistant service. Please check your connection or retry in English.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleRecording = () => {
    if (!isRecording) {
      setIsRecording(true);
      // Simulated voice capture prompt for browser demo
      setTimeout(() => {
        setIsRecording(false);
        const sampleSpoken = selectedLang === 'hi' ? 'मेरे आवेदन में क्या कमियां बाकी हैं?' : 'What gaps are left in my application?';
        handleSend(sampleSpoken);
      }, 2500);
    } else {
      setIsRecording(false);
    }
  };

  const samplePrompts = [
    'What gaps are left?',
    'What does Clause 7 require?',
    'What documents are missing?',
    'Why did my readiness score decrease?',
    'Show me the application status',
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end">
      <div
        className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="px-5 py-3.5 bg-gradient-to-r from-slate-50 to-white border-b border-slate-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-700 border border-brand-200 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-brand-600" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Multilingual Voice & Chat</h3>
              <p className="text-[10px] text-slate-500">12 Indian Languages • Grounded in {standardId}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Language Selection Selector Bar */}
        <div className="px-4 py-2 bg-slate-100/70 border-b border-slate-200 flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-xs text-slate-600">
            <Languages className="w-3.5 h-3.5 text-brand-600" />
            <span className="font-semibold text-[11px]">Language:</span>
          </div>

          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            className="text-xs font-semibold px-2 py-1 bg-white border border-slate-300 rounded-lg focus:ring-1 focus:ring-brand-500 focus:outline-hidden"
          >
            {INDIAN_LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.label}
              </option>
            ))}
          </select>
        </div>

        {/* Chat History */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4 text-xs">
          {messages.map((msg) => {
            const isBot = msg.role === 'assistant';
            return (
              <div
                key={msg.id}
                className={`flex gap-2.5 ${isBot ? 'justify-start' : 'justify-end'}`}
              >
                {isBot && (
                  <div className="w-6 h-6 rounded-md bg-brand-100 text-brand-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] p-3 rounded-2xl space-y-2 ${
                    isBot
                      ? 'bg-slate-50 border border-slate-200 text-slate-800'
                      : 'bg-brand-600 text-white shadow-sm'
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                  {/* Citations Tag */}
                  {isBot && msg.citations && msg.citations.length > 0 && (
                    <div className="pt-1.5 border-t border-slate-200/60 flex flex-wrap gap-1">
                      {msg.citations.map((c, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-white text-brand-800 border border-slate-200 shadow-2xs"
                        >
                          <BookOpen className="w-2.5 h-2.5 text-brand-600" />
                          <span>{c.standard_id} Clause {c.clause}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {!isBot && (
                  <div className="w-6 h-6 rounded-md bg-slate-800 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            );
          })}

          {loading && (
            <div className="flex gap-2.5 items-center text-slate-500">
              <div className="w-6 h-6 rounded-md bg-brand-50 text-brand-700 flex items-center justify-center">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              </div>
              <span className="text-[11px] italic">Processing in {INDIAN_LANGUAGES.find(l => l.code === selectedLang)?.label}...</span>
            </div>
          )}

          {isRecording && (
            <div className="flex gap-2 items-center p-2 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 animate-pulse text-xs">
              <Mic className="w-4 h-4 text-rose-600" />
              <span>Listening to Indian speech ({INDIAN_LANGUAGES.find(l => l.code === selectedLang)?.label})...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="p-2.5 bg-slate-50/70 border-t border-slate-100 flex gap-1.5 overflow-x-auto">
          {samplePrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(p)}
              className="px-2.5 py-1 text-[11px] font-semibold text-slate-700 bg-white hover:bg-brand-50 hover:text-brand-700 hover:border-brand-300 rounded-full border border-slate-200 transition-colors whitespace-nowrap shadow-2xs"
            >
              {p}
            </button>
          ))}
        </div>

        {/* Input Bar with Mic Button */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="p-3 bg-white border-t border-slate-200 flex items-center gap-2 flex-shrink-0"
        >
          <button
            type="button"
            onClick={toggleRecording}
            className={`p-2.5 rounded-xl border transition-colors ${
              isRecording
                ? 'bg-rose-600 text-white border-rose-600 animate-pulse'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border-slate-300'
            }`}
            title="Speak query"
          >
            {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`Ask in ${INDIAN_LANGUAGES.find(l => l.code === selectedLang)?.label}...`}
            className="flex-1 px-3.5 py-2 text-xs bg-slate-50 border border-slate-300 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-brand-500"
          />

          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white shadow-sm disabled:opacity-50 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};

import { useState, useEffect, useRef } from "react";
import { X, Send, Sparkles, Globe, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

const BACKEND_URL = 'https://rail-madad-chatbot-1094417494880.asia-south1.run.app';

type Message = {
  id: string;
  role: 'user' | 'bot';
  text: string;
  buttons?: { text: string }[];
};

const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'mr', label: 'मराठी' }
];

export function ChatbotCapsule() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Language States
  const [language, setLanguage] = useState("en");
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);

  const sessionIdRef = useRef("session-" + Math.random().toString(36).substring(7));
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasInitialized = useRef(false);

  const currentLangLabel = SUPPORTED_LANGUAGES.find(l => l.code === language)?.label || 'English';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    if (!hasInitialized.current) {
      hasInitialized.current = true;
      sendMessageToApi("Hi", true);
    }
  }, []);

  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
    setMessages([]); // Clear chat UI
    sessionIdRef.current = "session-" + Math.random().toString(36).substring(7); // Reset Dialogflow context
    sendMessageToApi("Hi", true, newLang); // Fetch new greeting in selected language
  };

  const sendMessageToApi = async (text: string, isHiddenInit = false, overrideLang?: string) => {
    if (!text.trim()) return;

    if (!isHiddenInit) {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', text }]);
    }
    
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/chat_proxy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            "message": text, 
            "language": overrideLang || language,
            "session_id": sessionIdRef.current
        })
      });

      const data = await response.json();
      
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: 'bot', 
        text: data.reply,
        buttons: data.buttons 
      }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: 'bot', 
        text: "AI server connection error. Please try again." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = message;
    setMessage(""); 
    sendMessageToApi(text); 
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="absolute bottom-full mb-4 left-1/2 -translate-x-1/2 w-96 max-w-[calc(100vw-2rem)]"
          >
            <div className="bg-white rounded-3xl shadow-2xl border border-indigo-100 overflow-hidden flex flex-col h-[520px]">
              
              {/* Header */}
              <div className="bg-gradient-to-r from-indigo-600 to-blue-600 px-4 py-3.5 flex items-center justify-between shadow-md z-10">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="size-8 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/30">
                      <Sparkles className="size-4 text-white" />
                    </div>
                    <div className="absolute bottom-0 right-0 size-2.5 bg-green-400 rounded-full border-2 border-indigo-600 animate-pulse" />
                  </div>
                  <div>
                    <span className="text-white font-bold text-sm block leading-tight">RailBot Assistant</span>
                    <span className="text-[10px] text-indigo-100 uppercase tracking-widest font-semibold">Live AI Agent</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  
                  {/* BEAUTIFIED CUSTOM LANGUAGE SELECTOR */}
                  <div className="relative">
                    <button 
                      onClick={() => setIsLangMenuOpen(!isLangMenuOpen)}
                      className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 border border-white/20 transition-all rounded-full px-3 py-1.5 backdrop-blur-md text-white text-xs font-bold shadow-sm"
                    >
                      <Globe className="size-3.5 text-indigo-100" />
                      <span>{currentLangLabel}</span>
                      <ChevronDown className={`size-3.5 transition-transform duration-300 ${isLangMenuOpen ? 'rotate-180' : ''}`} />
                    </button>

                    <AnimatePresence>
                      {isLangMenuOpen && (
                        <>
                          {/* Invisible overlay to close menu when clicking outside */}
                          <div 
                            className="fixed inset-0 z-40"
                            onClick={() => setIsLangMenuOpen(false)}
                          />
                          
                          {/* The Dropdown Menu */}
                          <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            transition={{ duration: 0.15, ease: "easeOut" }}
                            className="absolute top-full right-0 mt-2 w-36 bg-white rounded-2xl shadow-2xl border border-indigo-100 overflow-hidden z-50 origin-top-right"
                          >
                            <div className="py-1.5 px-1.5 flex flex-col gap-1">
                              {SUPPORTED_LANGUAGES.map((lang) => (
                                <button
                                  key={lang.code}
                                  onClick={() => {
                                    setIsLangMenuOpen(false);
                                    handleLanguageChange(lang.code);
                                  }}
                                  className={`w-full flex items-center justify-between px-3 py-2 text-sm rounded-xl transition-all ${
                                    language === lang.code 
                                      ? 'bg-indigo-50 text-indigo-700 font-bold' 
                                      : 'text-slate-600 hover:bg-slate-50 hover:text-indigo-600 font-medium'
                                  }`}
                                >
                                  {lang.label}
                                  {language === lang.code && <div className="size-1.5 rounded-full bg-indigo-600 shadow-sm" />}
                                </button>
                              ))}
                            </div>
                          </motion.div>
                        </>
                      )}
                    </AnimatePresence>
                  </div>

                  <button
                    onClick={() => setIsOpen(false)}
                    className="size-7 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
                  >
                    <X className="size-4" />
                  </button>
                </div>
              </div>

              {/* Chat Area */}
              <div className="flex-1 p-4 overflow-y-auto bg-slate-50/50 scroll-smooth">
                {messages.length === 0 && !isLoading && (
                   <div className="flex flex-col items-center justify-center py-10 opacity-60">
                      <div className="size-16 bg-indigo-100 rounded-full flex items-center justify-center text-3xl mb-3 animate-bounce shadow-inner">👋</div>
                      <p className="text-slate-500 font-bold text-sm">Welcome to RailMadad</p>
                   </div>
                )}

                {messages.map((msg, index) => {
                  const isLastMessage = index === messages.length - 1;
                  
                  return (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      key={msg.id} 
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} gap-2.5 mb-5`}
                    >
                      {msg.role === 'bot' && (
                        <div className="size-8 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1 shadow-sm border border-indigo-200">
                          <Sparkles className="size-4 text-white" />
                        </div>
                      )}
                      
                      <div className={`max-w-[85%] flex flex-col gap-1.5 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                        <div className={`px-4 py-2.5 text-sm shadow-sm leading-relaxed ${
                          msg.role === 'user' 
                            ? 'bg-gradient-to-br from-indigo-600 to-blue-600 text-white rounded-2xl rounded-tr-sm border border-indigo-700' 
                            : 'bg-white text-slate-800 rounded-2xl rounded-tl-sm border border-slate-200'
                        }`}>
                          {msg.text}
                        </div>

                        {msg.role === 'bot' && msg.buttons && msg.buttons.length > 0 && isLastMessage && (
                          <div className="flex flex-wrap gap-2 mt-1">
                            {msg.buttons.map((btn, i) => (
                              <motion.button 
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                key={i}
                                onClick={() => sendMessageToApi(btn.text)}
                                className="bg-white border border-indigo-200 text-indigo-600 px-3 py-1.5 rounded-full text-xs font-semibold hover:bg-indigo-50 hover:border-indigo-300 transition-colors shadow-sm"
                              >
                                {btn.text}
                              </motion.button>
                            ))}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}

                {isLoading && (
                  <div className="flex justify-start gap-2.5 mb-5">
                    <div className="size-8 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1 shadow-sm border border-indigo-200">
                      <Sparkles className="size-4 text-white" />
                    </div>
                    <div className="px-5 py-3 text-[11px] bg-white text-slate-400 rounded-2xl rounded-tl-sm border border-slate-200 italic shadow-sm flex items-center gap-1.5">
                      <span className="flex gap-0.5">
                        <span className="size-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="size-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="size-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </span>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <form onSubmit={handleSubmit} className="p-3 bg-white border-t border-slate-100">
                <div className="flex gap-2 relative">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-1 pl-4 pr-12 py-3 rounded-full bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm transition-all shadow-inner"
                  />
                  <button
                    type="submit"
                    className="absolute right-1 top-1 bottom-1 aspect-square bg-gradient-to-br from-indigo-600 to-blue-600 rounded-full flex items-center justify-center text-white hover:shadow-lg transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={!message.trim() || isLoading}
                  >
                    <Send className="size-4" />
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="relative group"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className="px-6 py-3.5 bg-gradient-to-r from-indigo-600 via-indigo-700 to-blue-600 rounded-full shadow-xl hover:shadow-2xl transition-all flex items-center gap-3 border border-white/10">
          <motion.div
            animate={isOpen ? { rotate: 0 } : { rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="size-6 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm"
          >
            <Sparkles className="size-4 text-white" />
          </motion.div>
          <span className="text-white font-bold text-sm tracking-wide">Ask RailBot</span>
          {!isOpen && (
            <motion.div
              animate={{ scale: [1, 1.3, 1], opacity: [1, 0.5, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="absolute -top-1 -right-1 size-3.5 bg-green-400 rounded-full border-2 border-white shadow-sm"
            />
          )}
        </div>

        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-blue-500 rounded-full blur-xl opacity-40 group-hover:opacity-70 transition-opacity -z-10" />
      </motion.button>
    </div>
  );
}
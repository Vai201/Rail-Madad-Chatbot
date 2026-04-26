import { useState, useEffect, useRef } from "react";
import { X, Send, Sparkles, Globe } from "lucide-react";
import { motion, AnimatePresence } from "motion/react"; // or "framer-motion" depending on your setup

const BACKEND_URL = 'https://rail-madad-chatbot-1094417494880.asia-south1.run.app';

// Define the shape of our chat messages
type Message = {
  id: string;
  role: 'user' | 'bot';
  text: string;
  buttons?: { text: string }[];
};

export function ChatbotCapsule() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [language, setLanguage] = useState("en");

  // Generate a random session ID once per user visit
  const sessionIdRef = useRef("session-" + Math.random().toString(36).substring(7));
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasInitialized = useRef(false);

  // Auto-scroll to the newest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Auto-trigger the bot greeting on first load
  useEffect(() => {
    if (!hasInitialized.current) {
      hasInitialized.current = true;
      sendMessageToApi("Hi", true); // Send "Hi" silently
    }
  }, []);

  const sendMessageToApi = async (text: string, isHiddenInit = false) => {
    if (!text.trim()) return;

    // 1. Add User Message to UI (unless it's the hidden initialization)
    if (!isHiddenInit) {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', text }]);
    }
    
    // 2. Show "Thinking..." state
    setIsLoading(true);

    try {
      // 3. Call your Python Backend
      const response = await fetch(`${BACKEND_URL}/chat_proxy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            "message": text, 
            "language": language,
            "session_id": sessionIdRef.current
        })
      });

      const data = await response.json();
      
      // 4. Add AI Response and action buttons to UI
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
    setMessage(""); // Clear input box
    sendMessageToApi(text); // Send to AI
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
            <div className="bg-white rounded-2xl shadow-2xl border border-indigo-200/50 overflow-hidden flex flex-col h-[500px]">
              {/* Header */}
              <div className="bg-gradient-to-r from-indigo-600 to-blue-600 px-4 py-3 flex items-center justify-between shadow-md z-10">
                <div className="flex items-center gap-2">
                  <div className="size-2 bg-green-300 rounded-full animate-pulse" />
                  <div>
                    <span className="text-white font-bold text-sm block leading-tight">RailMadad Support</span>
                    <span className="text-[10px] text-indigo-200 uppercase tracking-widest font-bold">Live AI Agent</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  {/* Language Selector */}
                  <div className="flex items-center bg-white/20 rounded-lg px-2 py-1">
                    <Globe className="size-3 text-white mr-1" />
                    <select 
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      className="bg-transparent text-white text-[10px] font-bold outline-none cursor-pointer [&>option]:text-slate-800"
                    >
                      <option value="en">EN</option>
                      <option value="hi">HI</option>
                      <option value="mr">MR</option>
                    </select>
                  </div>

                  <button
                    onClick={() => setIsOpen(false)}
                    className="text-white/80 hover:text-white transition-colors"
                    aria-label="Close chat"
                  >
                    <X className="size-5" />
                  </button>
                </div>
              </div>

              {/* Chat Area */}
              <div className="flex-1 p-4 overflow-y-auto bg-slate-50 scroll-smooth">
                {messages.length === 0 && !isLoading && (
                   <div className="flex flex-col items-center justify-center py-10 opacity-60">
                      <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center text-3xl mb-3 animate-bounce">👋</div>
                      <p className="text-slate-500 font-bold text-sm">Welcome to Rail Madad</p>
                   </div>
                )}

                {/* Render Messages */}
                {messages.map((msg, index) => {
                  const isLastMessage = index === messages.length - 1;
  
                  return (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} gap-2 mb-4`}>
                      {msg.role === 'bot' && (
                        <div className="size-8 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
                          <Sparkles className="size-4 text-white" />
                        </div>
                      )}
                      
                      <div className={`max-w-[85%] flex flex-col gap-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                        <div className={`px-4 py-2.5 text-sm shadow-sm leading-relaxed ${
                          msg.role === 'user' 
                            ? 'bg-indigo-600 text-white rounded-2xl rounded-br-none border border-indigo-700' 
                            : 'bg-white text-slate-800 rounded-2xl rounded-tl-none border border-indigo-100'
                        }`}>
                          {msg.text}
                        </div>

                        {/* Render Dialogflow Action Buttons (ONLY if it is the last message) */}
                        {msg.role === 'bot' && msg.buttons && msg.buttons.length > 0 && isLastMessage && (
                          <div className="flex flex-wrap gap-2 mt-1">
                            {msg.buttons.map((btn, i) => (
                              <button 
                                key={i}
                                onClick={() => sendMessageToApi(btn.text)}
                                className="bg-white border border-indigo-200 text-indigo-600 px-3 py-1.5 rounded-full text-[10px] font-bold hover:bg-indigo-600 hover:text-white transition-all shadow-sm active:scale-95"
                              >
                                {btn.text}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* Typing Indicator */}
                {isLoading && (
                  <div className="flex justify-start gap-2 mb-4">
                    <div className="size-8 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
                      <Sparkles className="size-4 text-white" />
                    </div>
                    <div className="px-4 py-2.5 text-[11px] bg-white text-slate-400 rounded-2xl rounded-tl-none border border-indigo-100 italic animate-pulse">
                      RailBot is thinking...
                    </div>
                  </div>
                )}
                
                {/* Invisible div to scroll to */}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <form onSubmit={handleSubmit} className="border-t border-slate-100 p-3 bg-white">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-1 px-4 py-2.5 rounded-xl bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm transition-all"
                  />
                  <button
                    type="submit"
                    className="h-10 px-4 bg-gradient-to-r from-indigo-600 to-blue-600 rounded-xl flex items-center justify-center text-white font-bold hover:shadow-lg transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
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

      {/* Capsule Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="relative group"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className="px-6 py-3 bg-gradient-to-r from-indigo-600 via-indigo-700 to-blue-600 rounded-full shadow-lg hover:shadow-xl transition-shadow flex items-center gap-3 border border-white/10">
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
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="absolute -top-1 -right-1 size-3 bg-green-400 rounded-full border-2 border-white"
            />
          )}
        </div>

        {/* Glow Effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-blue-500 rounded-full blur-lg opacity-40 group-hover:opacity-75 transition-opacity -z-10" />
      </motion.button>
    </div>
  );
}
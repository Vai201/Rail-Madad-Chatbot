import { useState, useEffect, useRef } from "react";
import { X, Send, Sparkles, Globe, ChevronDown, Paperclip, Loader2, Navigation, AlertTriangle, MessageSquare } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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
  // UI States
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // App Modes
  const [chatMode, setChatMode] = useState<'normal' | 'tracking' | 'sos_auth' | 'sos_active'>('normal');
  const [sosId, setSosId] = useState("");

  // Language States
  const [language, setLanguage] = useState("en");
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);

  // Media Upload States
  const [allowMediaUpload, setAllowMediaUpload] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [attachmentUrl, setAttachmentUrl] = useState<string | null>(null);
  const [attachmentName, setAttachmentName] = useState<string | null>(null);
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const sessionIdRef = useRef("session-" + Math.random().toString(36).substring(7));
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const currentLangLabel = SUPPORTED_LANGUAGES.find(l => l.code === language)?.label || 'English';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    const handleRemoteTracking = () => {
      setIsOpen(true);
      setChatMode('tracking');
      setMessages([{id: Date.now().toString(), role: 'bot', text: "Please enter your 10-digit mobile number to track your open complaints."}]);
    };
    
    window.addEventListener('open-railbot-tracking', handleRemoteTracking);
    return () => window.removeEventListener('open-railbot-tracking', handleRemoteTracking);
  }, []);

  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
    setMessages([]); 
    setChatMode('normal');
    sessionIdRef.current = "session-" + Math.random().toString(36).substring(7);
  };

  const sendMessageToApi = async (text: string, isHiddenInit = false, overrideLang?: string, mediaUrl?: string | null) => {
    if (!text.trim() && !mediaUrl) return;

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
            "session_id": sessionIdRef.current,
            "media_url": mediaUrl || null 
        })
      });

      const data = await response.json();
      
      setAllowMediaUpload(data.allow_upload || false);
      
      const repliesArray = (data.reply || "").split('<br><br>');
      const newMessages = repliesArray.map((replyText: string, index: number) => ({
        id: Date.now().toString() + "-" + index,
        role: 'bot' as const,
        text: replyText,
        buttons: index === repliesArray.length - 1 ? data.buttons : undefined
      }));

      setMessages(prev => [...prev, ...newMessages]);
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

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/generate-upload-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileName: file.name, contentType: file.type })
      });
      
      const { signedUrl, publicUrl } = await res.json();

      await fetch(signedUrl, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file
      });

      setAttachmentUrl(publicUrl);
      setAttachmentName(file.name);
    } catch (error) {
      console.error("Upload failed", error);
      alert("Failed to upload file. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  // SMART DETECTOR: Checks if the bot is asking for a mobile number
  const isAskingForPhone = messages.length > 0 && messages[messages.length - 1].role === 'bot' && messages[messages.length - 1].text.toLowerCase().includes('mobile number');
  const isTrackingOrPhone = chatMode === 'tracking' || isAskingForPhone;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() && !attachmentUrl) return;

    const userText = message;
    const displayMessage = message || "Sent an attachment 📎";
    
    // Clear Input
    setMessage(""); 
    setAttachmentUrl(null);
    setAttachmentName(null);
    setAllowMediaUpload(false); 
    
    // Show User Message
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', text: displayMessage }]);
    setIsLoading(true);

    try {
      // MODE 1: TRACKING
      if (chatMode === 'tracking') {
        const cleanNumber = userText.replace(/\D/g, '');
        if (userText.toLowerCase() === 'cancel') {
            setChatMode('normal');
            setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: "Tracking cancelled. How can I help you today?" }]);
            setIsLoading(false);
            return;
        }
        if (cleanNumber.length !== 10) {
            setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: "⚠️ That doesn't look like a valid 10-digit number. Please try again, or type 'cancel' to exit." }]);
            setIsLoading(false);
            return;
        }

        const res = await fetch(`${BACKEND_URL}/api/track`, {
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone_number: cleanNumber })
        });
        const data = await res.json();
        
        let replyText = "";
        if (data.complaints && data.complaints.length > 0) {
            replyText = data.complaints.map((c: any) => `<b>ID:</b> ${c.id}<br><b>Status:</b> ${c.status}<br><b>Dept:</b> ${c.department}<br><b>Resolution:</b> ${c.resolution || 'Pending'}`).join('<br><br>---<br><br>');
        } else {
            replyText = "No complaints found for this number.";
        }
        
        setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: replyText }]);
        setChatMode('normal'); 
        setIsLoading(false);
      } 
      
      // MODE 2: SOS AUTHENTICATION
      else if (chatMode === 'sos_auth') {
        if (userText.toLowerCase() === 'cancel') {
            setChatMode('normal');
            setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: "SOS mode deactivated. How can I help you today?" }]);
            setIsLoading(false);
            return;
        }
        setSosId(userText); 
        setChatMode('sos_active');
        setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: "Complaint ID logged. What is your immediate emergency? (Tactical help will be provided)" }]);
        setIsLoading(false);
      } 
      
      // MODE 3: SOS ACTIVE
      else if (chatMode === 'sos_active') {
        const res = await fetch(`${BACKEND_URL}/api/sos`, {
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ complaint_id: sosId, message: userText })
        });
        const data = await res.json();
        setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: "🚨 " + data.reply }]);
        setIsLoading(false);
      } 
      
      // MODE 4: NORMAL CHAT
      else {
        // ENFORCE 10 DIGITS FOR DIALOGFLOW TOO!
        if (isAskingForPhone && userText.toLowerCase() !== 'cancel') {
            const cleanNumber = userText.replace(/\D/g, '');
            if (cleanNumber.length !== 10) {
                setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: "⚠️ Please enter exactly 10 digits. (Or type 'cancel' to exit)." }]);
                setIsLoading(false);
                return;
            }
        }

        let finalMessageText = userText;
        if (attachmentUrl) {
          finalMessageText += `\n[Evidence: ${attachmentUrl}]`;
        }
        await sendMessageToApi(finalMessageText, true, undefined, attachmentUrl); 
      }
    } catch (err) {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'bot', text: "Connection error. Please try again." }]);
      setIsLoading(false);
    } 
  };

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="absolute bottom-full mb-4 left-1/2 -translate-x-1/2 w-[400px] max-w-[calc(100vw-2rem)]"
          >
            <div className="bg-white rounded-3xl shadow-2xl border border-indigo-100 overflow-hidden flex flex-col h-[560px]">
              
              {/* Header */}
              <div className={`px-4 py-3.5 flex items-center justify-between shadow-md z-10 transition-colors ${chatMode === 'sos_active' ? 'bg-gradient-to-r from-rose-600 to-red-600' : 'bg-gradient-to-r from-indigo-600 to-blue-600'}`}>
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="size-8 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/30">
                      <Sparkles className="size-4 text-white" />
                    </div>
                    <div className="absolute bottom-0 right-0 size-2.5 bg-green-400 rounded-full border-2 border-white animate-pulse" />
                  </div>
                  <div>
                    <span className="text-white font-bold text-sm block leading-tight">RailBot Assistant</span>
                    <span className="text-[10px] text-white/80 uppercase tracking-widest font-semibold">
                      {chatMode === 'sos_active' ? "🚨 SOS MODE ACTIVE" : "Live AI Agent"}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <button 
                      onClick={() => setIsLangMenuOpen(!isLangMenuOpen)}
                      className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 border border-white/20 transition-all rounded-full px-3 py-1.5 backdrop-blur-md text-white text-xs font-bold shadow-sm"
                    >
                      <Globe className="size-3.5 text-white/90" />
                      <span>{currentLangLabel}</span>
                      <ChevronDown className={`size-3.5 transition-transform duration-300 ${isLangMenuOpen ? 'rotate-180' : ''}`} />
                    </button>

                    <AnimatePresence>
                      {isLangMenuOpen && (
                        <>
                          <div className="fixed inset-0 z-40" onClick={() => setIsLangMenuOpen(false)} />
                          <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            className="absolute top-full right-0 mt-2 w-36 bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden z-50 origin-top-right"
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
              <div className={`flex-1 p-4 overflow-y-auto scroll-smooth ${chatMode === 'sos_active' ? 'bg-rose-50/30' : 'bg-slate-50/50'}`}>
                
                {messages.length === 0 && !isLoading && (
                   <div className="flex flex-col items-center justify-center py-6 animate-in fade-in zoom-in duration-500">
                      <div className="size-16 bg-indigo-100 rounded-full flex items-center justify-center text-3xl mb-3 shadow-inner">👋</div>
                      <p className="text-slate-500 font-bold text-sm mb-6">How can we help you today?</p>
                      
                      <div className="w-full flex flex-col gap-3 px-2">
                        <button 
                          onClick={() => { setChatMode('normal'); sendMessageToApi("Hi", true); }} 
                          className="flex items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-slate-200 hover:border-indigo-400 hover:shadow-md transition-all text-left group"
                        >
                          <div className="bg-indigo-50 p-2.5 rounded-full text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                            <MessageSquare className="size-5" />
                          </div>
                          <div>
                            <div className="font-bold text-slate-800 text-sm">New Query / Complaint</div>
                            <div className="text-xs text-slate-500">Ask a question or file an issue</div>
                          </div>
                        </button>
                        
                        <button 
                          onClick={() => { 
                            setChatMode('tracking'); 
                            setMessages([{id: '1', role: 'bot', text: "Please enter your 10-digit mobile number to track your open complaints."}]); 
                          }} 
                          className="flex items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-slate-200 hover:border-blue-400 hover:shadow-md transition-all text-left group"
                        >
                          <div className="bg-blue-50 p-2.5 rounded-full text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                            <Navigation className="size-5" />
                          </div>
                          <div>
                            <div className="font-bold text-slate-800 text-sm">Track Complaint</div>
                            <div className="text-xs text-slate-500">Check live resolution status</div>
                          </div>
                        </button>

                        <button 
                          onClick={() => { 
                            setChatMode('sos_auth'); 
                            setMessages([{id: '1', role: 'bot', text: "🚨 <b>SOS MODE:</b> Please enter your Complaint ID (e.g., C-45) to verify."}]); 
                          }} 
                          className="flex items-center gap-4 bg-rose-50 p-4 rounded-2xl shadow-sm border border-rose-200 hover:border-rose-400 hover:shadow-md transition-all text-left group"
                        >
                          <div className="bg-rose-100 p-2.5 rounded-full text-rose-600 group-hover:bg-rose-600 group-hover:text-white transition-colors">
                            <AlertTriangle className="size-5" />
                          </div>
                          <div>
                            <div className="font-bold text-rose-800 text-sm">SOS Emergency</div>
                            <div className="text-xs text-rose-600">48-Hour Live Tactical Assistance</div>
                          </div>
                        </button>
                      </div>
                   </div>
                )}

                {messages.map((msg, index) => {
                  const isLastMessage = index === messages.length - 1;
                  const isEmergency = msg.text.includes('🚨');
                  
                  return (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      key={msg.id} 
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} gap-2.5 mb-5`}
                    >
                      {msg.role === 'bot' && (
                        <div className={`size-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 shadow-sm border ${isEmergency || chatMode === 'sos_active' ? 'bg-gradient-to-br from-rose-500 to-red-500 border-rose-200' : 'bg-gradient-to-br from-indigo-500 to-blue-500 border-indigo-200'}`}>
                          <Sparkles className="size-4 text-white" />
                        </div>
                      )}
                      
                      <div className={`max-w-[85%] flex flex-col gap-1.5 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                        <div 
                          className={`px-4 py-2.5 text-sm shadow-sm leading-relaxed rounded-2xl ${
                            msg.role === 'user' 
                              ? 'bg-gradient-to-br from-indigo-600 to-blue-600 text-white rounded-tr-sm border border-indigo-700' 
                              : isEmergency || chatMode === 'sos_active'
                                ? 'bg-rose-50 text-rose-900 rounded-tl-sm border border-rose-200 shadow-rose-100 font-medium'
                                : 'bg-white text-slate-800 rounded-tl-sm border border-slate-200'
                          }`}
                          dangerouslySetInnerHTML={{ __html: msg.text }}
                        />

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
                    <div className="size-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 shadow-sm bg-gradient-to-br from-indigo-500 to-blue-500 border-indigo-200">
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
              <form 
                onSubmit={handleSubmit} 
                className={`p-3 border-t flex flex-col gap-2 transition-colors ${chatMode === 'sos_active' || chatMode === 'sos_auth' ? 'bg-rose-50 border-rose-100' : 'bg-white border-slate-100'}`}
              >
                
                {attachmentName && (
                  <div className="flex items-center gap-2 bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-lg text-xs font-medium w-fit border border-indigo-100">
                    <Paperclip className="size-3.5" />
                    <span className="truncate max-w-[200px]">{attachmentName}</span>
                    <button type="button" onClick={() => { setAttachmentUrl(null); setAttachmentName(null); }} className="hover:text-indigo-900 ml-1">
                      <X className="size-3" />
                    </button>
                  </div>
                )}

                <div className="flex gap-2 relative items-center">
                  <input 
                    type="file" 
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept="image/*,video/*"
                    className="hidden" 
                  />
                  
                  {allowMediaUpload && chatMode === 'normal' && (
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isUploading}
                      className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-full transition-colors disabled:opacity-50"
                      title="Attach Photo or Video"
                    >
                      {isUploading ? <Loader2 className="size-4 animate-spin" /> : <Paperclip className="size-4" />}
                    </button>
                  )}

                  <input
                    type={isTrackingOrPhone ? "tel" : "text"}
                    value={message}
                    onChange={(e) => {
                      if (isTrackingOrPhone) {
                        const onlyNums = e.target.value.replace(/\D/g, '');
                        if (onlyNums.length <= 10) setMessage(onlyNums);
                      } else {
                        setMessage(e.target.value);
                      }
                    }}
                    placeholder={chatMode === 'sos_active' ? "Describe your emergency..." : isTrackingOrPhone ? "Enter 10-digit number..." : allowMediaUpload ? "Describe issue & attach photo..." : "Type your message..."}
                    className={`flex-1 pl-4 pr-12 py-3 rounded-full border focus:outline-none focus:ring-2 text-sm transition-all shadow-inner ${
                      chatMode === 'sos_active' || chatMode === 'sos_auth' 
                        ? 'bg-white border-rose-200 focus:ring-rose-500/20 focus:border-rose-500' 
                        : 'bg-slate-50 border-slate-200 focus:ring-indigo-500/20 focus:border-indigo-500'
                    }`}
                  />
                  
                  {/* The Send button is now entirely disabled unless exactly 10 digits are typed! */}
                  <button
                    type="submit"
                    className={`absolute right-1 top-1 bottom-1 aspect-square rounded-full flex items-center justify-center text-white hover:shadow-lg transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed ${
                      chatMode === 'sos_active' || chatMode === 'sos_auth'
                        ? 'bg-gradient-to-br from-rose-600 to-red-600'
                        : 'bg-gradient-to-br from-indigo-600 to-blue-600'
                    }`}
                    disabled={
                      (!message.trim() && !attachmentUrl) || 
                      isLoading || 
                      isUploading || 
                      (isTrackingOrPhone && message.toLowerCase() !== 'cancel' && message.replace(/\D/g, '').length !== 10)
                    }
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
import { Link, useLocation } from "react-router";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export function Navigation() {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  const navLinks = [
    { path: "/", label: "Heritage" },
    { path: "/trains", label: "Trains" },
    { path: "/intent", label: "Our Intent" },
    { path: "/technology", label: "Technology" },
  ];

  const isActive = (path: string) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-lg border-b border-slate-200/50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <img
              src="/images/swarail-logo.png"
              alt="Swarail Logo"
              className="size-12 object-contain group-hover:scale-105 transition-transform"
            />
            <div className="hidden sm:block">
              <div className="text-xs text-slate-600 font-medium">Digital India Initiative</div>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-2">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className="relative px-4 py-2 text-sm font-medium transition-colors"
              >
                <span
                  className={
                    isActive(link.path)
                      ? "text-indigo-600"
                      : "text-slate-700 hover:text-indigo-600"
                  }
                >
                  {link.label}
                </span>
                {isActive(link.path) && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-indigo-500 to-blue-500"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </Link>
            ))}
            
            {/* 🔍 Track Complaint Navbar Capsule */}
            <div className="ml-2 pl-3 border-l border-slate-200">
              <button 
                onClick={() => window.dispatchEvent(new CustomEvent('open-railbot-tracking'))} 
                className="flex items-center gap-2 px-4 py-1.5 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-full text-slate-700 text-sm font-bold shadow-sm transition-all hover:shadow cursor-pointer active:scale-95"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-blue-600"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg>
                Track Complaint
              </button>
            </div>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-slate-50 transition-colors"
            aria-label="Toggle menu"
          >
            {isOpen ? <X className="size-6" /> : <Menu className="size-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden overflow-hidden border-t border-slate-200/50"
            >
              <div className="py-4 space-y-2">
                {navLinks.map((link) => (
                  <Link
                    key={link.path}
                    to={link.path}
                    onClick={() => setIsOpen(false)}
                    className={`block px-4 py-2 rounded-lg transition-colors ${
                      isActive(link.path)
                        ? "bg-indigo-100 text-indigo-600 font-medium"
                        : "text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    {link.label}
                  </Link>
                ))}
                
                {/* 🔍 Mobile Track Complaint Button */}
                <div className="px-4 pt-2 mt-2 border-t border-slate-100">
                  <button 
                    onClick={() => {
                      setIsOpen(false);
                      window.dispatchEvent(new CustomEvent('open-railbot-tracking'));
                    }} 
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-xl text-slate-700 text-sm font-bold shadow-sm transition-all active:scale-95"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-blue-600"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg>
                    Track Complaint
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </nav>
  );
}
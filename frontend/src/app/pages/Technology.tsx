import { motion, AnimatePresence } from "framer-motion";
import { Code, Cpu, Database, Cloud, Sparkles, Zap } from "lucide-react";
import { useState, useEffect } from "react";

interface TechLogo {
  name: string;
  imageUrl: string;
  description: string;
  role: string;
  color: string;
  angle: number;
}

const techStack: TechLogo[] = [
  {
    name: "Google Cloud",
    imageUrl: "https://www.vectorlogo.zone/logos/google_cloud/google_cloud-icon.svg",
    description: "Cloud infrastructure powering our scalable backend services",
    role: "Cloud Infrastructure",
    color: "from-blue-500 to-blue-600",
    angle: 0,
  },
  {
    name: "Dialogflow",
    imageUrl: "https://assets.streamlinehq.com/image/private/w_300,h_300,ar_1/f_auto/v1/icons/3/dialogflow-hwo0764xobs2i5fcrkc4ro.png/dialogflow-mwyw8o2b21wa3l53ro3p.png?_a=DATAiZAAZAA0",
    description: "Natural language processing for intelligent conversations",
    role: "NLP Engine",
    color: "from-orange-500 to-orange-600",
    angle: 45,
  },
  {
    name: "Gemini AI",
    imageUrl: "https://logo-teka.com/wp-content/uploads/2026/02/gemini-icon-logo.svg",
    description: "Advanced AI model for understanding and responding to queries",
    role: "AI Model",
    color: "from-purple-500 to-purple-600",
    angle: 90,
  },
  {
    name: "Indian Railways",
    imageUrl: "https://crystalpng.com/wp-content/uploads/2025/09/indian-railways-logo.png",
    description: "Official partner providing reliable railway data and services",
    role: "Data Source",
    color: "from-red-500 to-red-600",
    angle: 135,
  },
  {
    name: "CRIS",
    imageUrl: "https://govtjobfix.com/wp-content/uploads/2019/07/Centre-for-Railway-Information-Systems-CRIS.png",
    description: "Centre for Railway Information Systems - core data provider and IT department of Indian Railway",
    role: "Information Systems",
    color: "from-green-500 to-green-600",
    angle: 180,
  },
  {
    name: "Google Firebase",
    imageUrl: "https://img.icons8.com/?size=100&id=62452&format=png&color=000000",
    description: "Scalable global hosting with automated SSL and seamless CLI deployment",
    role: "Deploying and Hosting",
    color: "from-yellow-500 to-orange-600",
    angle: 225,
  },
  {
    name: "GitHub",
    imageUrl: "https://www.vectorlogo.zone/logos/github/github-icon.svg",
    description: "Open-source collaboration and version control",
    role: "Version Control",
    color: "from-gray-700 to-gray-800",
    angle: 270,
  },
  {
    name: "Python",
    imageUrl: "https://www.vectorlogo.zone/logos/python/python-icon.svg",
    description: "Backend logic and AI model integration",
    role: "Backend Language",
    color: "from-yellow-500 to-yellow-600",
    angle: 315,
  },
];

const features = [
  {
    icon: Code,
    title: "Modern Stack",
    description: "Built with React, TypeScript, and Tailwind CSS",
  },
  {
    icon: Cpu,
    title: "AI-Powered",
    description: "Leveraging Google's Gemini for intelligent responses",
  },
  {
    icon: Database,
    title: "Real-Time Data",
    description: "Live integration with railway information systems",
  },
  {
    icon: Cloud,
    title: "Scalable",
    description: "Cloud infrastructure ready for millions of users",
  },
];

export function Technology() {
  const [hoveredTech, setHoveredTech] = useState<string | null>(null);
  const [pinnedTech, setPinnedTech] = useState<string | null>(null);
  const [radius, setRadius] = useState(280);

  // Handle responsive radius for the orbit
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 640) setRadius(120); // Mobile
      else if (window.innerWidth < 1024) setRadius(200); // Tablet
      else setRadius(280); // Desktop
    };
    
    handleResize(); // Initial check
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Global click listener to close pinned tooltip when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (!(e.target as HTMLElement).closest('.tech-node')) {
        setPinnedTech(null);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const handleNodeClick = (techName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setPinnedTech(pinnedTech === techName ? null : techName);
  };

  return (
    <div className="pt-16 min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 text-white py-20">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjEiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-20" />
        </div>

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full mb-6">
              <Sparkles className="size-4" />
              <span className="text-sm font-medium">Powered by Cutting-Edge Technology</span>
            </div>
            <h1 className="text-5xl lg:text-6xl font-bold mb-6">
              Technology{" "}
              <span className="bg-gradient-to-r from-orange-400 to-green-400 bg-clip-text text-transparent">
                Ecosystem
              </span>
            </h1>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              A symphony of modern technologies working together to revolutionize rail travel information
            </p>
          </motion.div>
        </div>
      </section>

      {/* Orbiting Logos Section */}
      <section className="py-20 bg-gradient-to-b from-slate-900 to-slate-800 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold text-white mb-4">Our Technology Stack</h2>
            <p className="text-slate-300 max-w-2xl mx-auto">
              Hover over or tap each technology to explore its role in our ecosystem
            </p>
          </motion.div>

          {/* Orbital System */}
          <div className="relative w-full max-w-4xl mx-auto aspect-[1/1] md:aspect-video flex items-center justify-center my-16 md:my-32">
            
            {/* Center Logo - Indian Railways */}
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ duration: 1, type: "spring" }}
              className="absolute z-20"
            >
              <div className="relative group">
                <div className="size-24 md:size-32 bg-gradient-to-br from-orange-500 via-white to-green-500 rounded-full flex items-center justify-center shadow-2xl ring-4 ring-white/20">
                  <div className="size-20 md:size-28 bg-white rounded-full flex items-center justify-center p-3 md:p-4 overflow-hidden">
                    <img 
                      src="/images/swarail-logo.png" 
                      alt="Indian Railways" 
                      className="w-full h-full object-contain"
                    />
                  </div>
                </div>
                {/* Glow effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-orange-500 to-green-500 rounded-full blur-2xl opacity-50 animate-pulse" />
                {/* Center label */}
                <div className="absolute -bottom-14 md:-bottom-16 left-1/2 -translate-x-1/2 whitespace-nowrap">
                  <div className="bg-white/10 backdrop-blur-sm px-3 md:px-4 py-1.5 md:py-2 rounded-full border border-white/20 text-center">
                    <p className="text-white font-bold text-xs md:text-sm">Indian Railways</p>
                    <p className="text-white/60 text-[10px] md:text-xs">Core System</p>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Orbiting Technologies */}
            {techStack.map((tech, index) => {
              const angleInRadians = (tech.angle * Math.PI) / 180;
              const x = Math.cos(angleInRadians) * radius;
              const y = Math.sin(angleInRadians) * radius;
              
              const isHovered = hoveredTech === tech.name;
              const isPinned = pinnedTech === tech.name;
              const isActive = isHovered || isPinned;

              return (
                <motion.div
                  key={tech.name}
                  className={`absolute tech-node ${isActive ? 'z-50' : 'z-10'}`}
                  style={{
                    left: "50%",
                    top: "50%",
                  }}
                  initial={{ x: 0, y: 0, opacity: 0 }}
                  animate={{
                    x: x,
                    y: y,
                    opacity: 1,
                  }}
                  transition={{
                    x: { delay: index * 0.1, duration: 0.8 },
                    y: { delay: index * 0.1, duration: 0.8 },
                    opacity: { delay: index * 0.1, duration: 0.5 },
                  }}
                >
                  <motion.div
                    whileHover={{ scale: 1.15 }}
                    onHoverStart={() => setHoveredTech(tech.name)}
                    onHoverEnd={() => setHoveredTech(null)}
                    onClick={(e) => handleNodeClick(tech.name, e)}
                    className="relative group cursor-pointer -translate-x-1/2 -translate-y-1/2"
                  >
                    {/* The Icon Bubble */}
                    <div className={`size-14 md:size-16 bg-white rounded-full flex items-center justify-center shadow-xl ring-2 ${isActive ? 'ring-indigo-400' : 'ring-white/30'} hover:ring-indigo-300 transition-all p-3 overflow-hidden`}>
                      <img src={tech.imageUrl} alt={tech.name} className="w-full h-full object-contain drop-shadow-sm" />
                    </div>
                    
                    {/* Glow on hover or active */}
                    <div className={`absolute inset-0 bg-white rounded-full blur-xl transition-opacity duration-300 -z-10 ${isActive ? 'opacity-60' : 'opacity-0'}`} />

                    {/* Connection line to center */}
                    <motion.div
                      className="absolute top-1/2 left-1/2 origin-left -z-20"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: isActive ? 0.4 : 0 }}
                      style={{
                        background: `linear-gradient(to right, transparent, rgba(255,255,255,0.8))`,
                        width: `${radius}px`,
                        height: "2px",
                        transform: `translateY(-50%) rotate(${tech.angle + 180}deg)`,
                      }}
                    />

                    {/* Tooltip Information Box */}
                    <AnimatePresence>
                      {isActive && (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.9, y: 10 }}
                          animate={{ opacity: 1, scale: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.9, y: 10 }}
                          transition={{ type: "spring", stiffness: 400, damping: 25 }}
                          className={`
                            fixed bottom-6 left-4 right-4 
                            md:absolute md:top-1/2 md:-translate-y-1/2 md:bottom-auto md:left-auto md:right-auto md:w-72 
                            bg-slate-900/95 backdrop-blur-xl border border-white/20 p-5 rounded-2xl shadow-2xl z-[100]
                            ${x > 0 ? 'md:right-full md:mr-6' : 'md:left-full md:ml-6'}
                          `}
                          onClick={(e) => e.stopPropagation()} // Prevent clicks inside tooltip from closing it
                        >
                          <div className="flex items-start gap-4">
                            <div className="size-12 bg-white rounded-xl flex items-center justify-center flex-shrink-0 p-2.5 border border-slate-700">
                              <img src={tech.imageUrl} alt={tech.name} className="w-full h-full object-contain" />
                            </div>
                            <div className="flex-1 text-left">
                              <h3 className="text-lg font-bold text-white mb-0.5">{tech.name}</h3>
                              <p className="text-indigo-400 text-[11px] font-bold mb-2 uppercase tracking-widest">{tech.role}</p>
                              <p className="text-slate-300 text-sm leading-relaxed">{tech.description}</p>
                            </div>
                          </div>
                          
                          {/* Close button shown only when pinned (especially useful for mobile) */}
                          {isPinned && (
                            <div className="mt-4 pt-3 border-t border-white/10 flex justify-end">
                              <button 
                                onClick={(e) => { e.stopPropagation(); setPinnedTech(null); }}
                                className="text-xs font-semibold text-slate-400 hover:text-white transition-colors bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-lg"
                              >
                                Close
                              </button>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>

                  </motion.div>
                </motion.div>
              );
            })}

            {/* Orbital Rings - Dynamically sized based on radius */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
              <div 
                style={{ width: radius * 2, height: radius * 2 }} 
                className="border border-white/10 rounded-full transition-all duration-500" 
              />
              <div 
                style={{ width: (radius * 2) + 60, height: (radius * 2) + 60 }} 
                className="absolute border border-white/5 rounded-full transition-all duration-500" 
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 bg-gradient-to-b from-slate-800 to-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold text-white mb-4">Technical Highlights</h2>
            <p className="text-slate-300 max-w-2xl mx-auto">
              Built with modern best practices and production-ready architecture
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all group"
              >
                <div className="size-12 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="size-6 text-white" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{feature.title}</h3>
                <p className="text-slate-400 text-sm">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Open Source CTA */}
      <section className="py-16 bg-gradient-to-r from-indigo-600 to-blue-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-white">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <Code className="size-12 mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-4">Open Source & Transparent</h2>
            <p className="text-white/90 mb-6 max-w-2xl mx-auto">
              This entire project is open-source. Explore our codebase, contribute, or learn from our implementation.
            </p>
            <a 
              href="https://github.com/Vai201/Rail-Madad-Chatbot" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-block px-8 py-3 bg-white text-indigo-600 font-medium rounded-full hover:shadow-xl transition-shadow"
            >
              View on GitHub
            </a>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
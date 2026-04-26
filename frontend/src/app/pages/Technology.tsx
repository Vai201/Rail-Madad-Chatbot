import { motion } from "motion/react";
import { Code, Cpu, Database, Cloud, Sparkles, Zap } from "lucide-react";
import { useState } from "react";

interface TechLogo {
  name: string;
  icon: string;
  description: string;
  role: string;
  color: string;
  angle: number;
}

const techStack: TechLogo[] = [
  {
    name: "Google Cloud Platform",
    icon: "☁️",
    description: "Cloud infrastructure powering our scalable backend services",
    role: "Cloud Infrastructure",
    color: "from-blue-500 to-blue-600",
    angle: 0,
  },
  {
    name: "Dialogflow",
    icon: "💬",
    description: "Natural language processing for intelligent conversations",
    role: "NLP Engine",
    color: "from-orange-500 to-orange-600",
    angle: 45,
  },
  {
    name: "Gemini AI",
    icon: "✨",
    description: "Advanced AI model for understanding and responding to queries",
    role: "AI Model",
    color: "from-purple-500 to-purple-600",
    angle: 90,
  },
  {
    name: "Indian Railways",
    icon: "🚂",
    description: "Official partner providing reliable railway data and services",
    role: "Data Source",
    color: "from-red-500 to-red-600",
    angle: 135,
  },
  {
    name: "CRIS",
    icon: "🖥️",
    description: "Centre for Railway Information Systems - core data provider",
    role: "Information Systems",
    color: "from-green-500 to-green-600",
    angle: 180,
  },
  {
    name: "IRCTC",
    icon: "🎫",
    description: "Indian Railway Catering and Tourism Corporation integration",
    role: "Booking Integration",
    color: "from-indigo-500 to-indigo-600",
    angle: 225,
  },
  {
    name: "GitHub",
    icon: "🐙",
    description: "Open-source collaboration and version control",
    role: "Version Control",
    color: "from-gray-700 to-gray-800",
    angle: 270,
  },
  {
    name: "Python",
    icon: "🐍",
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
  const [selectedTech, setSelectedTech] = useState<TechLogo | null>(null);

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
              Hover over each technology to learn more about its role in our ecosystem
            </p>
          </motion.div>

          {/* Orbital System */}
          <div className="relative w-full max-w-4xl mx-auto aspect-square flex items-center justify-center">
            {/* Center Logo - Rare Indian Railways Logo */}
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ duration: 1, type: "spring" }}
              className="absolute z-10"
            >
              <div className="relative group">
                <div className="size-32 bg-gradient-to-br from-orange-500 via-white to-green-500 rounded-full flex items-center justify-center shadow-2xl ring-4 ring-white/20">
                  <div className="size-28 bg-white rounded-full flex items-center justify-center">
                    <span className="text-6xl">🚂</span>
                  </div>
                </div>
                {/* Glow effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-orange-500 to-green-500 rounded-full blur-2xl opacity-50 animate-pulse" />
                {/* Center label */}
                <div className="absolute -bottom-16 left-1/2 -translate-x-1/2 whitespace-nowrap">
                  <div className="bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full border border-white/20">
                    <p className="text-white font-bold text-sm">Indian Railways</p>
                    <p className="text-white/60 text-xs">Core System</p>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Orbiting Technologies */}
            {techStack.map((tech, index) => {
              const radius = 280;
              const angleInRadians = (tech.angle * Math.PI) / 180;
              const x = Math.cos(angleInRadians) * radius;
              const y = Math.sin(angleInRadians) * radius;

              return (
                <motion.div
                  key={tech.name}
                  className="absolute"
                  style={{
                    left: "50%",
                    top: "50%",
                  }}
                  initial={{ x: 0, y: 0, opacity: 0 }}
                  animate={{
                    x: x,
                    y: y,
                    opacity: 1,
                    rotate: 360,
                  }}
                  transition={{
                    x: { delay: index * 0.1, duration: 0.8 },
                    y: { delay: index * 0.1, duration: 0.8 },
                    opacity: { delay: index * 0.1, duration: 0.5 },
                    rotate: {
                      duration: 40,
                      repeat: Infinity,
                      ease: "linear",
                    },
                  }}
                >
                  <motion.div
                    whileHover={{ scale: 1.3 }}
                    onHoverStart={() => setSelectedTech(tech)}
                    onHoverEnd={() => setSelectedTech(null)}
                    className="relative group cursor-pointer"
                  >
                    <div className={`size-20 bg-gradient-to-br ${tech.color} rounded-full flex items-center justify-center shadow-xl ring-2 ring-white/30 hover:ring-4 hover:ring-white/50 transition-all`}>
                      <span className="text-4xl">{tech.icon}</span>
                    </div>
                    {/* Glow on hover */}
                    <div className={`absolute inset-0 bg-gradient-to-br ${tech.color} rounded-full blur-xl opacity-0 group-hover:opacity-70 transition-opacity -z-10`} />

                    {/* Connection line to center */}
                    <motion.div
                      className="absolute inset-0"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: selectedTech?.name === tech.name ? 0.3 : 0 }}
                      style={{
                        background: `linear-gradient(to right, transparent, ${tech.color})`,
                        width: "2px",
                        height: `${radius}px`,
                        left: "50%",
                        top: "50%",
                        transformOrigin: "top",
                        transform: `rotate(${tech.angle + 180}deg)`,
                      }}
                    />
                  </motion.div>
                </motion.div>
              );
            })}

            {/* Orbital Rings */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="size-[560px] border border-white/10 rounded-full" />
              <div className="absolute size-[600px] border border-white/5 rounded-full" />
            </div>
          </div>

          {/* Tech Info Display */}
          <motion.div
            className="mt-20 min-h-32"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {selectedTech ? (
              <motion.div
                key={selectedTech.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 max-w-2xl mx-auto"
              >
                <div className="flex items-start gap-4">
                  <div className={`size-16 bg-gradient-to-br ${selectedTech.color} rounded-xl flex items-center justify-center text-3xl flex-shrink-0`}>
                    {selectedTech.icon}
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-1">{selectedTech.name}</h3>
                    <p className="text-orange-400 text-sm font-medium mb-3">{selectedTech.role}</p>
                    <p className="text-slate-300 leading-relaxed">{selectedTech.description}</p>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="text-center text-slate-400">
                <Zap className="size-8 mx-auto mb-2 opacity-50" />
                <p>Hover over any technology to learn more</p>
              </div>
            )}
          </motion.div>
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
            <button className="px-8 py-3 bg-white text-indigo-600 font-medium rounded-full hover:shadow-xl transition-shadow">
              View on GitHub
            </button>
          </motion.div>
        </div>
      </section>
    </div>
  );
}

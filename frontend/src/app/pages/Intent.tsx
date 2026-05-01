import { motion } from "motion/react";
import { Target, Heart, Shield, Users, Sparkles, Globe } from "lucide-react";

const intentions = [
  {
    icon: Target,
    title: "Our Mission",
    description:
      "To democratize access to railway information through innovative AI technology, making travel planning effortless for every Indian citizen.",
    color: "from-orange-500 to-red-500",
  },
  {
    icon: Heart,
    title: "Our Vision",
    description:
      "A future where technology bridges the gap between travelers and the vast Indian Railways network, creating seamless journey experiences.",
    color: "from-green-500 to-teal-500",
  },
  {
    icon: Shield,
    title: "Fair Use Commitment",
    description:
      "We operate under fair use principles, providing educational and informational services while respecting Indian Railways' systems and policies.",
    color: "from-blue-500 to-indigo-500",
  },
];

const principles = [
  {
    icon: Users,
    title: "User-First Approach",
    description: "Every feature is designed with travelers' needs at the forefront",
  },
  {
    icon: Sparkles,
    title: "Innovation & Excellence",
    description: "Leveraging cutting-edge AI to solve real-world travel challenges",
  },
  {
    icon: Globe,
    title: "Inclusive & Accessible",
    description: "Building solutions that work for everyone, everywhere in India",
  },
];

export function Intent() {
  return (
    <div className="pt-16">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-slate-900 via-indigo-900 to-blue-900 text-white py-24">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjEiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-10" />

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl lg:text-6xl font-bold mb-6">
              Building the Future of{" "}
              <span className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                Rail Travel
              </span>
            </h1>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              Our commitment to innovation, accessibility, and responsible technology use
            </p>
          </motion.div>
        </div>
      </section>

      {/* Main Intentions */}
      <section className="py-20 bg-gradient-to-b from-white to-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8">
            {intentions.map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.2 }}
                className="group"
              >
                <div className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all border border-slate-200 h-full">
                  <div className={`size-16 bg-gradient-to-br ${item.color} rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                    <item.icon className="size-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900 mb-4">{item.title}</h3>
                  <p className="text-slate-600 leading-relaxed">{item.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Fair Use Policy Details */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-white rounded-2xl p-8 lg:p-12 shadow-xl border border-indigo-200"
          >
            <div className="flex items-center gap-4 mb-8">
              <div className="size-12 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-lg flex items-center justify-center">
                <Shield className="size-6 text-white" />
              </div>
              <h2 className="text-3xl font-bold text-slate-900">Fair Use & Ethics</h2>
            </div>

            <div className="space-y-6 text-slate-700">
              <div>
                <h3 className="font-semibold text-lg text-slate-900 mb-2">Educational Purpose</h3>
                <p className="leading-relaxed">
                  This platform is developed as a prototype to demonstrate the potential of AI in enhancing railway information accessibility. It serves educational and research purposes while showcasing modern web technologies.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-lg text-slate-900 mb-2">Data Responsibility</h3>
                <p className="leading-relaxed">
                  We respect Indian Railways' official systems and do not attempt to bypass, scrape, or overload their infrastructure. All information is presented for demonstration purposes with proper attribution.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-lg text-slate-900 mb-2">Non-Commercial Use</h3>
                <p className="leading-relaxed">
                  This is a non-commercial, open-source initiative aimed at improving public access to information. We do not charge users or monetize railway data in any way.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-lg text-slate-900 mb-2">Attribution & Credits</h3>
                <p className="leading-relaxed">
                  All trademarks, logos, and data related to Indian Railways remain the property of the Ministry of Railways, Government of India. We acknowledge and respect all intellectual property rights.
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Principles Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold text-slate-900 mb-4">Our Guiding Principles</h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              The values that drive every decision we make
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {principles.map((principle, index) => (
              <motion.div
                key={principle.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15 }}
                className="text-center"
              >
                <div className="size-20 bg-gradient-to-br from-indigo-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <principle.icon className="size-10 text-indigo-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">{principle.title}</h3>
                <p className="text-slate-600">{principle.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-indigo-600 to-blue-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-white">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl font-bold mb-4">Questions or Feedback?</h2>
            <p className="text-white/90 mb-6">
              We're committed to transparency and continuous improvement. Reach out to us with your thoughts.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <button className="px-6 py-3 bg-white text-indigo-600 font-medium rounded-full hover:shadow-xl transition-shadow">
                Contact Us
              </button>
              <a 
                href="https://github.com/Vai201/Rail-Madad-Chatbot" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-block px-8 py-3 bg-white text-indigo-600 font-medium rounded-full hover:shadow-xl transition-shadow"
              >
                View on GitHub
              </a>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}

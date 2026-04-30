import { motion } from "motion/react";
import { Zap, Clock, Users, Star } from "lucide-react";

const trainCategories = [
  {
    name: "Vande Bharat Express",
    type: "Seater & Sleeper",
    image: "🚄",
    speed: "180 km/h",
    features: ["Indigenous", "AC", "WiFi", "Bio-Toilets"],
    description: "India's pride - fully air-conditioned, semi-high-speed trains",
    gradient: "from-blue-500 to-purple-600",
  },
  {
    name: "Rajdhani Express",
    type: "Premium AC",
    image: "🚂",
    speed: "160 km/h",
    features: ["Fully AC", "Meals Included", "Priority", "Bedding"],
    description: "Connecting state capitals with unmatched luxury",
    gradient: "from-red-500 to-orange-600",
  },
  {
    name: "Shatabdi Express",
    type: "Day Train",
    image: "⚡",
    speed: "150 km/h",
    features: ["AC Chair Car", "Meals", "Fast", "Comfortable"],
    description: "Premium day-time intercity travel experience",
    gradient: "from-green-500 to-teal-600",
  },
  {
    name: "Tejas Express",
    type: "Premium Service",
    image: "💫",
    speed: "200 km/h",
    features: ["Modern Coaches", "Entertainment", "WiFi", "Premium"],
    description: "Modern amenities with world-class service standards",
    gradient: "from-indigo-500 to-blue-600",
  },
  {
    name: "Duronto Express",
    type: "Non-Stop",
    image: "🎯",
    speed: "160 km/h",
    features: ["Limited Stops", "Fast", "AC & Non-AC", "Long Distance"],
    description: "Non-stop service between major cities for faster travel",
    gradient: "from-purple-500 to-pink-600",
  },
  {
    name: "Humsafar Express",
    type: "AC Sleeper",
    image: "🌙",
    speed: "130-160 km/h",
    features: ["All 3AC", "Bedding", "CCTV", "Secure"],
    description: "Comfortable overnight journey with enhanced security",
    gradient: "from-cyan-500 to-blue-600",
  },
  {
    name: "Double Decker",
    type: "High Capacity",
    image: "🏢",
    speed: "130 km/h",
    features: ["Two Levels", "AC Chair Car", "Spacious", "Unique"],
    description: "Innovative two-level design for increased capacity",
    gradient: "from-orange-500 to-red-600",
  },
  {
    name: "LHB Express",
    type: "Standard & Superfast",
    image: "🚃",
    speed: "110-130 km/h",
    features: ["Modern Coaches", "Safe", "Comfortable", "Reliable"],
    description: "German technology-based coaches for superior safety",
    gradient: "from-slate-500 to-gray-600",
  },
];

export function Trains() {
  return (
    <div className="pt-16">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-indigo-600 via-blue-600 to-cyan-600 text-white py-20">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjEiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-20" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <h1 className="text-5xl lg:text-6xl font-bold mb-6">Our Fleet</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto">
              From high-speed Vande Bharat to reliable LHB coaches - experience India's diverse railway network
            </p>
          </motion.div>
        </div>
      </section>

      {/* Trains Grid */}
      <section className="py-16 bg-gradient-to-b from-white to-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {trainCategories.map((train, index) => (
              <motion.div
                key={train.name}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ y: -8 }}
                className="group"
              >
                <div className="bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all border border-slate-200">
                  {/* Header with Gradient */}
                  <div className={`bg-gradient-to-br ${train.gradient} p-6 relative overflow-hidden`}>
                    <div className="absolute top-0 right-0 text-9xl opacity-10 transform translate-x-8 -translate-y-4">
                      {train.image}
                    </div>
                    <div className="relative">
                      <div className="text-5xl mb-3">{train.image}</div>
                      <h3 className="text-2xl font-bold text-white mb-1">{train.name}</h3>
                      <p className="text-white/90 text-sm">{train.type}</p>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <Zap className="size-4 text-indigo-600" />
                      <span className="text-sm font-medium text-slate-700">Max Speed: {train.speed}</span>
                    </div>

                    <p className="text-slate-600 mb-4 text-sm leading-relaxed">
                      {train.description}
                    </p>

                    {/* Features */}
                    <div className="space-y-2">
                      <div className="text-xs font-medium text-slate-700 mb-2">Key Features:</div>
                      <div className="flex flex-wrap gap-2">
                        {train.features.map((feature) => (
                          <span
                            key={feature}
                            className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-xs font-medium"
                          >
                            {feature}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Info Section */}
      <section className="py-16 bg-slate-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-gradient-to-br from-indigo-600 to-blue-600 rounded-2xl p-8 text-white text-center shadow-xl"
          >
            <Star className="size-12 mx-auto mb-4" />
            <h2 className="text-3xl font-bold mb-4">Book Your Journey Today</h2>
            <p className="text-white/90 mb-6 max-w-2xl mx-auto">
              Experience world-class rail travel with Indian Railways. Safe, comfortable, and connecting every corner of India.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <div className="flex items-center gap-2">
                <Clock className="size-5" />
                <span className="text-sm">On-Time Performance</span>
              </div>
              <div className="flex items-center gap-2">
                <Users className="size-5" />
                <span className="text-sm">23M+ Daily Travelers</span>
              </div>
              <div className="flex items-center gap-2">
                <Star className="size-5" />
                <span className="text-sm">World-Class Service</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}

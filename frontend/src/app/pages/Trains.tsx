import { motion } from "motion/react";
import { Zap, Clock, Users, Star } from "lucide-react";

const trainCategories = [
  {
    name: "Vande Bharat Express",
    type: "Seater & Sleeper",
    image: "🚄",
    imageUrl: "https://erail.in/images/info/Vande-Bharat.jpg",
    speed: "180 km/h",
    features: ["Indigenous", "AC", "WiFi", "Bio-Toilets"],
    description: "India's pride - fully air-conditioned, semi-high-speed trains",
  },
  {
    name: "Rajdhani Express",
    type: "Premium AC",
    image: "🚂",
    imageUrl: "https://www.jiyobangla.com/upload/1/news/1704455211_photo_11zon_1-640x400.jpg",
    speed: "160 km/h",
    features: ["Fully AC", "Meals Included", "Priority", "Bedding"],
    description: "Connecting state capitals with unmatched luxury",
  },
  {
    name: "Shatabdi Express",
    type: "Day Train",
    image: "⚡",
    imageUrl: "https://images.indianexpress.com/2025/11/Mumbai-ahmedabad-shatabdi-express.jpg",
    speed: "150 km/h",
    features: ["AC Chair Car", "Meals", "Fast", "Comfortable"],
    description: "Premium day-time intercity travel experience",
  },
  {
    name: "Tejas Express",
    type: "Premium Service",
    image: "💫",
    imageUrl: "http://trak.in/wp-content/uploads/2017/05/Tejas-Express.jpg",
    speed: "200 km/h",
    features: ["Modern Coaches", "Entertainment", "WiFi", "Premium"],
    description: "Modern amenities with world-class service standards",
  },
  {
    name: "Duronto Express",
    type: "Non-Stop",
    image: "🎯",
    imageUrl: "https://tripzdude.com/wp-content/uploads/2023/11/f8wacm.jpg",
    speed: "160 km/h",
    features: ["Limited Stops", "Fast", "AC & Non-AC", "Long Distance"],
    description: "Non-stop service between major cities for faster travel",
  },
  {
    name: "Humsafar Express",
    type: "AC Sleeper",
    image: "🌙",
    imageUrl: "https://i.ytimg.com/vi/v_Nokn6Pbxs/maxresdefault.jpg",
    speed: "130-160 km/h",
    features: ["All 3AC", "Bedding", "CCTV", "Secure"],
    description: "Comfortable overnight journey with enhanced security",
  },
  {
    name: "Double Decker",
    type: "High Capacity",
    image: "🏢",
    imageUrl: "https://i.pinimg.com/originals/e9/7d/ce/e97dce15709eadf5a3c24d579a7827c5.jpg",
    speed: "130 km/h",
    features: ["Two Levels", "AC Chair Car", "Spacious", "Unique"],
    description: "Innovative two-level design for increased capacity",
  },
  {
    name: "LHB Express",
    type: "Standard & Superfast",
    image: "🚃",
    imageUrl: "https://i.ytimg.com/vi/THIVviq3EBA/maxresdefault.jpg",
    speed: "110-130 km/h",
    features: ["Modern Coaches", "Safe", "Comfortable", "Reliable"],
    description: "German technology-based coaches for superior safety",
  },
  {
    name: "Maharaja Express",
    type: "Ultra-Luxury",
    image: "👑",
    imageUrl: "https://www.peakadventuretour.com/assets/images/maharaja-express-train_banner.webp",
    speed: "70-80 km/h",
    features: ["Luxury", "Royal Suites", "Guided Excursions", "Multi-City"],
    description: "Experience India's regal heritage aboard the world's leading Luxury Train",
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
                  
                  {/* --- HEADER WITH IMAGE & UNIVERSAL DARK OVERLAY --- */}
                  <div className="relative h-56 overflow-hidden">
                    {/* Background Image */}
                    <img 
                      src={train.imageUrl} 
                      alt={train.name} 
                      className="absolute inset-0 w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 ease-in-out"
                    />
                    
                    {/* Universal Dark Overlay for Text Readability */}
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/40 to-transparent" />
                    
                    {/* Header Content */}
                    <div className="absolute inset-0 p-6 flex flex-col justify-end z-10">
                      <div className="absolute top-4 right-4 text-4xl drop-shadow-md">
                        {train.image}
                      </div>
                      <h3 className="text-2xl font-bold text-white mb-1 drop-shadow-md">{train.name}</h3>
                      <p className="text-white/90 text-sm font-medium drop-shadow-md">{train.type}</p>
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
import { motion } from "motion/react";
import { Calendar, Users, MapPin, TrendingUp, AlertCircle, ExternalLink, Mail, Github, Linkedin } from "lucide-react";

const milestones = [
  {
    year: "1853",
    title: "The Genesis of a Network",
    description: "The inaugural 34-kilometer passenger run from Bori Bunder to Thane. Operating entirely on steam and manual ledgers, this single route laid the foundation for what would become the world's most complex transit network.",
    icon: "🚂",
    imageUrl: "https://irfca.org/gallery/main.php?g2_view=core.DownloadItem&g2_itemId=20236&g2_serialNumber=3",
  },
  {
    year: "1925",
    title: "The Electric Transition",
    description: "India's first electric train operates between Bombay VT and Poona (Today's Pune). This historic shift away from pure steam propulsion paved the way for the massive electrified network of modern India.",
    icon: "⚡",
    imageUrl: "https://irfca.org/gallery/main.php?g2_view=core.DownloadItem&g2_itemId=130340&g2_serialNumber=10",
  },
  {
    year: "1951",
    title: "Unification of the Grid",
    description: "Following Independence, 42 fragmented and independent railway systems are officially nationalized and merged into a single, unified entity: Indian Railways.",
    icon: "🇮🇳",
    imageUrl: "https://image.slidesharecdn.com/railwayzones-210708014356/75/Railway-zones-of-India-3-2048.jpg",
  },
  {
    year: "1986-1988",
    title: "Silicon & Speed",
    description: "The Centre for Railway Information Systems (CRIS) introduces computerized passenger reservation, shifting ticketing from paper queues to a digital database. Two years later, the Shatabdi Express is launched.",
    icon: "💻",
    imageUrl: "https://irfca.org/gallery/main.php?g2_view=core.DownloadItem&g2_itemId=30263&g2_serialNumber=2",
  },
  {
    year: "2016",
    title: "Breaking the Speed Barrier",
    description: "The Gatimaan Express is inaugurated. Reaching operational speeds of 160 km/h on the Delhi-Agra route, it officially marks India's entry into the semi-high-speed transit era.",
    icon: "🚄",
    imageUrl: "https://ichef.bbci.co.uk/ace/standard/976/cpsprodpb/7D4E/production/_89087023_dsc_8995.jpg.webp",
  },
  {
    year: "2019",
    title: "The 'Make in India' Masterpiece",
    description: "Train 18, the Vande Bharat Express, revolutionizes Indian engineering. The self-propelled, engineless trainset eliminates the traditional locomotive, offering rapid acceleration and aircraft-like passenger amenities.",
    icon: "🎯",
    imageUrl: "https://www.financialexpress.com/wp-content/uploads/2024/09/vande-bharat-express-5.jpg",
  },
  {
    year: "2021",
    title: "The Airport-Class Transit Hubs",
    description: "A paradigm shift in infrastructure begins with the inauguration of world-class, redeveloped stations like Rani Kamlapati and Gandhinagar Capital. Transit nodes are transformed into multi-modal commercial hubs.",
    icon: "🏛️",
    imageUrl: "https://www.garud.org.in/wp-content/uploads/2020/07/1.-Main-Slider-Image-Replace-scaled.jpg",
  },
  {
    year: "2022",
    title: "KAVACH & The Freight Revolution",
    description: "The indigenous Automatic Train Protection (ATP) system, KAVACH, sees accelerated nationwide deployment. Concurrently, major stretches of the Dedicated Freight Corridors (DFC) become operational.",
    icon: "🛡️",
    imageUrl: "https://www.itln.in/h-upload/2025/05/19/82166-image-09.webp",
  },
  {
    year: "2023",
    title: "Regional Rapid & Push-Pull Technology",
    description: "The network expands its footprint with Namo Bharat (RRTS) for rapid regional transit, and the Amrit Bharat Express, utilizing advanced push-pull locomotive technology for mass-scale travel.",
    icon: "🚇",
    imageUrl: "https://images.financialexpressdigital.com/2023/05/1-298.jpg?w=1600",
  },
  {
    year: "2024",
    title: "Conquering the Himalayas",
    description: "Completion of the monumental Chenab Railway Bridge. Soaring 359 meters above the riverbed—taller than the Eiffel Tower—it finally connects the Kashmir Valley to the national railway grid.",
    icon: "🌉",
    imageUrl: "https://static.businessworld.in/chenab-bridge-_20250624183411_original_image_24.webp",
  },
  {
    year: "2025-2026",
    title: "Total Electrification & The AI Horizon",
    description: "As the network approaches 100% route electrification, the digital layer is upgraded with AI-driven predictive maintenance.",
    icon: "💡",
    imageUrl: "https://imgeng.jagran.com/images/2025/08/17/article/image/vande-bharat-sleeper-train-1755426851819.webp",
  },
];

const stats = [
  { icon: Users, value: "23M+", label: "Daily Passengers" },
  { icon: MapPin, value: "68,000km", label: "Route Network" },
  { icon: Calendar, value: "171+", label: "Years of Service" },
  { icon: TrendingUp, value: "1.3M+", label: "Employees" },
];

export function Home() {
  return (
    <div className="pt-16">
      {/* RailMadad Prototype Banner */}
      <section className="bg-gradient-to-r from-amber-50 to-amber-100 border-b-2 border-amber-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-center gap-3 text-center"
          >
            <AlertCircle className="size-5 text-amber-700 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-amber-900">
                Prototype Project: AI-Driven Multilingual Redressal for Indian Railways Complaint System (RailMadad)
              </p>
              <p className="text-xs text-amber-700 mt-0.5">
                Educational demonstration • Not affiliated with official Indian Railways systems
              </p>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-900 via-blue-900 to-slate-900 text-white">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS1vcGFjaXR5PSIwLjEiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNncmlkKSIvPjwvc3ZnPg==')] opacity-30" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 lg:py-32">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center max-w-4xl mx-auto"
          >
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-5xl lg:text-7xl font-bold mb-6"
            >
              171 Years of{" "}
              <span className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                Excellence
              </span>
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="text-xl lg:text-2xl text-blue-100 mb-8"
            >
              Connecting India, Powering Dreams, Building the Future
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="text-sm text-blue-200"
            >
              From steam engines to Vande Bharat - A journey of transformation
            </motion.div>
          </motion.div>
        </div>

        {/* Wave Divider */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M0 0L60 10C120 20 240 40 360 45C480 50 600 40 720 35C840 30 960 30 1080 35C1200 40 1320 50 1380 55L1440 60V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0V0Z"
              className="fill-white"
            />
          </svg>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl p-6 shadow-sm border border-indigo-100 hover:shadow-md transition-shadow"
              >
                <stat.icon className="size-8 text-indigo-600 mb-3" />
                <div className="text-3xl font-bold text-slate-900 mb-1">{stat.value}</div>
                <div className="text-sm text-slate-600">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline Section */}
      <section className="py-20 bg-gradient-to-b from-white to-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent mb-4">
              Indian Railways: The Architecture of a Nation
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              From humble beginnings to the world's fourth-largest railway network
            </p>
          </motion.div>

          <div className="relative">
            {/* Timeline Line */}
            <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-indigo-500 via-blue-400 to-indigo-500" />

            <div className="space-y-12">
              {milestones.map((milestone, index) => (
                <motion.div
                  key={`${milestone.year}-${milestone.title}`}
                  initial={{ opacity: 0, x: index % 2 === 0 ? -50 : 50 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.5 }}
                  className={`relative flex flex-col lg:flex-row items-center gap-8 group ${
                    index % 2 === 0 ? "lg:flex-row" : "lg:flex-row-reverse"
                  }`}
                >
                  {/* Content */}
                  <div className={`flex-1 ${index % 2 === 0 ? "lg:text-right" : "lg:text-left"} w-full`}>
                    <div className={`inline-block bg-white rounded-2xl p-6 shadow-md border border-indigo-100 hover:shadow-xl transition-all duration-300 w-full max-w-lg ${index % 2 === 0 ? "lg:mr-auto lg:ml-0 mx-auto" : "lg:ml-auto lg:mr-0 mx-auto"}`}>
                      
                      <div className={`flex items-center gap-3 mb-3 ${index % 2 === 0 ? "lg:flex-row-reverse lg:justify-end" : ""}`}>
                        <span className="text-3xl">{milestone.icon}</span>
                        <span className="text-2xl font-bold text-indigo-600">{milestone.year}</span>
                      </div>
                      
                      <h3 className="text-xl font-bold text-slate-900 mb-2">
                        {milestone.title}
                      </h3>
                      <p className="text-slate-600 mb-5 leading-relaxed">{milestone.description}</p>
                      
                      {/* FIXED RESPONSIVE IMAGE CONTAINER */}
                      <div className="relative w-full h-48 sm:h-56 md:h-64 rounded-xl overflow-hidden shadow-inner group-hover:shadow-md transition-shadow">
                        <div className="absolute inset-0 bg-indigo-900/10 group-hover:bg-transparent transition-colors duration-500 z-10" />
                        <img 
                          src={milestone.imageUrl} 
                          alt={milestone.title}
                          className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-700"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Timeline Dot */}
                  <div className="hidden lg:block relative z-10">
                    <div className="size-5 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-full ring-4 ring-white shadow-md group-hover:scale-125 transition-transform duration-300" />
                  </div>

                  {/* Spacer for alternating layout */}
                  <div className="hidden lg:block flex-1" />
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Disclaimer Section */}
      <section className="py-16 bg-slate-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-white rounded-2xl p-8 shadow-lg border-2 border-amber-200"
          >
            <div className="flex items-start gap-4 mb-6">
              <AlertCircle className="size-8 text-amber-600 flex-shrink-0 mt-1" />
              <div>
                <h2 className="text-2xl font-bold text-slate-900 mb-4">Important Disclaimer</h2>
                <div className="space-y-4 text-slate-700">
                  <p>
                    This is an <strong>educational prototype</strong> developed for the project titled
                    <strong> "AI-Driven Multilingual Redressal for Indian Railways Complaint System (RailMadad)"</strong>.
                    This platform demonstrates the potential of artificial intelligence in enhancing railway complaint management systems.
                  </p>
                  <p>
                    <strong>We are NOT affiliated with, endorsed by, or connected to:</strong>
                  </p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Indian Railways (Ministry of Railways, Government of India)</li>
                    <li>RailMadad (Official railway complaint portal)</li>
                    <li>CRIS (Centre for Railway Information Systems)</li>
                    <li>IRCTC (Indian Railway Catering and Tourism Corporation)</li>
                  </ul>
                  <p>
                    All trademarks, logos, and official information belong to their respective owners.
                    This project is built for educational and research purposes under fair use principles.
                  </p>
                  <div className="flex items-center gap-4 pt-4 border-t border-slate-200 mt-6">
                    <a
                      href="https://indianrailways.gov.in"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-indigo-600 hover:text-indigo-700 font-medium"
                    >
                      <ExternalLink className="size-4" />
                      Visit Official Indian Railways Website
                    </a>
                  </div>
                  <div className="flex items-center gap-4">
                    <a
                      href="https://railmadad.indianrailways.gov.in"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-indigo-600 hover:text-indigo-700 font-medium"
                    >
                      <ExternalLink className="size-4" />
                      Visit Official RailMadad Portal
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Personal Information Section */}
      <section className="py-16 bg-gradient-to-br from-indigo-900 to-blue-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center"
          >
            <h2 className="text-3xl font-bold mb-6">About the Developer</h2>
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
              <div className="mb-6">
                <div className="size-20 bg-gradient-to-br from-indigo-400 to-blue-400 rounded-full mx-auto mb-4 flex items-center justify-center text-4xl shadow-inner">
                  👨‍💻
                </div>
                <h3 className="text-xl font-bold mb-2">Student Developer</h3>
                <p className="text-blue-200 mb-6">
                  Computer Science Engineering Student | AI & ML Enthusiast
                </p>
              </div>

              <div className="text-left space-y-4 text-blue-100 mb-6">
                <p>
                  This project represents my exploration of AI-driven solutions for real-world problems faced by Indian Railways passengers.
                  By combining natural language processing, multilingual support, and modern web technologies,
                  this prototype demonstrates how technology can improve complaint redressal systems.
                </p>
                <p>
                  <strong className="text-white">Technologies Used:</strong> React, TypeScript, Tailwind CSS,
                  Google Cloud Platform, Dialogflow, Gemini AI, Python
                </p>
              </div>

              <div className="flex justify-center gap-4 flex-wrap">
                <a
                  href="mailto:your.email@example.com"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
                >
                  <Mail className="size-4" />
                  <span className="text-sm">Email</span>
                </a>
                <a
                  href="https://github.com/yourusername"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
                >
                  <Github className="size-4" />
                  <span className="text-sm">GitHub</span>
                </a>
                <a
                  href="https://linkedin.com/in/yourprofile"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
                >
                  <Linkedin className="size-4" />
                  <span className="text-sm">LinkedIn</span>
                </a>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-indigo-600 to-blue-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl lg:text-4xl font-bold mb-6">
              Experience the Future of Complaint Management
            </h2>
            <p className="text-lg text-blue-100 mb-8">
              Explore how AI can revolutionize railway passenger services
            </p>
            <a
              href="/technology"
              className="inline-block px-8 py-3 bg-white text-indigo-600 font-medium rounded-full hover:shadow-xl hover:scale-105 transition-all"
            >
              Explore Technology Stack
            </a>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
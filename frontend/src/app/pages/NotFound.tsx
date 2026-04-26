import { Link } from "react-router";
import { Home, ArrowLeft, Search } from "lucide-react";
import { motion } from "motion/react";

export function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 pt-16">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* 404 Visual */}
          <div className="mb-8">
            <motion.div
              animate={{ rotate: [0, 5, -5, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="text-9xl mb-4"
            >
              🚂
            </motion.div>
            <h1 className="text-8xl font-bold bg-gradient-to-r from-indigo-600 to-blue-600 bg-clip-text text-transparent mb-4">
              404
            </h1>
          </div>

          {/* Message */}
          <h2 className="text-3xl font-bold text-slate-900 mb-4">Station Not Found</h2>
          <p className="text-lg text-slate-600 mb-8">
            Looks like this train has derailed! The page you're looking for doesn't exist.
          </p>

          {/* Actions */}
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white font-medium rounded-full hover:shadow-lg transition-shadow"
            >
              <Home className="size-4" />
              Go Home
            </Link>
            <button
              onClick={() => window.history.back()}
              className="inline-flex items-center gap-2 px-6 py-3 bg-white text-slate-700 font-medium rounded-full border border-slate-300 hover:bg-slate-50 transition-colors"
            >
              <ArrowLeft className="size-4" />
              Go Back
            </button>
          </div>

          {/* Quick Links */}
          <div className="mt-12 pt-8 border-t border-slate-200">
            <p className="text-sm text-slate-600 mb-4">Popular destinations:</p>
            <div className="flex flex-wrap justify-center gap-3">
              <Link
                to="/trains"
                className="px-4 py-2 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium hover:bg-indigo-200 transition-colors"
              >
                Explore Trains
              </Link>
              <Link
                to="/technology"
                className="px-4 py-2 bg-purple-100 text-purple-700 rounded-full text-sm font-medium hover:bg-purple-200 transition-colors"
              >
                Technology
              </Link>
              <Link
                to="/intent"
                className="px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium hover:bg-blue-200 transition-colors"
              >
                Our Intent
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

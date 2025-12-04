import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Brain, Zap, TrendingUp, Target } from 'lucide-react';
import { Button } from '../components/ui/button';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#020617] relative overflow-hidden">
      {/* Hero Background Image with Overlay */}
      <div 
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: 'url(https://images.unsplash.com/photo-1627424921687-8a600e8434a7?crop=entropy&cs=srgb&fm=jpg&q=85)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <div className="absolute inset-0 bg-[#020617] opacity-90"></div>
      </div>

      {/* Hero Glow Effect */}
      <div className="absolute inset-0 hero-glow z-0"></div>

      {/* Content */}
      <div className="relative z-10">
        <div className="container mx-auto px-6 md:px-12 lg:px-16 min-h-screen flex flex-col justify-center items-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center max-w-5xl"
          >
            {/* Logo/Icon */}
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, duration: 0.6 }}
              className="flex justify-center mb-8"
            >
              <div className="relative">
                <Brain className="w-24 h-24 md:w-32 md:h-32 text-[#22d3ee] animate-glow" />
                <Zap className="w-12 h-12 text-[#f472b6] absolute -bottom-2 -right-2" />
              </div>
            </motion.div>

            {/* Main Heading */}
            <h1 
              className="text-5xl md:text-7xl font-bold tracking-tight mb-6 text-[#f8fafc]"
              data-testid="landing-hero-title"
            >
              BrainPath
            </h1>

            {/* Subtitle */}
            <p className="text-xl md:text-2xl text-[#94a3b8] mb-8 leading-relaxed max-w-3xl mx-auto">
              Transform how you learn with our adaptive AI-powered platform
            </p>

            {/* Description */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4, duration: 0.8 }}
              className="bg-[#0f172a] border border-[#1e293b] rounded-3xl p-8 md:p-12 mb-12 text-left neon-glow"
              data-testid="landing-description-card"
            >
              <p className="text-base md:text-lg text-[#94a3b8] leading-relaxed mb-6">
                <strong className="text-[#22d3ee]">BrainPath</strong> is designed to create a truly personalized and adaptive learning experience by understanding how each student learns best.
              </p>
              
              <div className="grid md:grid-cols-2 gap-6 mt-8">
                <div className="flex gap-4">
                  <Target className="w-8 h-8 text-[#22d3ee] flex-shrink-0" />
                  <div>
                    <h3 className="text-lg font-semibold text-[#f8fafc] mb-2">Personalized Learning</h3>
                    <p className="text-sm text-[#94a3b8]">Three core techniques: passages, videos, and flowcharts tailored to your level</p>
                  </div>
                </div>
                
                <div className="flex gap-4">
                  <Zap className="w-8 h-8 text-[#f472b6] flex-shrink-0" />
                  <div>
                    <h3 className="text-lg font-semibold text-[#f8fafc] mb-2">AI-Powered Assessment</h3>
                    <p className="text-sm text-[#94a3b8]">Smart questions that adapt to your progress and learning speed</p>
                  </div>
                </div>
                
                <div className="flex gap-4">
                  <TrendingUp className="w-8 h-8 text-[#a3e635] flex-shrink-0" />
                  <div>
                    <h3 className="text-lg font-semibold text-[#f8fafc] mb-2">Performance Analytics</h3>
                    <p className="text-sm text-[#94a3b8]">Track accuracy, speed, strengths, and areas for improvement</p>
                  </div>
                </div>
                
                <div className="flex gap-4">
                  <Brain className="w-8 h-8 text-[#c084fc] flex-shrink-0" />
                  <div>
                    <h3 className="text-lg font-semibold text-[#f8fafc] mb-2">Adaptive Difficulty</h3>
                    <p className="text-sm text-[#94a3b8]">Content becomes progressively challenging as you improve</p>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* CTA Button */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.6 }}
            >
              <Button
                size="lg"
                className="text-xl px-12 py-6 h-auto rounded-full bg-[#22d3ee] text-[#020617] hover:bg-[#22d3ee]/90 font-bold shadow-[0_0_15px_rgba(34,211,238,0.5)] hover:shadow-[0_0_25px_rgba(34,211,238,0.7)] hover:scale-105 transition-all duration-300"
                onClick={() => navigate('/auth')}
                data-testid="get-started-btn"
              >
                Get Started
              </Button>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

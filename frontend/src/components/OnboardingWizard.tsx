import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ArrowRight, ArrowLeft, Upload, MessageSquare, Calendar, DollarSign, BarChart3 } from 'lucide-react';
import { GlassCard } from './ui/GlassCard';
import { Button } from './ui/Button';

interface OnboardingWizardProps {
  onComplete: () => void;
}

const steps = [
  {
    id: 1,
    title: "Welcome to VintedBot! 👋",
    description: "The AI-powered bot that automates your Vinted sales",
    content: (
      <div className="text-center py-8">
        <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-violet-500 to-purple-600 rounded-3xl flex items-center justify-center">
          <span className="text-5xl">🤖</span>
        </div>
        <h2 className="text-3xl font-bold text-white mb-4">
          Sell Smarter, Faster
        </h2>
        <p className="text-slate-400 max-w-md mx-auto text-lg">
          VintedBot uses AI to analyze your items, optimize pricing, schedule publications, and handle messages automatically.
        </p>

        <div className="grid grid-cols-3 gap-4 mt-8 max-w-lg mx-auto">
          <div className="text-center">
            <div className="text-3xl font-bold text-violet-400 mb-1">5+</div>
            <div className="text-sm text-slate-500">AI Features</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400 mb-1">24/7</div>
            <div className="text-sm text-slate-500">Automation</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-400 mb-1">+40%</div>
            <div className="text-sm text-slate-500">Avg Sales</div>
          </div>
        </div>
      </div>
    )
  },
  {
    id: 2,
    title: "Upload Your First Photos 📸",
    description: "Let AI analyze and create descriptions",
    content: (
      <div className="text-center py-8">
        <div className="border-2 border-dashed border-white/20 rounded-xl p-12 mb-6 hover:border-violet-500/50 transition-colors cursor-pointer">
          <Upload className="w-16 h-16 text-violet-400 mx-auto mb-4" />
          <p className="text-white font-semibold mb-2">Drag & drop photos</p>
          <p className="text-sm text-slate-400">or click to browse</p>
        </div>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          AI will detect item type, condition, suggest pricing, and generate SEO-optimized descriptions automatically.
        </p>
      </div>
    )
  },
  {
    id: 3,
    title: "Enable AI Features 🤖",
    description: "Turn on smart automation",
    content: (
      <div className="space-y-3 py-4">
        {[
          {
            icon: MessageSquare,
            title: 'AI Auto-Messages',
            desc: 'Let GPT-4 respond to buyers automatically',
            color: 'from-blue-500 to-cyan-500'
          },
          {
            icon: Calendar,
            title: 'Smart Scheduling',
            desc: 'ML-powered optimal publication times',
            color: 'from-violet-500 to-purple-500'
          },
          {
            icon: DollarSign,
            title: 'Price Optimizer',
            desc: 'AI pricing strategies to maximize profit',
            color: 'from-green-500 to-emerald-500'
          },
          {
            icon: BarChart3,
            title: 'ML Analytics',
            desc: 'Revenue predictions & insights',
            color: 'from-orange-500 to-red-500'
          }
        ].map((feature) => (
          <motion.div
            key={feature.title}
            className="flex items-center gap-4 p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className={`p-3 bg-gradient-to-br ${feature.color} rounded-lg`}>
              <feature.icon className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h4 className="text-white font-semibold">{feature.title}</h4>
              <p className="text-sm text-slate-400">{feature.desc}</p>
            </div>
            <input
              type="checkbox"
              className="w-5 h-5 accent-violet-500 cursor-pointer"
              defaultChecked
            />
          </motion.div>
        ))}
      </div>
    )
  },
  {
    id: 4,
    title: "Keyboard Shortcuts ⌨️",
    description: "Navigate like a pro",
    content: (
      <div className="py-4">
        <div className="space-y-3 max-w-md mx-auto">
          {[
            { keys: ['⌘', 'K'], desc: 'Command Palette' },
            { keys: ['⌘', 'H'], desc: 'Dashboard' },
            { keys: ['⌘', 'U'], desc: 'Upload Photos' },
            { keys: ['⌘', 'D'], desc: 'My Drafts' },
            { keys: ['⌘', 'M'], desc: 'Messages' },
            { keys: ['⌘', 'P'], desc: 'Publish' },
            { keys: ['?'], desc: 'Show all shortcuts' }
          ].map((shortcut, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
            >
              <div className="flex items-center gap-2">
                {shortcut.keys.map((key, j) => (
                  <kbd
                    key={j}
                    className="px-2 py-1 bg-slate-800 border border-white/20 rounded text-white font-mono text-sm"
                  >
                    {key}
                  </kbd>
                ))}
              </div>
              <span className="text-slate-400 text-sm">{shortcut.desc}</span>
            </div>
          ))}
        </div>
      </div>
    )
  },
  {
    id: 5,
    title: "You're All Set! 🎉",
    description: "Start selling with AI automation",
    content: (
      <div className="text-center py-8">
        <motion.div
          className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', delay: 0.2 }}
        >
          <Check className="w-12 h-12 text-white" />
        </motion.div>
        <h2 className="text-2xl font-bold text-white mb-4">
          Ready to Automate!
        </h2>
        <p className="text-slate-400 mb-8 max-w-md mx-auto">
          Your VintedBot is configured and ready to boost your sales. Start uploading items and let AI do the work!
        </p>

        <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto">
          <div className="p-4 bg-violet-500/10 rounded-xl border border-violet-500/20">
            <div className="text-2xl font-bold text-violet-400 mb-1">GPT-4</div>
            <div className="text-xs text-slate-400">AI Powered</div>
          </div>
          <div className="p-4 bg-green-500/10 rounded-xl border border-green-500/20">
            <div className="text-2xl font-bold text-green-400 mb-1">PWA</div>
            <div className="text-xs text-slate-400">Offline Ready</div>
          </div>
          <div className="p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
            <div className="text-2xl font-bold text-blue-400 mb-1">ML</div>
            <div className="text-xs text-slate-400">Predictions</div>
          </div>
          <div className="p-4 bg-orange-500/10 rounded-xl border border-orange-500/20">
            <div className="text-2xl font-bold text-orange-400 mb-1">Auto</div>
            <div className="text-xs text-slate-400">24/7 Active</div>
          </div>
        </div>
      </div>
    )
  }
];

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const isLastStep = currentStep === steps.length - 1;
  const isFirstStep = currentStep === 0;

  const handleNext = () => {
    if (isLastStep) {
      onComplete();
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(0, prev - 1));
  };

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <motion.div
        className="max-w-3xl w-full my-8"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <GlassCard className="p-8">
          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm text-slate-400">
                Step {currentStep + 1} of {steps.length}
              </span>
              <span className="text-sm text-violet-400 font-semibold">
                {Math.round(((currentStep + 1) / steps.length) * 100)}%
              </span>
            </div>
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-violet-500 to-purple-600"
                initial={{ width: 0 }}
                animate={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
              />
            </div>
          </div>

          {/* Step Indicators */}
          <div className="flex justify-center gap-2 mb-8">
            {steps.map((step, index) => (
              <button
                key={step.id}
                onClick={() => setCurrentStep(index)}
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                  index === currentStep
                    ? 'bg-violet-500 text-white'
                    : index < currentStep
                    ? 'bg-green-500 text-white'
                    : 'bg-white/10 text-slate-500'
                }`}
              >
                {index < currentStep ? <Check className="w-5 h-5" /> : index + 1}
              </button>
            ))}
          </div>

          {/* Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="mb-8"
            >
              <h1 className="text-3xl font-bold text-white mb-2 text-center">
                {steps[currentStep].title}
              </h1>
              <p className="text-slate-400 mb-6 text-center">
                {steps[currentStep].description}
              </p>

              {steps[currentStep].content}
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex justify-between items-center pt-6 border-t border-white/10">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={isFirstStep}
              icon={ArrowLeft}
            >
              Back
            </Button>

            <Button
              onClick={handleNext}
              icon={isLastStep ? Check : ArrowRight}
              className="min-w-[120px]"
            >
              {isLastStep ? 'Get Started 🚀' : 'Next'}
            </Button>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  );
}

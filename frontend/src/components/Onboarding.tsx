import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Check,
  ArrowRight,
  Upload,
  Sparkles,
  Users,
  Settings,
  Zap
} from 'lucide-react';
import confetti from 'canvas-confetti';
import Button from './ui/Button';
import { cn } from '@/lib/utils';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  action?: string;
  href?: string;
}

const steps: OnboardingStep[] = [
  {
    id: 'welcome',
    title: 'Bienvenue sur VintedBot ! 🎉',
    description: 'Automatisez vos ventes Vinted avec l\'IA en 4 étapes simples',
    icon: <Sparkles className="w-8 h-8" />
  },
  {
    id: 'account',
    title: 'Connectez votre compte Vinted',
    description: 'Synchronisez votre compte pour automatiser vos publications',
    icon: <Users className="w-8 h-8" />,
    action: 'Connecter',
    href: '/accounts'
  },
  {
    id: 'upload',
    title: 'Uploadez vos premières photos',
    description: 'L\'IA analysera vos photos et générera des descriptions optimisées',
    icon: <Upload className="w-8 h-8" />,
    action: 'Uploader',
    href: '/upload'
  },
  {
    id: 'automation',
    title: 'Configurez l\'automatisation',
    description: 'Paramétrez le bump automatique et les réponses aux messages',
    icon: <Zap className="w-8 h-8" />,
    action: 'Configurer',
    href: '/automation'
  },
  {
    id: 'done',
    title: 'Vous êtes prêt ! 🚀',
    description: 'Votre compte est configuré. Commencez à vendre plus vite !',
    icon: <Check className="w-8 h-8" />
  }
];

export default function Onboarding() {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);

  useEffect(() => {
    // Check if user has seen onboarding
    const hasSeenOnboarding = localStorage.getItem('hasSeenOnboarding');
    if (!hasSeenOnboarding) {
      setIsOpen(true);
    }
  }, []);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
      setCompletedSteps([...completedSteps, steps[currentStep].id]);
    } else {
      handleComplete();
    }
  };

  const handleSkip = () => {
    localStorage.setItem('hasSeenOnboarding', 'true');
    setIsOpen(false);
  };

  const handleComplete = () => {
    localStorage.setItem('hasSeenOnboarding', 'true');
    setIsOpen(false);

    // Celebrate!
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });
  };

  const step = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden"
            >
              {/* Header */}
              <div className="relative p-8 bg-gradient-to-br from-brand-600 to-purple-600 text-white">
                <button
                  onClick={handleSkip}
                  className="absolute top-4 right-4 p-2 hover:bg-white/20 rounded-xl transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>

                {/* Progress */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white/80">
                      Étape {currentStep + 1}/{steps.length}
                    </span>
                    <span className="text-sm font-medium text-white/80">
                      {Math.round(progress)}%
                    </span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-2 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      className="h-full bg-white"
                    />
                  </div>
                </div>

                {/* Icon */}
                <motion.div
                  key={currentStep}
                  initial={{ scale: 0, rotate: -180 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: 'spring', duration: 0.6 }}
                  className="w-20 h-20 bg-white rounded-2xl flex items-center justify-center text-brand-600 mx-auto mb-6"
                >
                  {step.icon}
                </motion.div>

                {/* Title */}
                <motion.h2
                  key={`title-${currentStep}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-3xl font-bold text-center mb-3"
                >
                  {step.title}
                </motion.h2>

                {/* Description */}
                <motion.p
                  key={`desc-${currentStep}`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="text-lg text-white/90 text-center"
                >
                  {step.description}
                </motion.p>
              </div>

              {/* Content */}
              <div className="p-8">
                {/* Steps indicator */}
                <div className="flex items-center justify-center gap-2 mb-8">
                  {steps.map((s, index) => (
                    <div
                      key={s.id}
                      className={cn(
                        'w-3 h-3 rounded-full transition-all',
                        index === currentStep
                          ? 'bg-brand-600 w-8'
                          : completedSteps.includes(s.id)
                          ? 'bg-success-500'
                          : 'bg-gray-200'
                      )}
                    />
                  ))}
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  {currentStep > 0 && (
                    <Button
                      variant="secondary"
                      onClick={() => setCurrentStep(currentStep - 1)}
                      className="flex-1"
                    >
                      Retour
                    </Button>
                  )}

                  {step.action ? (
                    <Button
                      variant="primary"
                      onClick={() => {
                        window.location.href = step.href || '/';
                        handleSkip();
                      }}
                      icon={<ArrowRight className="w-5 h-5" />}
                      iconPosition="right"
                      className="flex-1"
                    >
                      {step.action}
                    </Button>
                  ) : (
                    <Button
                      variant="primary"
                      onClick={handleNext}
                      icon={currentStep === steps.length - 1 ? <Check className="w-5 h-5" /> : <ArrowRight className="w-5 h-5" />}
                      iconPosition="right"
                      className="flex-1"
                    >
                      {currentStep === steps.length - 1 ? 'Terminer' : 'Suivant'}
                    </Button>
                  )}
                </div>

                {/* Skip button */}
                {currentStep < steps.length - 1 && (
                  <button
                    onClick={handleSkip}
                    className="w-full text-center text-sm text-gray-500 hover:text-gray-700 mt-4 transition-colors"
                  >
                    Passer le tutoriel
                  </button>
                )}
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}

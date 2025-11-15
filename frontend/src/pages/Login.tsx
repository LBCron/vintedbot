import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { Mail, Lock, LogIn, ArrowRight, Shield, Sparkles, Zap } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { GlassCard } from '../components/ui/GlassCard';
import toast from 'react-hot-toast';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const isEmailValid = email.length > 0 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const emailError = email.length > 0 && !isEmailValid ? 'Email invalide' : '';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!isEmailValid) {
      toast.error('Veuillez entrer un email valide');
      return;
    }

    if (password.length < 8) {
      toast.error('Le mot de passe doit contenir au moins 8 caractères');
      return;
    }

    setLoading(true);

    try {
      await login({ email, password });

      if (rememberMe) {
        localStorage.setItem('remember_me', 'true');
      }

      toast.success('Connexion réussie ! 🎉');
      navigate('/dashboard');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail;

      if (errorMessage?.includes('Invalid email')) {
        toast.error('Email ou mot de passe incorrect');
      } else if (errorMessage?.includes('password')) {
        toast.error('Mot de passe incorrect');
      } else if (errorMessage?.includes('not found')) {
        toast.error('Aucun compte trouvé avec cet email');
      } else {
        toast.error('Erreur de connexion. Veuillez réessayer.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className="absolute -top-40 -right-40 w-80 h-80 bg-violet-500/30 rounded-full blur-3xl"
        />
        <motion.div
          animate={{
            scale: [1, 1.3, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1
          }}
          className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-500/30 rounded-full blur-3xl"
        />
      </div>

      {/* Main card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.5, type: "spring" }}
        className="w-full max-w-md relative z-10"
      >
        <GlassCard className="p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.2 }}
              className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl mb-4 shadow-lg shadow-violet-500/50"
            >
              <Sparkles className="w-10 h-10 text-white" />
            </motion.div>
            <motion.h1
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-4xl font-bold bg-gradient-to-r from-white via-violet-200 to-purple-200 bg-clip-text text-transparent mb-2"
            >
              VintedBot
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-slate-400 font-medium"
            >
              Automatisez vos ventes Vinted avec l'IA
            </motion.p>
          </div>

          {/* Form */}
          <motion.form
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            onSubmit={handleSubmit}
            className="space-y-5"
          >
            {/* Email */}
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="vous@exemple.com"
              icon={Mail}
              error={emailError}
              required
            />

            {/* Password */}
            <div className="space-y-3">
              <Input
                label="Mot de passe"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                icon={Lock}
                required
              />

              {/* Remember me + Forgot password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-2 border-violet-500/50 text-violet-600 focus:ring-2 focus:ring-violet-500 focus:ring-offset-0 cursor-pointer transition-all bg-white/5"
                  />
                  <span className="text-sm text-slate-400 group-hover:text-white transition-colors">
                    Se souvenir de moi
                  </span>
                </label>

                <Link
                  to="/forgot-password"
                  className="text-sm text-violet-400 hover:text-violet-300 font-medium transition-colors"
                >
                  Mot de passe oublié ?
                </Link>
              </div>
            </div>

            {/* Submit button */}
            <Button
              type="submit"
              disabled={loading}
              loading={loading}
              icon={loading ? undefined : LogIn}
              className="w-full"
              size="lg"
            >
              {loading ? 'Connexion en cours...' : 'Se connecter'}
            </Button>
          </motion.form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-transparent text-slate-400">ou</span>
            </div>
          </div>

          {/* Register link */}
          <div className="text-center">
            <p className="text-sm text-slate-400">
              Pas encore de compte ?{' '}
              <Link
                to="/register"
                className="text-violet-400 hover:text-violet-300 font-semibold transition-colors inline-flex items-center gap-1 group"
              >
                Créer un compte
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </p>
          </div>

          {/* Security badge */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="mt-6 pt-6 border-t border-white/10"
          >
            <div className="flex items-center justify-center gap-2 text-sm text-slate-400">
              <Shield className="w-4 h-4 text-green-400" />
              <span>Connexion sécurisée SSL • Vos données sont chiffrées</span>
            </div>
          </motion.div>
        </GlassCard>

        {/* Footer links */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
          className="mt-6 text-center text-xs text-slate-500 space-x-4"
        >
          <a href="#" className="hover:text-slate-400 transition-colors">Politique de confidentialité</a>
          <span>•</span>
          <a href="#" className="hover:text-slate-400 transition-colors">Conditions d'utilisation</a>
        </motion.div>
      </motion.div>
    </div>
  );
}

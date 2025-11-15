import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { Mail, Lock, User, UserPlus, ArrowRight, Shield, Sparkles, Check } from 'lucide-react';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { GlassCard } from '../components/ui/GlassCard';
import toast from 'react-hot-toast';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const isNameValid = name.length >= 2;
  const nameError = name.length > 0 && !isNameValid ? 'Le nom doit contenir au moins 2 caractères' : '';

  const isEmailValid = email.length > 0 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const emailError = email.length > 0 && !isEmailValid ? 'Email invalide' : '';

  const isPasswordValid = password.length >= 8;
  const passwordError = password.length > 0 && !isPasswordValid ? 'Le mot de passe doit contenir au moins 8 caractères' : '';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!isNameValid) {
      toast.error('Veuillez entrer un nom valide');
      return;
    }

    if (!isEmailValid) {
      toast.error('Veuillez entrer un email valide');
      return;
    }

    if (!isPasswordValid) {
      toast.error('Le mot de passe doit contenir au moins 8 caractères');
      return;
    }

    if (!acceptTerms) {
      toast.error('Veuillez accepter les conditions d\'utilisation');
      return;
    }

    setLoading(true);

    try {
      await register({ email, password, name });
      toast.success('Compte créé avec succès ! 🎉');
      navigate('/dashboard');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail;

      if (errorMessage?.includes('already registered') || errorMessage?.includes('already exists')) {
        toast.error('Un compte existe déjà avec cet email');
      } else if (errorMessage?.includes('email')) {
        toast.error('Email invalide ou déjà utilisé');
      } else if (errorMessage?.includes('password')) {
        toast.error('Mot de passe trop faible. Utilisez au moins 8 caractères.');
      } else {
        toast.error('Erreur lors de la création du compte. Veuillez réessayer.');
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
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 2
          }}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"
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
              Créer un compte
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.4 }}
              className="text-slate-400 font-medium"
            >
              Rejoignez des milliers de vendeurs qui automatisent leurs ventes
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
            {/* Full Name */}
            <Input
              label="Nom complet"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jean Dupont"
              icon={User}
              error={nameError}
              required
            />

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
            <div className="space-y-2">
              <Input
                label="Mot de passe"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                icon={Lock}
                error={passwordError}
                required
              />
              {/* Password strength indicator */}
              {password.length > 0 && (
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full ${
                        password.length >= 12
                          ? 'bg-green-500'
                          : password.length >= 8
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      initial={{ width: 0 }}
                      animate={{
                        width: password.length >= 12 ? '100%' : password.length >= 8 ? '66%' : '33%'
                      }}
                    />
                  </div>
                  <span className="text-xs text-slate-400">
                    {password.length >= 12 ? 'Fort' : password.length >= 8 ? 'Moyen' : 'Faible'}
                  </span>
                </div>
              )}
            </div>

            {/* Accept terms */}
            <label className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={acceptTerms}
                onChange={(e) => setAcceptTerms(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded border-2 border-violet-500/50 text-violet-600 focus:ring-2 focus:ring-violet-500 focus:ring-offset-0 cursor-pointer transition-all bg-white/5"
                required
              />
              <span className="text-sm text-slate-400 group-hover:text-white transition-colors">
                J'accepte les{' '}
                <a href="#" className="text-violet-400 hover:text-violet-300 font-medium underline">
                  conditions d'utilisation
                </a>{' '}
                et la{' '}
                <a href="#" className="text-violet-400 hover:text-violet-300 font-medium underline">
                  politique de confidentialité
                </a>
              </span>
            </label>

            {/* Submit button */}
            <Button
              type="submit"
              disabled={loading}
              loading={loading}
              icon={loading ? undefined : UserPlus}
              className="w-full"
              size="lg"
            >
              {loading ? 'Création en cours...' : 'Créer mon compte'}
            </Button>

            {/* Benefits */}
            <div className="mt-6 space-y-2">
              {[
                'Analyse IA gratuite de vos photos',
                'Publication automatisée sur Vinted',
                'Gestion multi-comptes',
              ].map((benefit, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 + index * 0.1 }}
                  className="flex items-center gap-2 text-sm text-slate-400"
                >
                  <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-500/20 flex items-center justify-center border border-green-500/30">
                    <Check className="w-3 h-3 text-green-400" />
                  </div>
                  <span>{benefit}</span>
                </motion.div>
              ))}
            </div>
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

          {/* Login link */}
          <div className="text-center">
            <p className="text-sm text-slate-400">
              Vous avez déjà un compte ?{' '}
              <Link
                to="/login"
                className="text-violet-400 hover:text-violet-300 font-semibold transition-colors inline-flex items-center gap-1 group"
              >
                Se connecter
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </p>
          </div>

          {/* Security badge */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="mt-6 pt-6 border-t border-white/10"
          >
            <div className="flex items-center justify-center gap-2 text-sm text-slate-400">
              <Shield className="w-4 h-4 text-green-400" />
              <span>Inscription sécurisée SSL • Données chiffrées</span>
            </div>
          </motion.div>
        </GlassCard>

        {/* Footer links */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.1 }}
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

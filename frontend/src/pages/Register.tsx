import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Mail, Lock, User, UserPlus, ArrowRight, Loader2, Shield, Sparkles, Check } from 'lucide-react';
import InputField from '../components/auth/InputField';
import PasswordStrength from '../components/auth/PasswordStrength';
import toast from 'react-hot-toast';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  // Validation states
  const isNameValid = name.length >= 2;
  const nameError = name.length > 0 && !isNameValid ? 'Le nom doit contenir au moins 2 caractères' : '';

  const isEmailValid = email.length > 0 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const emailError = email.length > 0 && !isEmailValid ? 'Email invalide' : '';

  const isPasswordValid = password.length >= 8;
  const passwordError = password.length > 0 && !isPasswordValid ? 'Le mot de passe doit contenir au moins 8 caractères' : '';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    // Validation
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

      // Better error messages
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
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-primary-50 via-white to-primary-100 flex items-center justify-center p-4">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-200/30 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-200/30 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-200/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      {/* Main card */}
      <div className="w-full max-w-md relative">
        <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-primary-500/10 p-8 border border-white/20">
          {/* Header with logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl mb-4 shadow-lg shadow-primary-500/30">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-primary-800 bg-clip-text text-transparent mb-2">
              Créer un compte
            </h1>
            <p className="text-gray-600 font-medium">
              Rejoignez des milliers de vendeurs qui automatisent leurs ventes
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Full Name */}
            <InputField
              label="Nom complet"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jean Dupont"
              icon={<User className="w-5 h-5" />}
              error={nameError}
              success={isNameValid}
              required
              autoComplete="name"
            />

            {/* Email */}
            <InputField
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="vous@exemple.com"
              icon={<Mail className="w-5 h-5" />}
              error={emailError}
              success={isEmailValid}
              required
              autoComplete="email"
            />

            {/* Password with strength indicator */}
            <div>
              <InputField
                label="Mot de passe"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                icon={<Lock className="w-5 h-5" />}
                error={passwordError}
                showPasswordToggle
                required
                autoComplete="new-password"
              />
              <PasswordStrength password={password} />
            </div>

            {/* Accept terms */}
            <label className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={acceptTerms}
                onChange={(e) => setAcceptTerms(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded border-2 border-gray-300 text-primary-600 focus:ring-2 focus:ring-primary-500 focus:ring-offset-0 cursor-pointer transition-all"
                required
              />
              <span className="text-sm text-gray-600 group-hover:text-gray-900 transition-colors">
                J'accepte les{' '}
                <a href="#" className="text-primary-600 hover:text-primary-700 font-medium underline">
                  conditions d'utilisation
                </a>{' '}
                et la{' '}
                <a href="#" className="text-primary-600 hover:text-primary-700 font-medium underline">
                  politique de confidentialité
                </a>
              </span>
            </label>

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="
                w-full py-3.5 px-6
                bg-gradient-to-r from-primary-600 to-primary-700
                hover:from-primary-700 hover:to-primary-800
                text-white font-semibold rounded-xl
                flex items-center justify-center gap-2
                transition-all duration-300
                shadow-lg shadow-primary-500/30
                hover:shadow-xl hover:shadow-primary-500/40
                hover:-translate-y-0.5
                disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0
                group
              "
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Création en cours...</span>
                </>
              ) : (
                <>
                  <UserPlus className="w-5 h-5 transition-transform group-hover:scale-110" />
                  <span>Créer mon compte</span>
                  <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
                </>
              )}
            </button>

            {/* Benefits */}
            <div className="mt-6 space-y-2">
              {[
                'Analyse IA gratuite de vos photos',
                'Publication automatisée sur Vinted',
                'Gestion multi-comptes',
              ].map((benefit, index) => (
                <div key={index} className="flex items-center gap-2 text-sm text-gray-600">
                  <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
                    <Check className="w-3 h-3 text-green-600" />
                  </div>
                  <span>{benefit}</span>
                </div>
              ))}
            </div>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white text-gray-500">ou</span>
            </div>
          </div>

          {/* Login link */}
          <div className="text-center">
            <p className="text-sm text-gray-600">
              Vous avez déjà un compte ?{' '}
              <Link
                to="/login"
                className="text-primary-600 hover:text-primary-700 font-semibold transition-colors inline-flex items-center gap-1 group"
              >
                Se connecter
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </p>
          </div>

          {/* Security badge */}
          <div className="mt-6 pt-6 border-t border-gray-100">
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <Shield className="w-4 h-4 text-green-600" />
              <span>Inscription sécurisée SSL • Données chiffrées</span>
            </div>
          </div>
        </div>

        {/* Footer links */}
        <div className="mt-6 text-center text-xs text-gray-500 space-x-4">
          <a href="#" className="hover:text-gray-700 transition-colors">Politique de confidentialité</a>
          <span>•</span>
          <a href="#" className="hover:text-gray-700 transition-colors">Conditions d'utilisation</a>
        </div>
      </div>
    </div>
  );
}

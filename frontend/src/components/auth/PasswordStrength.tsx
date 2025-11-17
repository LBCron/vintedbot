import { Check, X } from 'lucide-react';

interface PasswordStrengthProps {
  password: string;
}

export default function PasswordStrength({ password }: PasswordStrengthProps) {
  // Backend password requirements
  const requirements = [
    {
      test: (pwd: string) => pwd.length >= 12,
      text: 'Au moins 12 caractères'
    },
    {
      test: (pwd: string) => /[a-z]/.test(pwd),
      text: 'Une minuscule (a-z)'
    },
    {
      test: (pwd: string) => /[A-Z]/.test(pwd),
      text: 'Une majuscule (A-Z)'
    },
    {
      test: (pwd: string) => /[0-9]/.test(pwd),
      text: 'Un chiffre (0-9)'
    },
    {
      test: (pwd: string) => /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;'`~]/.test(pwd),
      text: 'Un caractère spécial (!@#$%...)'
    },
  ];

  const getStrength = (pwd: string): { level: number; text: string; color: string } => {
    if (!pwd) return { level: 0, text: '', color: '' };

    const passedCount = requirements.filter(req => req.test(pwd)).length;
    const percentage = (passedCount / requirements.length) * 100;

    if (percentage < 40) return { level: 1, text: 'Faible', color: 'bg-red-500' };
    if (percentage < 80) return { level: 2, text: 'Moyen', color: 'bg-yellow-500' };
    return { level: 3, text: 'Fort', color: 'bg-green-500' };
  };

  const strength = getStrength(password);
  const allRequirementsMet = requirements.every(req => req.test(password));

  if (!password) return null;

  return (
    <div className="mt-3 space-y-3">
      {/* Progress bar */}
      <div className="flex gap-2">
        {[1, 2, 3].map((level) => (
          <div
            key={level}
            className={`
              h-2 flex-1 rounded-full transition-all duration-300
              ${level <= strength.level ? strength.color : 'bg-gray-200'}
            `}
          />
        ))}
      </div>

      {/* Strength text */}
      <div className="flex items-center justify-between text-sm">
        <span className={`font-medium ${
          strength.level === 1 ? 'text-red-600' :
          strength.level === 2 ? 'text-yellow-600' :
          'text-green-600'
        }`}>
          Force : {strength.text}
        </span>
        {allRequirementsMet && (
          <span className="text-xs text-green-600 font-medium">
            ✓ Tous les critères sont remplis
          </span>
        )}
      </div>

      {/* Requirements checklist */}
      <div className="space-y-1.5 text-xs">
        {requirements.map((req, index) => {
          const passed = req.test(password);
          return (
            <div
              key={index}
              className={`flex items-center gap-2 transition-colors ${
                passed ? 'text-green-600' : 'text-gray-500'
              }`}
            >
              <div className={`flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center ${
                passed ? 'bg-green-100' : 'bg-gray-100'
              }`}>
                {passed ? (
                  <Check className="w-3 h-3" />
                ) : (
                  <X className="w-3 h-3" />
                )}
              </div>
              <span>{req.text}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

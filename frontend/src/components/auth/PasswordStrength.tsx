interface PasswordStrengthProps {
  password: string;
}

export default function PasswordStrength({ password }: PasswordStrengthProps) {
  const getStrength = (pwd: string): { level: number; text: string; color: string } => {
    if (!pwd) return { level: 0, text: '', color: '' };

    let strength = 0;

    // Length check
    if (pwd.length >= 8) strength++;
    if (pwd.length >= 12) strength++;

    // Character variety
    if (/[a-z]/.test(pwd)) strength++;
    if (/[A-Z]/.test(pwd)) strength++;
    if (/[0-9]/.test(pwd)) strength++;
    if (/[^a-zA-Z0-9]/.test(pwd)) strength++;

    // Map strength to level
    if (strength <= 2) return { level: 1, text: 'Faible', color: 'bg-red-500' };
    if (strength <= 4) return { level: 2, text: 'Moyen', color: 'bg-yellow-500' };
    return { level: 3, text: 'Fort', color: 'bg-green-500' };
  };

  const strength = getStrength(password);

  if (!password) return null;

  return (
    <div className="mt-3 space-y-2">
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

      {/* Text indicator */}
      <div className="flex items-center justify-between text-sm">
        <span className={`font-medium ${
          strength.level === 1 ? 'text-red-600' :
          strength.level === 2 ? 'text-yellow-600' :
          'text-green-600'
        }`}>
          Force du mot de passe : {strength.text}
        </span>

        {strength.level < 3 && (
          <span className="text-xs text-gray-500">
            {password.length < 8 ? '8+ caractères' :
             !/[A-Z]/.test(password) ? 'Ajouter une majuscule' :
             !/[0-9]/.test(password) ? 'Ajouter un chiffre' :
             'Ajouter un symbole'}
          </span>
        )}
      </div>
    </div>
  );
}

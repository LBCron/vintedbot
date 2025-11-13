import { InputHTMLAttributes, ReactNode, useState } from 'react';
import { Eye, EyeOff, Check, X, AlertCircle } from 'lucide-react';

interface InputFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon?: ReactNode;
  error?: string;
  success?: boolean;
  helperText?: string;
  showPasswordToggle?: boolean;
}

export default function InputField({
  label,
  icon,
  error,
  success,
  helperText,
  showPasswordToggle = false,
  type = 'text',
  className = '',
  ...props
}: InputFieldProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const inputType = showPasswordToggle && showPassword ? 'text' : type;

  return (
    <div className="input-group">
      <label className="block text-sm font-semibold text-gray-700 mb-2">
        {label}
      </label>

      <div className="relative">
        {/* Icon à gauche */}
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
            {icon}
          </div>
        )}

        {/* Input */}
        <input
          type={inputType}
          className={`
            w-full px-4 py-3
            ${icon ? 'pl-11' : 'pl-4'}
            ${showPasswordToggle || success || error ? 'pr-11' : 'pr-4'}
            border-2 rounded-xl
            transition-all duration-300 ease-in-out
            placeholder:text-gray-400 placeholder:opacity-60
            focus:outline-none focus:ring-0
            ${error
              ? 'border-red-300 bg-red-50 focus:border-red-500 focus:bg-red-50/50'
              : success
              ? 'border-green-300 bg-green-50 focus:border-green-500 focus:bg-green-50/50'
              : isFocused
              ? 'border-primary-500 bg-white shadow-lg shadow-primary-100'
              : 'border-gray-200 bg-white hover:border-gray-300'
            }
            ${className}
          `}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          {...props}
        />

        {/* Icons à droite */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
          {/* Validation icons */}
          {success && !showPasswordToggle && (
            <Check className="w-5 h-5 text-green-500" />
          )}
          {error && !showPasswordToggle && (
            <AlertCircle className="w-5 h-5 text-red-500" />
          )}

          {/* Password toggle */}
          {showPasswordToggle && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              tabIndex={-1}
            >
              {showPassword ? (
                <EyeOff className="w-5 h-5" />
              ) : (
                <Eye className="w-5 h-5" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Helper text / Error message */}
      {(error || helperText) && (
        <div className={`mt-2 flex items-start gap-1.5 text-sm ${error ? 'text-red-600' : 'text-gray-500'}`}>
          {error && <X className="w-4 h-4 mt-0.5 flex-shrink-0" />}
          <span>{error || helperText}</span>
        </div>
      )}
    </div>
  );
}

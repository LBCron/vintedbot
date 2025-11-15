/**
 * i18next Configuration for VintedBot
 *
 * Multilingual support: FR (default) / EN
 */
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import translationFR from './locales/fr.json';
import translationEN from './locales/en.json';

const resources = {
  fr: {
    translation: translationFR
  },
  en: {
    translation: translationEN
  }
};

i18n
  .use(LanguageDetector) // Detect user language
  .use(initReactI18next) // Pass i18n to React
  .init({
    resources,
    fallbackLng: 'fr',
    defaultNS: 'translation',

    detection: {
      // Order of language detection
      order: ['localStorage', 'navigator', 'htmlTag'],
      // Cache user language preference
      caches: ['localStorage'],
      lookupLocalStorage: 'vintedbot_language'
    },

    interpolation: {
      escapeValue: false // React already escapes
    },

    react: {
      useSuspense: true
    }
  });

export default i18n;

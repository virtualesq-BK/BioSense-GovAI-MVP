'use client';

import { Button } from '@/components/ui/button';
import { useLanguage } from '@/lib/i18n/language-provider';

export function LanguageToggle() {
  const { locale, setLocale, t } = useLanguage();

  return (
    <Button
      variant="ghost"
      size="sm"
      aria-label={t('common.languageToggle')}
      onClick={() => setLocale(locale === 'ko' ? 'en' : 'ko')}
      className="font-semibold"
    >
      {locale === 'ko' ? 'EN' : '한국어'}
    </Button>
  );
}

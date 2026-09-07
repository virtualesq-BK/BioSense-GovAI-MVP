'use client';

import Link from 'next/link';
import {
  Activity,
  ArrowRight,
  BarChart3,
  Database,
  FileSearch,
  Shield,
  Sparkles
} from 'lucide-react';
import { ThemeToggle } from '@/components/layout/theme-toggle';
import { LanguageToggle } from '@/components/layout/language-toggle';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/lib/i18n/language-provider';
import type { TranslationKey } from '@/lib/i18n/dictionary';

const FEATURES: { icon: typeof Sparkles; titleKey: TranslationKey; descriptionKey: TranslationKey }[] = [
  { icon: Sparkles, titleKey: 'landing.feature1.title', descriptionKey: 'landing.feature1.description' },
  { icon: Database, titleKey: 'landing.feature2.title', descriptionKey: 'landing.feature2.description' },
  { icon: FileSearch, titleKey: 'landing.feature3.title', descriptionKey: 'landing.feature3.description' },
  { icon: BarChart3, titleKey: 'landing.feature4.title', descriptionKey: 'landing.feature4.description' },
  { icon: Shield, titleKey: 'landing.feature5.title', descriptionKey: 'landing.feature5.description' },
  { icon: Activity, titleKey: 'landing.feature6.title', descriptionKey: 'landing.feature6.description' }
];

const CONCEPT_DIAGRAMS: { src: string; titleKey: TranslationKey; descriptionKey: TranslationKey }[] = [
  {
    src: '/diagrams/biosensor-signal-pipeline.svg',
    titleKey: 'landing.diagrams.signalPipeline.title',
    descriptionKey: 'landing.diagrams.signalPipeline.description'
  },
  {
    src: '/diagrams/multi-omics-biomarker.svg',
    titleKey: 'landing.diagrams.multiOmics.title',
    descriptionKey: 'landing.diagrams.multiOmics.description'
  },
  {
    src: '/diagrams/liquid-biopsy-lab-on-chip.svg',
    titleKey: 'landing.diagrams.labOnChip.title',
    descriptionKey: 'landing.diagrams.labOnChip.description'
  },
  {
    src: '/diagrams/biosensor-workflow.svg',
    titleKey: 'landing.diagrams.workflow.title',
    descriptionKey: 'landing.diagrams.workflow.description'
  }
];

const WORKFLOW_STEPS: { step: string; titleKey: TranslationKey; descriptionKey: TranslationKey }[] = [
  { step: '01', titleKey: 'landing.workflow.step1.title', descriptionKey: 'landing.workflow.step1.description' },
  { step: '02', titleKey: 'landing.workflow.step2.title', descriptionKey: 'landing.workflow.step2.description' },
  { step: '03', titleKey: 'landing.workflow.step3.title', descriptionKey: 'landing.workflow.step3.description' }
];

export default function LandingPage() {
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-[var(--background)]">
      <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--background)]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 lg:px-8">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <Activity className="h-5 w-5 text-[var(--accent)]" />
            BioSense-GovAI
          </Link>
          <nav className="hidden items-center gap-6 text-sm text-[var(--muted-foreground)] md:flex">
            <a href="#features" className="hover:text-[var(--foreground)]">
              {t('landing.nav.features')}
            </a>
            <a href="#diagrams" className="hover:text-[var(--foreground)]">
              {t('landing.diagrams.title')}
            </a>
            <a href="#workflow" className="hover:text-[var(--foreground)]">
              {t('landing.nav.workflow')}
            </a>
            <Link href="/sign-in" className="hover:text-[var(--foreground)]">
              {t('landing.nav.signIn')}
            </Link>
            <Link href="/dashboard" className="hover:text-[var(--foreground)]">
              {t('landing.nav.dashboard')}
            </Link>
          </nav>
          <div className="flex items-center gap-2">
            <LanguageToggle />
            <ThemeToggle />
            <Link href="/dashboard">
              <Button size="sm">{t('landing.getStarted')}</Button>
            </Link>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-20 lg:px-8 lg:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <span className="inline-flex items-center rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-600 dark:text-cyan-300">
            {t('landing.hero.badge')}
          </span>
          <h1 className="mt-6 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            {t('landing.hero.title1')}
            <span className="block text-[var(--accent)]">{t('landing.hero.title2')}</span>
          </h1>
          <p className="mt-6 text-lg text-[var(--muted-foreground)]">{t('landing.hero.description')}</p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link href="/recommendations">
              <Button size="lg" className="gap-2">
                {t('landing.hero.generate')}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline">
                {t('landing.hero.viewDashboard')}
              </Button>
            </Link>
          </div>
          <p className="mt-6 text-xs text-[var(--muted-foreground)]">{t('landing.hero.audience')}</p>
        </div>
      </section>

      <section id="features" className="border-y border-[var(--border)] bg-[var(--muted)]/40 py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-8">
          <h2 className="text-center text-2xl font-bold sm:text-3xl">{t('landing.features.title')}</h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-[var(--muted-foreground)]">
            {t('landing.features.description')}
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ icon: Icon, titleKey, descriptionKey }) => (
              <div
                key={titleKey}
                className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="mb-4 inline-flex rounded-lg bg-[var(--muted)] p-2.5">
                  <Icon className="h-5 w-5 text-[var(--accent)]" />
                </div>
                <h3 className="font-semibold">{t(titleKey)}</h3>
                <p className="mt-2 text-sm text-[var(--muted-foreground)]">{t(descriptionKey)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="diagrams" className="py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-8">
          <h2 className="text-center text-2xl font-bold sm:text-3xl">{t('landing.diagrams.title')}</h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-[var(--muted-foreground)]">
            {t('landing.diagrams.description')}
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2">
            {CONCEPT_DIAGRAMS.map(({ src, titleKey, descriptionKey }) => (
              <figure
                key={src}
                className="overflow-hidden rounded-xl border border-[var(--border)] bg-white shadow-sm"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={src} alt={t(titleKey)} className="aspect-[16/9] w-full object-contain p-4" />
                <figcaption className="border-t border-[var(--border)] bg-[var(--card)] p-4">
                  <p className="font-semibold">{t(titleKey)}</p>
                  <p className="mt-1 text-sm text-[var(--muted-foreground)]">{t(descriptionKey)}</p>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      <section id="workflow" className="py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-8">
          <h2 className="text-center text-2xl font-bold sm:text-3xl">{t('landing.workflow.title')}</h2>
          <ol className="mx-auto mt-12 grid max-w-4xl gap-6 sm:grid-cols-3">
            {WORKFLOW_STEPS.map((item) => (
              <li
                key={item.step}
                className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 text-center"
              >
                <span className="text-3xl font-bold text-[var(--accent)]">{item.step}</span>
                <h3 className="mt-3 font-semibold">{t(item.titleKey)}</h3>
                <p className="mt-2 text-sm text-[var(--muted-foreground)]">{t(item.descriptionKey)}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <footer className="border-t border-[var(--border)] py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 text-sm text-[var(--muted-foreground)] sm:flex-row lg:px-8">
          <p>© {new Date().getFullYear()} BioSense-GovAI</p>
          <div className="flex gap-4">
            <Link href="/admin" className="hover:text-[var(--foreground)]">
              {t('landing.footer.admin')}
            </Link>
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/docs`}
              target="_blank"
              rel="noreferrer"
              className="hover:text-[var(--foreground)]"
            >
              {t('landing.footer.apiDocs')}
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

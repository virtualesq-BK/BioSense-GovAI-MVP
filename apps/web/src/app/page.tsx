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
import { Button } from '@/components/ui/button';

const features = [
  {
    icon: Sparkles,
    title: '하이브리드 추천 엔진',
    description: '지식 그래프 + RAG 문헌 + 공공 보건 데이터를 결합한 센서 전략 추천'
  },
  {
    icon: Database,
    title: '한국 공공 데이터',
    description: 'KOSIS·KDCA 암 발생률·사망률을 지역별로 통합 분석'
  },
  {
    icon: FileSearch,
    title: '과학 문헌 RAG',
    description: 'PDF 파싱, 벡터 검색, 인용 기반 근거 제시'
  },
  {
    icon: BarChart3,
    title: '성능 지표 예측',
    description: '민감도·특이도·LOD·비용·실험 프로토콜 자동 출력'
  },
  {
    icon: Shield,
    title: '신뢰도 스코어링',
    description: '가중 랭킹과 confidence score로 추천 품질 정량화'
  },
  {
    icon: Activity,
    title: '실시간 모니터링',
    description: '데이터 수집 파이프라인·문헌 인덱싱 상태 대시보드'
  }
];

export default function LandingPage() {
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
              기능
            </a>
            <a href="#workflow" className="hover:text-[var(--foreground)]">
              워크플로
            </a>
            <Link href="/sign-in" className="hover:text-[var(--foreground)]">
              로그인
            </Link>
            <Link href="/dashboard" className="hover:text-[var(--foreground)]">
              대시보드
            </Link>
          </nav>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Link href="/dashboard">
              <Button size="sm">시작하기</Button>
            </Link>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-20 lg:px-8 lg:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <span className="inline-flex items-center rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-600 dark:text-cyan-300">
            ctDNA · 바이오센서 공동 설계 SaaS
          </span>
          <h1 className="mt-6 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            AI 기반 바이오마커–바이오센서
            <span className="block text-[var(--accent)]">조기 암 진단 플랫폼</span>
          </h1>
          <p className="mt-6 text-lg text-[var(--muted-foreground)]">
            ctDNA 분자 특성과 한국 공공 보건 데이터, 과학 문헌을 결합하여
            최적의 바이오센서 전략을 추천하고 리포트로보냅니다.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link href="/recommendations">
              <Button size="lg" className="gap-2">
                추천 생성하기
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline">
                대시보드 보기
              </Button>
            </Link>
          </div>
          <p className="mt-6 text-xs text-[var(--muted-foreground)]">
            대상: 바이오센서 스타트업 · 대학 연구자 · 진단 기업
          </p>
        </div>
      </section>

      <section id="features" className="border-y border-[var(--border)] bg-[var(--muted)]/40 py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-8">
          <h2 className="text-center text-2xl font-bold sm:text-3xl">핵심 기능</h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-[var(--muted-foreground)]">
            연구부터 프로토타입까지, 데이터 기반 의사결정을 지원합니다.
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, description }) => (
              <div
                key={title}
                className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="mb-4 inline-flex rounded-lg bg-[var(--muted)] p-2.5">
                  <Icon className="h-5 w-5 text-[var(--accent)]" />
                </div>
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-[var(--muted-foreground)]">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="workflow" className="py-20">
        <div className="mx-auto max-w-6xl px-4 lg:px-8">
          <h2 className="text-center text-2xl font-bold sm:text-3xl">워크플로</h2>
          <ol className="mx-auto mt-12 grid max-w-4xl gap-6 sm:grid-cols-3">
            {[
              { step: '01', title: '케이스 입력', desc: '암종·ctDNA·지역·바이오마커 조건 설정' },
              { step: '02', title: 'AI 추천', desc: '하이브리드 검색으로 센서 전략 Top-K 생성' },
              { step: '03', title: '리포트', desc: 'PDF보내기 및 팀 공유' }
            ].map((item) => (
              <li
                key={item.step}
                className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 text-center"
              >
                <span className="text-3xl font-bold text-[var(--accent)]">{item.step}</span>
                <h3 className="mt-3 font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm text-[var(--muted-foreground)]">{item.desc}</p>
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
              관리
            </Link>
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/docs`}
              target="_blank"
              rel="noreferrer"
              className="hover:text-[var(--foreground)]"
            >
              API 문서
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

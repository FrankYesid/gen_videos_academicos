import { Routes, Route, Link, NavLink } from 'react-router-dom';
import {
  HomeIcon,
  ArrowUpTrayIcon,
  BeakerIcon,
  DocumentTextIcon,
  VideoCameraIcon,
  AcademicCapIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { CurrentCourseProvider, useCurrentCourse } from './contexts/CurrentCourseContext';
import WorkflowStepper from './components/WorkflowStepper';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import Analysis from './pages/Analysis';
import ScriptPage from './pages/Script';
import Video from './pages/Video';
import Pedagogical from './pages/Pedagogical';
import QA from './pages/QA';

const navItems = [
  { to: '/', label: 'Dashboard', icon: HomeIcon, end: true },
  { to: '/upload', label: 'Subir PDF', icon: ArrowUpTrayIcon },
  { to: '/analysis', label: 'Análisis', icon: BeakerIcon },
  { to: '/pedagogical', label: 'Pedagógico', icon: AcademicCapIcon },
  { to: '/script', label: 'Guion', icon: DocumentTextIcon },
  { to: '/qa', label: 'QA', icon: ShieldCheckIcon },
  { to: '/video', label: 'Video', icon: VideoCameraIcon },
];

function Shell() {
  const { getRouteForStep, currentCourseId, clearCurrentCourse } = useCurrentCourse();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4 flex-wrap">
          <Link to="/" className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lg shrink-0">
              <VideoCameraIcon className="w-5 h-5 text-white" />
            </div>
            <div className="min-w-0">
              <h1 className="text-lg font-bold text-slate-900 leading-tight truncate">
                AI Course Video Generator
              </h1>
              <p className="text-xs text-slate-500 leading-tight truncate">
                Transforma PDFs en videos educativos
              </p>
            </div>
          </Link>
          <div className="flex items-center gap-2 flex-wrap">
            {currentCourseId && (
              <button
                type="button"
                onClick={clearCurrentCourse}
                className="btn-secondary btn-sm"
                title="Cambia el curso activo actualmente seleccionado para navegar en el workflow"
              >
                ✨ Curso activo: <span className="font-mono text-xs">{currentCourseId.slice(0, 8)}…</span>
              </button>
            )}
            <span className="badge bg-brand-100 text-brand-700">v0.7.0 — WORKFLOW UI</span>
          </div>
        </div>
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <ul className="flex gap-1 overflow-x-auto pb-2">
            {navItems.map(({ to, label, icon: Icon, end }) => {
              const finalTo = end ? to : getRouteForStep(label === 'Subir PDF' ? 'upload' : label === 'Análisis' ? 'analysis' : label === 'Pedagógico' ? 'pedagogical' : label === 'Guion' ? 'script' : label === 'QA' ? 'qa' : label === 'Video' ? 'video' : 'upload');
              return (
                <li key={to} className="shrink-0">
                  <NavLink
                    to={finalTo}
                    end={end}
                    className={({ isActive }) =>
                      `inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                        isActive
                          ? 'bg-brand-100 text-brand-700 shadow-sm'
                          : 'text-slate-600 hover:bg-slate-100'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span className="whitespace-nowrap">{label}</span>
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <WorkflowStepper />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/analysis/:id?" element={<Analysis />} />
          <Route path="/pedagogical/:id?" element={<Pedagogical />} />
          <Route path="/script/:id?" element={<ScriptPage />} />
          <Route path="/qa/:id?" element={<QA />} />
          <Route path="/video/:id?" element={<Video />} />
        </Routes>
      </main>

      <footer className="bg-white border-t border-slate-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-xs text-slate-500 text-center">
          AI Course Video Generator ·{' '}
          <Link
            to="https://github.com"
            className="hover:text-brand-600 underline"
          >
            Repositorio
          </Link>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <CurrentCourseProvider>
      <Shell />
    </CurrentCourseProvider>
  );
}

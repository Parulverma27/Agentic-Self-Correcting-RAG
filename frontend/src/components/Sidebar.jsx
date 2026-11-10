import React from 'react';
import {
  LayoutDashboard,
  FileText,
  FileQuestion,
  Database,
  SlidersHorizontal,
  PlayCircle,
  BarChart2,
  Terminal,
  FileCheck,
  Settings,
  FlaskConical,
  GraduationCap
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'documents', label: 'Documents', icon: FileText },
    { id: 'docqa', label: 'Doc Q&A', icon: FileQuestion },
    { id: 'datasets', label: 'Datasets', icon: Database },
    { id: 'strategies', label: 'Grading Strategies', icon: SlidersHorizontal },
    { id: 'evaluation', label: 'Evaluation', icon: PlayCircle },
    { id: 'results', label: 'Results', icon: BarChart2 },
    { id: 'demo', label: 'Demo', icon: Terminal },
    { id: 'reports', label: 'Reports', icon: FileCheck },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="sidebar">
      <div>
        {/* Brand Logo Header */}
        <div className="sidebar-logo-area">
          <div className="logo-icon-box">
            <FlaskConical size={20} strokeWidth={2.4} />
          </div>
          <div>
            <div className="logo-text-title">RAGLab</div>
            <div className="logo-text-subtitle">Comparative Analysis</div>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <Icon size={17} strokeWidth={isActive ? 2.2 : 1.9} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Project Card at Bottom */}
      <div className="sidebar-project-card">
        <div className="sidebar-project-label">
          <GraduationCap size={14} />
          <span>Research Project</span>
        </div>
        <p className="sidebar-project-desc">
          Comparative Evaluation of Relevance-Grading Strategies in Corrective RAG Systems
        </p>
      </div>
    </aside>
  );
}

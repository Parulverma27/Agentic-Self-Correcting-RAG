import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import AcademicBanner from './components/AcademicBanner';

import DashboardView from './views/DashboardView';
import DocumentsView from './views/DocumentsView';
import StrategiesView from './views/StrategiesView';
import EvaluationView from './views/EvaluationView';
import GoldLabelsView from './views/GoldLabelsView';
import ResultsView from './views/ResultsView';
import DemoView from './views/DemoView';
import ReportsView from './views/ReportsView';
import SettingsView from './views/SettingsView';
import DocQAView from './views/DocQAView';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [notificationMsg, setNotificationMsg] = useState(null);

  const handleNotificationClick = () => {
    setNotificationMsg('All 3 relevance-grading models initialized and benchmark ready.');
    setTimeout(() => setNotificationMsg(null), 3500);
  };

  const renderActiveView = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardView onNavigate={(tab) => setActiveTab(tab)} />;
      case 'documents':
        return <DocumentsView onNavigateToDataset={() => setActiveTab('datasets')} />;
      case 'docqa':
        return <DocQAView />;
      case 'datasets':
        return <GoldLabelsView />;
      case 'strategies':
        return <StrategiesView />;
      case 'evaluation':
        return <EvaluationView onComplete={() => setActiveTab('results')} />;
      case 'results':
        return <ResultsView />;
      case 'demo':
        return <DemoView />;
      case 'reports':
        return <ReportsView />;
      case 'settings':
        return <SettingsView />;
      default:
        return <DashboardView onNavigate={(tab) => setActiveTab(tab)} />;
    }
  };

  return (
    <div className="app-layout">
      {/* Sidebar Navigation */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Workspace */}
      <div className="main-wrapper">
        <Header
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onNotificationClick={handleNotificationClick}
        />

        {/* Floating notification toast if bell clicked */}
        {notificationMsg && (
          <div
            style={{
              position: 'fixed',
              top: '74px',
              right: '32px',
              background: '#0f172a',
              color: '#ffffff',
              padding: '12px 18px',
              borderRadius: '10px',
              boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)',
              fontSize: '13px',
              zIndex: 100,
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }} />
            <span>{notificationMsg}</span>
          </div>
        )}

        <main className="content-area">
          {renderActiveView()}

          {/* Academic Banner Footer */}
          <AcademicBanner />
        </main>
      </div>
    </div>
  );
}

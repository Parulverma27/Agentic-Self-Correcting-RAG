import React, { useState } from 'react';
import { Check, Settings, Sliders, Bell, Palette } from 'lucide-react';

export default function SettingsView() {
  const [activeSubNav, setActiveSubNav] = useState('General');
  const [projectName, setProjectName] = useState('RAG Comparative Study');
  const [defaultDomain, setDefaultDomain] = useState('HotpotQA');
  const [resultsPerPage, setResultsPerPage] = useState('10');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const subNavs = [
    { id: 'General', label: 'General', icon: Settings },
    { id: 'Evaluation', label: 'Evaluation', icon: Sliders },
    { id: 'Notifications', label: 'Notifications', icon: Bell },
    { id: 'Appearance', label: 'Appearance', icon: Palette }
  ];

  const handleSave = (e) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="settings-view">
      {/* Header */}
      <div className="section-header">
        <h2 className="section-title">Settings</h2>
        <p className="section-subtitle">
          Customize your project preferences.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: '24px' }}>
        {/* Settings Left Subnav */}
        <div className="card-panel" style={{ padding: '12px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {subNavs.map((item) => {
              const Icon = item.icon;
              const isActive = activeSubNav === item.id;
              return (
                <button
                  key={item.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '9px 12px',
                    borderRadius: '8px',
                    border: 'none',
                    background: isActive ? '#eff6ff' : 'transparent',
                    color: isActive ? '#2563eb' : '#64748b',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: '13px',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                  onClick={() => setActiveSubNav(item.id)}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Settings Form Panel */}
        <div className="card-panel">
          <h3 className="card-heading" style={{ marginBottom: '18px' }}>
            {activeSubNav} Settings
          </h3>

          <form onSubmit={handleSave} style={{ maxWidth: '480px' }}>
            <div className="form-group">
              <label className="form-label">Project Name</label>
              <input
                id="setting-project-name"
                type="text"
                className="form-control"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Default Domain</label>
              <select
                id="setting-default-domain"
                className="form-control"
                value={defaultDomain}
                onChange={(e) => setDefaultDomain(e.target.value)}
              >
                <option value="HotpotQA">HotpotQA</option>
                <option value="BioASQ">BioASQ</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Results Per Page</label>
              <input
                id="setting-results-per-page"
                type="number"
                className="form-control"
                value={resultsPerPage}
                onChange={(e) => setResultsPerPage(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginTop: '24px' }}>
              <button id="btn-save-settings" type="submit" className="btn-primary">
                Save Changes
              </button>
              {savedSuccess && (
                <span style={{ fontSize: '13px', color: '#16a34a', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Check size={16} /> Saved!
                </span>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

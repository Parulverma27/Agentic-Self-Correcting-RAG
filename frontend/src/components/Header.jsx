import React from 'react';
import { Search, Bell } from 'lucide-react';

export default function Header({ searchQuery, setSearchQuery, onNotificationClick }) {
  return (
    <header className="top-header">
      {/* Global Search */}
      <div className="search-container">
        <Search size={17} color="#94a3b8" />
        <input
          id="global-search-input"
          type="text"
          className="search-input"
          placeholder="Search anything..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Header Actions */}
      <div className="header-actions">
        <button
          id="btn-notifications"
          className="header-icon-btn"
          title="Notifications"
          onClick={onNotificationClick}
        >
          <Bell size={18} />
          <span className="notification-dot"></span>
        </button>

        {/* User Profile Widget */}
        <div className="user-profile-widget" id="user-profile-trigger">
          <img
            src="/assets/researcher-avatar.jpg"
            alt="Researcher"
            className="avatar-img"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              e.currentTarget.nextElementSibling.style.display = 'flex';
            }}
          />
          <div className="avatar-fallback" style={{ display: 'none' }}>
            R
          </div>
          <div className="profile-info">
            <span className="profile-name">Researcher</span>
            <span className="profile-subtitle">Final Year Project</span>
          </div>
        </div>
      </div>
    </header>
  );
}

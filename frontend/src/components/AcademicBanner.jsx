import React from 'react';
import { GraduationCap } from 'lucide-react';

export default function AcademicBanner() {
  return (
    <div className="academic-banner" id="academic-project-banner">
      <div className="banner-left">
        <div className="banner-cap-icon">
          <GraduationCap size={26} strokeWidth={2.2} />
        </div>
        <div>
          <h4 className="banner-headline">Research • Analyze • Build Better RAG</h4>
          <p className="banner-subtext">
            Comparative Evaluation of Relevance-Grading Strategies in Corrective RAG Systems
          </p>
        </div>
      </div>

      <div className="banner-tag">
        B.Tech CSE (AI/ML) | Final Year Project
      </div>
    </div>
  );
}

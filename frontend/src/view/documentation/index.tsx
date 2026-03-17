import React from 'react';
import { MarkdownPage } from '../oceansound/components/MarkdownPage';

/**
 * Documentation Page
 *
 * Content is loaded from: public/content/aplose/documentation.md
 * Edit that markdown file to update this page's content.
 */
export const DocumentationPage: React.FC = () => {
  return (
    <div style={{ height: '100%', overflowY: 'auto' }}>
      <MarkdownPage contentPath="/content/aplose/documentation.md" />
    </div>
  );
};

export default DocumentationPage;

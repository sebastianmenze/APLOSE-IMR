import React from 'react';
import { MarkdownPage } from '../components/MarkdownPage';

/**
 * About Page
 *
 * Content is loaded from: public/content/oceansound/about.md
 * Edit that markdown file to update this page's content.
 */
export const About: React.FC = () => {
  return <MarkdownPage contentPath="/content/oceansound/about.md" />;
};

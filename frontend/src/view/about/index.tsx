import React from 'react';
import { MarkdownPage } from '@/view/oceansound/components/MarkdownPage';

/**
 * About Page (APLOSE)
 *
 * Content is loaded from: public/content/aplose/about.md
 * Edit that markdown file to update this page's content.
 */
export const AboutPage: React.FC = () => {
  return <MarkdownPage contentPath="/content/aplose/about.md" />;
};

export default AboutPage;

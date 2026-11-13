import { makeFetchResponseErrorMessage } from '@/common_defs/helper_functions';

// Shared helpers for reading the project-level metadata and reflecting it in the
// page header (the three lines under "apqaui app") and the document title. Used
// by the header populator (on page load) and the project settings modal (after a
// successful save), so the header stays in sync in both the Vite dev server and
// the backend-served bundle without a full page reload.

export async function fetchProjectInfo() {
  const response = await fetch('/qc/project');
  if (!response.ok) {
    throw new Error(await makeFetchResponseErrorMessage(response));
  }
  return response.json();
}

function setText(selector, value) {
  const el = document.querySelector(selector);
  if (el) el.textContent = value;
}

export function applyProjectHeaderInfo(payload) {
  const project = payload.project || {};
  const name = (project.name || '').trim();
  const comment = project.comment || '';

  setText('.apqaui-html-page-project-path', payload.path || '');
  setText('.apqaui-html-page-project-name', `Project name: ${name}`);
  setText('.apqaui-html-page-project-comment', `Description: ${comment}`);

  document.title = name ? `QC rules for ${name}` : 'QC rules';
}

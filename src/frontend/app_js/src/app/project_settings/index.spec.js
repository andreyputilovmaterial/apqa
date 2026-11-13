import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

import ProjectSettingsModal from './index.js';
import { applyProjectHeaderInfo } from './project_header.js';

function stubFetch(getProject, putProject) {
  vi.stubGlobal(
    'fetch',
    vi.fn((url, options = {}) => {
      if (options.method === 'PUT') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(putProject),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve(getProject) });
    }),
  );
}

function seedHeaderDom() {
  document.body.innerHTML = `
    <div class="apqaui-html-page-project-path"></div>
    <div class="apqaui-html-page-project-name"></div>
    <div class="apqaui-html-page-project-comment"></div>
  `;
}

describe('applyProjectHeaderInfo', () => {
  beforeEach(() => {
    seedHeaderDom();
  });

  afterEach(() => {
    document.body.innerHTML = '';
    document.title = '';
  });

  it('writes the path, name and description into the header and the title', () => {
    applyProjectHeaderInfo({
      path: '/tmp/projects.yaml',
      project: { name: 'Wave 69', comment: 'Brand health' },
    });

    expect(document.querySelector('.apqaui-html-page-project-path').textContent).toBe('/tmp/projects.yaml');
    expect(document.querySelector('.apqaui-html-page-project-name').textContent).toBe('Project name: Wave 69');
    expect(document.querySelector('.apqaui-html-page-project-comment').textContent).toBe('Description: Brand health');
    expect(document.title).toBe('QC rules for Wave 69');
  });

  it('falls back to a plain title when the project has no name', () => {
    applyProjectHeaderInfo({ path: '/tmp/projects.yaml', project: { name: '', comment: '' } });

    expect(document.querySelector('.apqaui-html-page-project-name').textContent).toBe('Project name: ');
    expect(document.title).toBe('QC rules');
  });
});

describe('ProjectSettingsModal', () => {
  beforeEach(() => {
    seedHeaderDom();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    document.body.innerHTML = '';
    document.title = '';
  });

  it('loads the current project and updates the header in place on save without reloading', async () => {
    let current = { project: { name: 'Wave 69', comment: 'Before' }, path: '/tmp/projects.yaml' };
    vi.stubGlobal(
      'fetch',
      vi.fn((url, options = {}) => {
        if (options.method === 'PUT') {
          const body = JSON.parse(options.body);
          current = {
            project: { name: body.name, comment: body.comment },
            path: '/tmp/projects.yaml',
          };
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve(current) });
      }),
    );

    const resolve = vi.fn();
    const reject = vi.fn();
    const wrapper = mount(ProjectSettingsModal, { props: { resolve, reject } });
    await flushPromises();

    expect(wrapper.find('input.apqa-project-settings-form-input').element.value).toBe('Wave 69');
    expect(wrapper.find('textarea.apqa-project-settings-form-input').element.value).toBe('Before');

    await wrapper.find('input.apqa-project-settings-form-input').setValue('Wave 70');
    await wrapper.find('textarea.apqa-project-settings-form-input').setValue('After');
    await wrapper.find('form').trigger('submit');
    await flushPromises();

    expect(resolve).toHaveBeenCalledTimes(1);
    expect(reject).not.toHaveBeenCalled();

    // The header and title were updated in place from the re-read project.
    expect(document.querySelector('.apqaui-html-page-project-name').textContent).toBe('Project name: Wave 70');
    expect(document.querySelector('.apqaui-html-page-project-comment').textContent).toBe('Description: After');
    expect(document.title).toBe('QC rules for Wave 70');
  });

  it('closes without saving when Cancel is clicked', async () => {
    stubFetch(
      { project: { name: 'Wave 69', comment: 'Before' }, path: '/tmp/projects.yaml' },
      { project: { name: 'Wave 69', comment: 'Before' } },
    );

    const resolve = vi.fn();
    const reject = vi.fn();
    const wrapper = mount(ProjectSettingsModal, { props: { resolve, reject } });
    await flushPromises();

    await wrapper.findAll('button').at(0).trigger('click');
    expect(reject).toHaveBeenCalledTimes(1);
    expect(resolve).not.toHaveBeenCalled();
  });
});

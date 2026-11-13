
import { describe, it, expect, vi, afterEach, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

import OnlineMonitor from './index.js';

const POLL_INTERVAL_MS = 5000;

function seedHeaderDom(path) {
  document.body.innerHTML = `<div class="apqaui-html-page-project-path">${path || ''}</div>`;
}

function stubFetch({ healthOk, projectPath }) {
  vi.stubGlobal(
    'fetch',
    vi.fn((url) => {
      if (url === '/health') {
        return Promise.resolve({ ok: healthOk });
      }
      if (url === '/qc/project') {
        if (projectPath instanceof Error) return Promise.reject(projectPath);
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ path: projectPath }),
        });
      }
      return Promise.reject(new Error(`unexpected url ${url}`));
    }),
  );
}

describe('OnlineMonitor', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    document.body.innerHTML = '';
  });

  it('shows the grey offline panel when /health fails', async () => {
    seedHeaderDom('/tmp/projects.yaml');
    stubFetch({ healthOk: false, projectPath: '/tmp/projects.yaml' });

    const wrapper = mount(OnlineMonitor);
    await flushPromises();

    expect(wrapper.find('.apqa-online-monitor').classes()).not.toContain('online');
    expect(wrapper.find('.description').exists()).toBe(true);
    expect(wrapper.find('.config-paths-mismatch-failure').exists()).toBe(false);
  });

  it('shouts in red and offers a reload when the project path changed', async () => {
    seedHeaderDom('/tmp/old.yaml');
    stubFetch({ healthOk: true, projectPath: '/tmp/new.yaml' });

    const wrapper = mount(OnlineMonitor);
    await flushPromises();

    expect(wrapper.find('.apqa-online-monitor').classes()).not.toContain('online');
    const failure = wrapper.find('.config-paths-mismatch-failure');
    expect(failure.exists()).toBe(true);
    expect(failure.text()).toContain('/tmp/old.yaml');
    expect(failure.text()).toContain('/tmp/new.yaml');
    expect(failure.find('.mdm-link-btn').exists()).toBe(true);
    expect(wrapper.find('.description').exists()).toBe(false);
  });

  it('stays hidden when online and the path is unchanged', async () => {
    seedHeaderDom('/tmp/projects.yaml');
    stubFetch({ healthOk: true, projectPath: '/tmp/projects.yaml' });

    const wrapper = mount(OnlineMonitor);
    await flushPromises();

    expect(wrapper.find('.apqa-online-monitor').classes()).toContain('online');
    expect(wrapper.find('.description').exists()).toBe(false);
    expect(wrapper.find('.config-paths-mismatch-failure').exists()).toBe(false);
  });

  it('captures the path from the first project fetch in dev mode and detects a later change', async () => {
    // Vite dev server: the header path element is empty at mount, so the path
    // must be captured from the first successful /qc/project response.
    seedHeaderDom('');

    let current = '/tmp/projects.yaml';
    vi.stubGlobal(
      'fetch',
      vi.fn((url) => {
        if (url === '/health') return Promise.resolve({ ok: true });
        if (url === '/qc/project') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ path: current }),
          });
        }
        return Promise.reject(new Error(`unexpected url ${url}`));
      }),
    );

    const wrapper = mount(OnlineMonitor);
    await flushPromises();
    expect(wrapper.find('.apqa-online-monitor').classes()).toContain('online');
    expect(wrapper.find('.config-paths-mismatch-failure').exists()).toBe(false);

    current = '/tmp/other.yaml';
    await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    await flushPromises();

    expect(wrapper.find('.apqa-online-monitor').classes()).not.toContain('online');
    expect(wrapper.find('.config-paths-mismatch-failure').exists()).toBe(true);
  });
});

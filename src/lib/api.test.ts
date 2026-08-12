import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError, type DSLSpec, type GeneratedProject } from './api';

const sampleDSL: DSLSpec = {
  meta: { name: 'blog-api', version: '1.0.0', framework: 'django', database: 'postgresql' },
  models: {
    User: { fields: { id: { type: 'uuid', primary_key: true } } },
  },
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('api client', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('hits /health at the API root, not under /api/v1', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ status: 'healthy', timestamp: '2026-01-01T00:00:00Z', version: '1.0.0' })
    );

    const result = await api.health();

    expect(result.status).toBe('healthy');
    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl.endsWith('/health')).toBe(true);
    expect(calledUrl).not.toContain('/api/v1/health');
  });

  it('parsePrompt posts the prompt and returns the DSL', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ dsl: sampleDSL, timestamp: '2026-01-01T00:00:00Z' })
    );

    const result = await api.parsePrompt('a blog api');

    expect(result.dsl.meta.name).toBe('blog-api');
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain('/parse-prompt');
    expect(JSON.parse((init as RequestInit).body as string)).toEqual({ prompt: 'a blog api' });
  });

  it('validateDSL returns errors/warnings from the API', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ valid: false, errors: ['meta.name is required'], warnings: [] })
    );

    const result = await api.validateDSL(sampleDSL);

    expect(result.valid).toBe(false);
    expect(result.errors).toHaveLength(1);
  });

  it('generateCode maps the raw API response into a GeneratedProject', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        id: 'abc-123',
        project_name: 'blog-api',
        framework: 'django',
        files: { 'app/models.py': 'class User: ...' },
        file_count: 1,
        timestamp: '2026-01-01T00:00:00Z',
      })
    );

    const project: GeneratedProject = await api.generateCode(sampleDSL, 'django');

    expect(project).toEqual({
      id: 'abc-123',
      name: 'blog-api',
      framework: 'django',
      files: { 'app/models.py': 'class User: ...' },
      file_count: 1,
      status: 'generated',
      createdAt: '2026-01-01T00:00:00Z',
    });
  });

  it('getFrameworks returns the framework list', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        frameworks: [{ id: 'django', name: 'Django + DRF', description: '', language: 'Python', features: [] }],
      })
    );

    const result = await api.getFrameworks();

    expect(result.frameworks[0].id).toBe('django');
  });

  it('surfaces the server-provided error message and status on a 400', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ error: 'Unsupported framework: flask', details: { supported: ['django'] } }, 400)
    );

    await expect(api.getFrameworks()).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      message: 'Unsupported framework: flask',
    });
  });

  it('wraps a network failure (server not running) in a descriptive ApiError', async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(api.health()).rejects.toBeInstanceOf(ApiError);
    await expect(api.health()).rejects.toThrow(/core\/app\.py/);
  });

  it('downloadProject zips the in-memory files without another network call', async () => {
    const fetchMock = vi.mocked(fetch);
    const project: GeneratedProject = {
      id: '1',
      name: 'blog-api',
      framework: 'django',
      files: { 'requirements.txt': 'Django==5.0\n' },
      file_count: 1,
      status: 'generated',
      createdAt: '2026-01-01T00:00:00Z',
    };

    const blob = await api.downloadProject(project);

    expect(blob).toBeInstanceOf(Blob);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('deleteProject resolves locally without calling the network (no server persistence exists)', async () => {
    const fetchMock = vi.mocked(fetch);

    await expect(api.deleteProject('some-id')).resolves.toBeUndefined();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('getDeploymentProviders returns a static local list without calling the network', async () => {
    const fetchMock = vi.mocked(fetch);

    const result = await api.getDeploymentProviders();

    expect(result.providers.length).toBeGreaterThan(0);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('deployProject simulates a deployment and returns a provider-shaped URL', async () => {
    const result = await api.deployProject('proj-1', 'railway', {
      projectName: 'My Blog API',
      environment: 'production',
    });

    expect(result.status).toBe('success');
    expect(result.provider).toBe('railway');
    expect(result.url).toBe('https://my-blog-api.railway.app');
  });
});

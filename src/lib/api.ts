/**
 * HTTP client for the Backend Builder core generation engine (core/app.py).
 *
 * Mirrors the real routes documented in core/openapi.yaml. A couple of
 * methods below (`getDeploymentProviders`, `deployProject`) do not call a
 * real backend endpoint at all, because the core engine has no cloud
 * deployment infrastructure to call - see the "Project Status" section of
 * the README. They're implemented as clearly-marked client-side
 * simulations rather than silently faked network calls, so it's obvious
 * from reading this file (and from the Deploy page's UI) which parts are
 * real.
 */

import JSZip from 'jszip';

export interface DSLField {
  type:
    | 'string'
    | 'text'
    | 'integer'
    | 'float'
    | 'boolean'
    | 'datetime'
    | 'date'
    | 'uuid'
    | 'url'
    | 'email'
    | 'json'
    | 'foreign_key'
    | 'many_to_many'
    | 'choice'
    | string;
  primary_key?: boolean;
  auto_generated?: boolean;
  required?: boolean;
  unique?: boolean;
  max_length?: number;
  default?: unknown;
  hashed?: boolean;
  auto_now_add?: boolean;
  auto_now?: boolean;
  model?: string;
  on_delete?: 'cascade' | 'set_null' | 'protect' | 'restrict';
  choices?: string[];
}

export interface DSLModel {
  fields: Record<string, DSLField>;
  permissions?: {
    read?: string[];
    write?: string[];
    create?: string[];
    delete?: string[];
  };
}

export interface DSLEndpoint {
  path: string;
  method: string;
  handler?: string;
  public?: boolean;
  auth_required?: boolean;
}

export interface DSLSpec {
  meta: {
    name: string;
    description?: string;
    version: string;
    framework: 'django' | 'go-fiber' | 'rails' | string;
    database?: string;
  };
  auth?: {
    provider?: 'jwt' | 'oauth2' | 'custom' | string;
    user_model?: string;
    required_fields?: string[];
    optional_fields?: string[];
  };
  models: Record<string, DSLModel>;
  api?: {
    base_path?: string;
    endpoints?: DSLEndpoint[];
  };
  jobs?: unknown[];
  deployment?: {
    docker?: {
      port?: number;
      health_check?: string;
    };
  };
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface Framework {
  id: 'django' | 'go-fiber' | 'rails' | string;
  name: string;
  description: string;
  language: string;
  features: string[];
}

/** The shape the web UI works with, after mapping the raw
 * `POST /api/v1/generate-code` response (which uses `project_name`, and has
 * no `status`/`createdAt`, since the core engine doesn't persist projects)
 * into something the Dashboard/CodeGenerator pages can track locally. */
export interface GeneratedProject {
  id: string;
  name: string;
  framework: string;
  files: Record<string, string>;
  file_count: number;
  status: 'generated' | 'building' | 'deployed' | 'error';
  createdAt: string;
}

export interface DeploymentProvider {
  id: string;
  name: string;
  description: string;
  features: string[];
  pricing: string;
}

export interface DeploymentConfig {
  projectName: string;
  environment: string;
  customDomain?: string;
}

export interface DeploymentResult {
  status: 'success' | 'error';
  url: string;
  provider: string;
}

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

// VITE_API_URL points at the versioned API root (see .env.example), e.g.
// "http://localhost:8000/api/v1". /health lives one level up, at the Flask
// app root, so it's requested against ROOT_URL instead of BASE_URL.
const DEFAULT_API_URL = 'http://localhost:8000/api/v1';
const BASE_URL = (import.meta.env.VITE_API_URL || DEFAULT_API_URL).replace(/\/+$/, '');
const ROOT_URL = BASE_URL.replace(/\/api\/v1$/, '');

async function request<T>(baseUrl: string, path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });
  } catch (networkError) {
    throw new ApiError(
      `Could not reach the Backend Builder core API at ${baseUrl}. Is core/app.py running?`,
      0,
      networkError
    );
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    let details: unknown;
    try {
      const body = await response.json();
      if (body && typeof body.error === 'string') message = body.error;
      details = body?.details;
    } catch {
      // Non-JSON error body (e.g. an HTML error page) - keep the generic message.
    }
    throw new ApiError(message, response.status, details);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function slugify(value: string): string {
  return (
    value
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'app'
  );
}

export const api = {
  /** GET /health - served at the Flask app root, not under /api/v1. */
  health(): Promise<{ status: string; timestamp: string; version: string }> {
    return request(ROOT_URL, '/health', { method: 'GET' });
  },

  /** POST /api/v1/parse-prompt */
  async parsePrompt(prompt: string): Promise<{ dsl: DSLSpec; timestamp: string }> {
    return request(BASE_URL, '/parse-prompt', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
  },

  /** POST /api/v1/validate-dsl */
  async validateDSL(dsl: DSLSpec): Promise<ValidationResult> {
    return request(BASE_URL, '/validate-dsl', {
      method: 'POST',
      body: JSON.stringify({ dsl }),
    });
  },

  /** POST /api/v1/generate-code (JSON form; returns file contents inline). */
  async generateCode(dsl: DSLSpec, framework: string): Promise<GeneratedProject> {
    const result = await request<{
      id: string;
      project_name: string;
      framework: string;
      files: Record<string, string>;
      file_count: number;
      timestamp: string;
    }>(BASE_URL, '/generate-code', {
      method: 'POST',
      body: JSON.stringify({ dsl, framework, format: 'json' }),
    });

    return {
      id: result.id,
      name: result.project_name,
      framework: result.framework,
      files: result.files,
      file_count: result.file_count,
      status: 'generated',
      createdAt: result.timestamp,
    };
  },

  /** GET /api/v1/frameworks */
  async getFrameworks(): Promise<{ frameworks: Framework[] }> {
    return request(BASE_URL, '/frameworks', { method: 'GET' });
  },

  /**
   * Zips up an already-generated project client-side (the files are
   * already in memory from `generateCode`), rather than round-tripping
   * back to the server. `jszip` is a direct dependency for exactly this.
   */
  async downloadProject(project: GeneratedProject): Promise<Blob> {
    const zip = new JSZip();
    for (const [path, content] of Object.entries(project.files)) {
      zip.file(path, content);
    }
    return zip.generateAsync({ type: 'blob' });
  },

  /**
   * The core engine has no database and doesn't persist generated
   * projects server-side (see core/app.py) - "your projects" live only in
   * this browser's local storage (src/lib/store.ts). There is nothing to
   * delete on a server, so this is a local no-op the caller awaits purely
   * to keep the same async shape as the rest of this client.
   */
  async deleteProject(_projectId: string): Promise<void> {
    return Promise.resolve();
  },

  /**
   * There is no real cloud-deployment backend (see README "Project
   * Status"). Returns a fixed, clearly-local list instead of hitting an
   * endpoint that doesn't exist in core/app.py.
   */
  async getDeploymentProviders(): Promise<{ providers: DeploymentProvider[] }> {
    return Promise.resolve({
      providers: [
        {
          id: 'railway',
          name: 'Railway',
          description: 'Deploy with zero configuration',
          features: ['Auto-deploy from Git', 'Built-in databases', 'Custom domains', 'Environment variables'],
          pricing: 'Free tier available',
        },
        {
          id: 'render',
          name: 'Render',
          description: 'Modern cloud platform',
          features: ['Auto-scaling', 'PostgreSQL', 'Redis', 'Static sites'],
          pricing: 'Free tier available',
        },
        {
          id: 'fly',
          name: 'Fly.io',
          description: 'Deploy close to your users',
          features: ['Global deployment', 'Edge computing', 'Auto-scaling', 'Postgres clusters'],
          pricing: 'Pay for resources used',
        },
      ],
    });
  },

  /**
   * Simulated deployment - no cloud infrastructure is actually
   * provisioned. Mirrors `copilot/copilot.py`'s `deploy_project`, which is
   * a simulation for the same reason (documented in the README). The
   * Deploy page shows a "Simulated" notice next to this so it isn't
   * presented to users as a real deploy.
   */
  async deployProject(
    projectId: string,
    provider: string,
    config: DeploymentConfig
  ): Promise<DeploymentResult> {
    await new Promise((resolve) => setTimeout(resolve, 1200));
    return {
      status: 'success',
      url: `https://${slugify(config.projectName || projectId)}.${provider}.app`,
      provider,
    };
  },
};

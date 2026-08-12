import { beforeEach, describe, expect, it } from 'vitest';
import { useProjectData, useSystemData, useUIState } from './store';
import type { GeneratedProject } from './api';

const project = (overrides: Partial<GeneratedProject> = {}): GeneratedProject => ({
  id: 'p1',
  name: 'blog-api',
  framework: 'django',
  files: { 'app/models.py': '...' },
  file_count: 1,
  status: 'generated',
  createdAt: '2026-01-01T00:00:00Z',
  ...overrides,
});

describe('useProjectData', () => {
  beforeEach(() => {
    useProjectData.setState({
      currentDSL: null,
      currentProject: null,
      projects: [],
      activeFile: null,
      isGenerating: false,
      isDeploying: false,
    });
  });

  it('starts with an empty project list and no active DSL/project', () => {
    const state = useProjectData.getState();
    expect(state.projects).toEqual([]);
    expect(state.currentDSL).toBeNull();
    expect(state.currentProject).toBeNull();
  });

  it('addProject prepends new projects and de-duplicates by id', () => {
    const { addProject } = useProjectData.getState();
    addProject(project({ id: 'p1', name: 'first' }));
    addProject(project({ id: 'p2', name: 'second' }));
    addProject(project({ id: 'p1', name: 'first-regenerated' }));

    const { projects } = useProjectData.getState();
    expect(projects).toHaveLength(2);
    expect(projects[0]).toMatchObject({ id: 'p1', name: 'first-regenerated' });
  });

  it('removeProject drops the project and clears currentProject if it matches', () => {
    const { addProject, setCurrentProject, removeProject } = useProjectData.getState();
    addProject(project({ id: 'p1' }));
    setCurrentProject(project({ id: 'p1' }));

    removeProject('p1');

    const state = useProjectData.getState();
    expect(state.projects).toHaveLength(0);
    expect(state.currentProject).toBeNull();
  });

  it('updateProjectStatus updates both the list entry and currentProject in place', () => {
    const { addProject, setCurrentProject, updateProjectStatus } = useProjectData.getState();
    addProject(project({ id: 'p1', status: 'generated' }));
    setCurrentProject(project({ id: 'p1', status: 'generated' }));

    updateProjectStatus('p1', 'deployed');

    const state = useProjectData.getState();
    expect(state.projects[0].status).toBe('deployed');
    expect(state.currentProject?.status).toBe('deployed');
  });

  it('setCurrentProject resets the active file selection', () => {
    const { setActiveFile, setCurrentProject } = useProjectData.getState();
    setActiveFile('app/models.py');
    expect(useProjectData.getState().activeFile).toBe('app/models.py');

    setCurrentProject(project());
    expect(useProjectData.getState().activeFile).toBeNull();
  });

  it('setIsGenerating and setIsDeploying toggle independently', () => {
    const { setIsGenerating, setIsDeploying } = useProjectData.getState();
    setIsGenerating(true);
    expect(useProjectData.getState().isGenerating).toBe(true);
    expect(useProjectData.getState().isDeploying).toBe(false);

    setIsDeploying(true);
    expect(useProjectData.getState().isDeploying).toBe(true);
  });
});

describe('useUIState', () => {
  beforeEach(() => {
    useUIState.setState({ theme: 'dark', sidebarCollapsed: false, notifications: [] });
  });

  it('setTheme toggles the theme', () => {
    useUIState.getState().setTheme('light');
    expect(useUIState.getState().theme).toBe('light');
  });

  it('setSidebarCollapsed updates the flag', () => {
    useUIState.getState().setSidebarCollapsed(true);
    expect(useUIState.getState().sidebarCollapsed).toBe(true);
  });

  it('addNotification prepends an unread notification with a generated id', () => {
    useUIState.getState().addNotification({ type: 'success', title: 'Done', message: 'It worked' });

    const { notifications } = useUIState.getState();
    expect(notifications).toHaveLength(1);
    expect(notifications[0]).toMatchObject({ type: 'success', title: 'Done', read: false });
    expect(notifications[0].id).toBeTruthy();
  });

  it('markNotificationRead flips only the matching notification', () => {
    const { addNotification } = useUIState.getState();
    addNotification({ type: 'info', title: 'A', message: '' });
    addNotification({ type: 'info', title: 'B', message: '' });
    const [second, first] = useUIState.getState().notifications;

    useUIState.getState().markNotificationRead(first.id);

    const notifications = useUIState.getState().notifications;
    expect(notifications.find((n) => n.id === first.id)?.read).toBe(true);
    expect(notifications.find((n) => n.id === second.id)?.read).toBe(false);
  });

  it('clearNotifications empties the list', () => {
    useUIState.getState().addNotification({ type: 'info', title: 'A', message: '' });
    useUIState.getState().clearNotifications();
    expect(useUIState.getState().notifications).toEqual([]);
  });
});

describe('useSystemData', () => {
  beforeEach(() => {
    useSystemData.setState({
      systemStatus: { api: 'offline', database: 'disconnected', aiEngine: 'inactive' },
      user: null,
    });
  });

  it('starts offline/disconnected/inactive and with no user', () => {
    const state = useSystemData.getState();
    expect(state.systemStatus).toEqual({ api: 'offline', database: 'disconnected', aiEngine: 'inactive' });
    expect(state.user).toBeNull();
  });

  it('setApiStatus("online") also flips database/aiEngine, since the core engine is one process', () => {
    useSystemData.getState().setApiStatus('online');

    expect(useSystemData.getState().systemStatus).toEqual({
      api: 'online',
      database: 'connected',
      aiEngine: 'active',
    });
  });

  it('setApiStatus("offline") reverts database/aiEngine too', () => {
    useSystemData.getState().setApiStatus('online');
    useSystemData.getState().setApiStatus('offline');

    expect(useSystemData.getState().systemStatus).toEqual({
      api: 'offline',
      database: 'disconnected',
      aiEngine: 'inactive',
    });
  });
});

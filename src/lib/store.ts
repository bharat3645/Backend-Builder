/**
 * Zustand stores backing the web UI. Split into three slices matching how
 * the components actually use them:
 *  - useProjectData: the DSL/project the user is working on right now.
 *    Persisted to localStorage since the core API is stateless and doesn't
 *    remember projects between requests (see core/app.py) - without this,
 *    a page refresh would silently lose a generated project.
 *  - useUIState: ephemeral UI state (theme, sidebar, toast notifications).
 *  - useSystemData: the live status strip driven by the /health poll in
 *    App.tsx.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { DSLSpec, GeneratedProject } from './api';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
}

interface ProjectDataState {
  currentDSL: DSLSpec | null;
  currentProject: GeneratedProject | null;
  projects: GeneratedProject[];
  activeFile: string | null;
  isGenerating: boolean;
  isDeploying: boolean;

  setCurrentDSL: (dsl: DSLSpec | null) => void;
  setCurrentProject: (project: GeneratedProject | null) => void;
  addProject: (project: GeneratedProject) => void;
  removeProject: (id: string) => void;
  updateProjectStatus: (id: string, status: GeneratedProject['status']) => void;
  setActiveFile: (path: string | null) => void;
  setIsGenerating: (value: boolean) => void;
  setIsDeploying: (value: boolean) => void;
}

export const useProjectData = create<ProjectDataState>()(
  persist(
    (set) => ({
      currentDSL: null,
      currentProject: null,
      projects: [],
      activeFile: null,
      isGenerating: false,
      isDeploying: false,

      setCurrentDSL: (dsl) => set({ currentDSL: dsl }),

      setCurrentProject: (project) => set({ currentProject: project, activeFile: null }),

      addProject: (project) =>
        set((state) => ({
          projects: [project, ...state.projects.filter((p) => p.id !== project.id)],
        })),

      removeProject: (id) =>
        set((state) => ({
          projects: state.projects.filter((p) => p.id !== id),
          currentProject: state.currentProject?.id === id ? null : state.currentProject,
        })),

      updateProjectStatus: (id, status) =>
        set((state) => ({
          projects: state.projects.map((p) => (p.id === id ? { ...p, status } : p)),
          currentProject:
            state.currentProject?.id === id
              ? { ...state.currentProject, status }
              : state.currentProject,
        })),

      setActiveFile: (path) => set({ activeFile: path }),
      setIsGenerating: (value) => set({ isGenerating: value }),
      setIsDeploying: (value) => set({ isDeploying: value }),
    }),
    {
      name: 'backend-builder-projects',
      // Only persist data, never the isGenerating/isDeploying/activeFile
      // in-flight UI flags - those should always start fresh on load.
      partialize: (state) => ({
        currentDSL: state.currentDSL,
        currentProject: state.currentProject,
        projects: state.projects,
      }),
    }
  )
);

interface UIState {
  theme: 'dark' | 'light';
  sidebarCollapsed: boolean;
  notifications: Notification[];

  setTheme: (theme: 'dark' | 'light') => void;
  setSidebarCollapsed: (value: boolean) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'read' | 'createdAt'>) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;
}

const MAX_NOTIFICATIONS = 50;

function makeId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export const useUIState = create<UIState>((set) => ({
  theme: 'dark',
  sidebarCollapsed: false,
  notifications: [],

  setTheme: (theme) => set({ theme }),
  setSidebarCollapsed: (value) => set({ sidebarCollapsed: value }),

  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        { ...notification, id: makeId(), read: false, createdAt: new Date().toISOString() },
        ...state.notifications,
      ].slice(0, MAX_NOTIFICATIONS),
    })),

  markNotificationRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) => (n.id === id ? { ...n, read: true } : n)),
    })),

  clearNotifications: () => set({ notifications: [] }),
}));

export interface SystemStatus {
  api: 'online' | 'offline';
  database: 'connected' | 'disconnected';
  aiEngine: 'active' | 'inactive';
}

export interface SystemUser {
  name: string;
  avatar?: string;
  plan?: string;
}

interface SystemDataState {
  systemStatus: SystemStatus;
  user: SystemUser | null;
  setApiStatus: (status: 'online' | 'offline') => void;
}

export const useSystemData = create<SystemDataState>((set) => ({
  systemStatus: {
    api: 'offline',
    database: 'disconnected',
    aiEngine: 'inactive',
  },
  // No user accounts exist in the core engine (see core/app.py) - null
  // until that's real, rather than fabricating a signed-in user.
  user: null,

  setApiStatus: (status) =>
    set((state) => ({
      systemStatus: {
        ...state.systemStatus,
        api: status,
        // The core engine is a single Flask process - there's no separate
        // database or AI microservice to probe independently, so these
        // track overall API reachability rather than faking distinct
        // health checks the backend doesn't expose.
        database: status === 'online' ? 'connected' : 'disconnected',
        aiEngine: status === 'online' ? 'active' : 'inactive',
      },
    })),
}));

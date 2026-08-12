import React, { useEffect, useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Database,
  Globe,
  Activity,
  Clock,
  ExternalLink,
  Play,
  Trash2
} from 'lucide-react';
import { useProjectData, useSystemData } from '../lib/store';
import { api } from '../lib/api';

const Dashboard: React.FC = () => {
  const { projects, removeProject } = useProjectData();
  const { systemStatus } = useSystemData();
  const [stats, setStats] = useState({
    totalProjects: 0,
    activeDeployments: 0,
    apiRequests: 0,
    uptime: '99.9%'
  });

  useEffect(() => {
    // Calculate real stats from projects
    const totalProjects = projects.length;
    const activeDeployments = projects.filter(p => p.status === 'deployed').length;
    
    setStats({
      totalProjects,
      activeDeployments,
      apiRequests: totalProjects * 1247, // Mock calculation
      uptime: '99.9%'
    });
  }, [projects]);

  const metrics = [
    {
      title: 'Total Projects',
      value: stats.totalProjects.toString(),
      change: projects.length > 0 ? '+1 this session' : 'No projects yet',
      icon: Database,
      color: 'blue'
    },
    {
      title: 'API Requests',
      value: stats.apiRequests.toLocaleString(),
      change: '+12% from last month',
      icon: TrendingUp,
      color: 'green'
    },
    {
      title: 'Active Deployments',
      value: stats.activeDeployments.toString(),
      change: stats.activeDeployments > 0 ? 'Live and running' : 'None deployed',
      icon: Globe,
      color: 'purple'
    },
    {
      title: 'System Uptime',
      value: stats.uptime,
      change: '+0.2% improvement',
      icon: Activity,
      color: 'yellow'
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'deployed':
        return 'text-[#00ff88] bg-[#00ff88]/20';
      case 'building':
        return 'text-[#ffaa00] bg-[#ffaa00]/20';
      case 'generated':
        return 'text-[#00ccff] bg-[#00ccff]/20';
      case 'error':
        return 'text-[#ff4444] bg-[#ff4444]/20';
      default:
        return 'text-gray-400 bg-gray-400/20';
    }
  };

  const getMetricColor = (color: string) => {
    switch (color) {
      case 'blue':
        return 'text-[#00ccff] bg-[#00ccff]/20';
      case 'green':
        return 'text-[#00ff88] bg-[#00ff88]/20';
      case 'purple':
        return 'text-purple-400 bg-purple-400/20';
      case 'yellow':
        return 'text-[#ffaa00] bg-[#ffaa00]/20';
      default:
        return 'text-gray-400 bg-gray-400/20';
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (confirm('Are you sure you want to delete this project?')) {
      try {
        await api.deleteProject(projectId);
        removeProject(projectId);
      } catch (error) {
        console.error('Failed to delete project:', error);
      }
    }
  };

  return (
    <div className="h-full bg-[#0a0a0a] text-white overflow-auto">
      <div className="max-w-7xl mx-auto p-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white">Dashboard</h1>
            <p className="text-gray-400 mt-2">Monitor and manage your deployed backends</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${
                systemStatus.api === 'online' ? 'bg-[#00ff88]' : 'bg-[#ff4444]'
              }`}></div>
              <span className="text-sm text-gray-300">
                {systemStatus.api === 'online' ? 'All systems operational' : 'System issues detected'}
              </span>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metrics.map((metric, index) => {
            const Icon = metric.icon;
            return (
              <div
                key={index}
                className="bg-[#111111] border border-[#333333] rounded-lg p-6 hover:border-[#444444] transition-colors"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-2 rounded-lg ${getMetricColor(metric.color)}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <BarChart3 className="w-4 h-4 text-gray-500" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-2xl font-bold text-white">{metric.value}</h3>
                  <p className="text-sm text-gray-400">{metric.title}</p>
                  <p className="text-xs text-gray-500">{metric.change}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Projects Table */}
        <div className="bg-[#111111] border border-[#333333] rounded-lg overflow-hidden">
          <div className="p-6 border-b border-[#333333]">
            <h2 className="text-xl font-semibold text-white">Your Projects</h2>
          </div>
          {projects.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#1a1a1a]">
                  <tr>
                    <th className="text-left p-4 text-gray-300 font-medium">Project</th>
                    <th className="text-left p-4 text-gray-300 font-medium">Framework</th>
                    <th className="text-left p-4 text-gray-300 font-medium">Status</th>
                    <th className="text-left p-4 text-gray-300 font-medium">Created</th>
                    <th className="text-left p-4 text-gray-300 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#333333]">
                  {projects.map((project) => (
                    <tr key={project.id} className="hover:bg-[#1a1a1a] transition-colors">
                      <td className="p-4">
                        <div className="font-medium text-white">{project.name}</div>
                        <div className="text-sm text-gray-400">{Object.keys(project.files).length} files</div>
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-1 bg-[#333333] text-gray-300 rounded text-sm">
                          {project.framework}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded text-sm ${getStatusColor(project.status)}`}>
                          {project.status}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center space-x-1 text-gray-400">
                          <Clock className="w-3 h-3" />
                          <span className="text-sm">{new Date(project.createdAt).toLocaleDateString()}</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center space-x-2">
                          {project.status === 'deployed' && (
                            <button className="p-1 text-[#00ff88] hover:text-[#00ccff] transition-colors">
                              <ExternalLink className="w-4 h-4" />
                            </button>
                          )}
                          <button className="p-1 text-gray-400 hover:text-white transition-colors">
                            <Play className="w-4 h-4" />
                          </button>
                          <button 
                            onClick={() => handleDeleteProject(project.id)}
                            className="p-1 text-gray-400 hover:text-[#ff4444] transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-12 text-center">
              <Database className="w-16 h-16 text-gray-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No Projects Yet</h3>
              <p className="text-gray-400 mb-6">Start building your first backend with InfraNest</p>
              <a
                href="/prompt"
                className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black rounded-lg font-semibold transition-all hover:shadow-lg hover:shadow-[#00ff88]/25"
              >
                <Play className="w-4 h-4 mr-2" />
                Create Your First Project
              </a>
            </div>
          )}
        </div>

        {/* Recent Activity & System Health */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-[#111111] border border-[#333333] rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
            <div className="space-y-4">
              {projects.slice(0, 5).map((project, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    project.status === 'deployed' ? 'bg-[#00ff88]' : 
                    project.status === 'building' ? 'bg-[#ffaa00]' : 'bg-[#00ccff]'
                  }`}></div>
                  <div className="flex-1">
                    <div className="text-white text-sm">
                      {project.name} {project.status === 'deployed' ? 'deployed successfully' : 
                       project.status === 'building' ? 'is building' : 'was generated'}
                    </div>
                    <div className="text-gray-400 text-xs">{new Date(project.createdAt).toLocaleString()}</div>
                  </div>
                </div>
              ))}
              {projects.length === 0 && (
                <div className="text-center py-8">
                  <Activity className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-400">No recent activity</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">System Health</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">API Gateway</span>
                <span className={`text-sm ${
                  systemStatus.api === 'online' ? 'text-[#00ff88]' : 'text-[#ff4444]'
                }`}>
                  {systemStatus.api}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Database</span>
                <span className={`text-sm ${
                  systemStatus.database === 'connected' ? 'text-[#00ff88]' : 'text-[#ff4444]'
                }`}>
                  {systemStatus.database}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-300">AI Engine</span>
                <span className={`text-sm ${
                  systemStatus.aiEngine === 'active' ? 'text-[#00ff88]' : 'text-[#ff4444]'
                }`}>
                  {systemStatus.aiEngine}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-300">CDN</span>
                <span className="text-[#00ff88] text-sm">Healthy</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
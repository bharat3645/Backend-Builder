import React, { useState, useEffect } from 'react';
import {
  Rocket,
  Globe,
  Database,
  Shield,
  CheckCircle,
  AlertCircle,
  Loader2,
  ExternalLink,
  AlertTriangle
} from 'lucide-react';
import { useProjectData, useUIState } from '../lib/store';
import { api, DeploymentProvider } from '../lib/api';
import toast from 'react-hot-toast';

const Deploy: React.FC = () => {
  const { currentProject, isDeploying, setIsDeploying, updateProjectStatus } = useProjectData();
  const { addNotification } = useUIState();
  const [selectedProvider, setSelectedProvider] = useState('railway');
  const [deploymentStatus, setDeploymentStatus] = useState<string | null>(null);
  const [deploymentUrl, setDeploymentUrl] = useState<string | null>(null);
  const [providers, setProviders] = useState<DeploymentProvider[]>([]);
  const [deploymentConfig, setDeploymentConfig] = useState({
    projectName: currentProject?.name || 'my-api',
    environment: 'production',
    customDomain: ''
  });

  useEffect(() => {
    // Load deployment providers
    const loadProviders = async () => {
      try {
        const result = await api.getDeploymentProviders();
        setProviders(result.providers);
      } catch (error) {
        console.error('Failed to load providers:', error);
        // Fallback providers
        setProviders([
          {
            id: 'railway',
            name: 'Railway',
            description: 'Deploy with zero configuration',
            features: ['Auto-deploy from Git', 'Built-in databases', 'Custom domains', 'Environment variables'],
            pricing: 'Free tier available'
          },
          {
            id: 'render',
            name: 'Render',
            description: 'Modern cloud platform',
            features: ['Auto-scaling', 'PostgreSQL', 'Redis', 'Static sites'],
            pricing: 'Free tier available'
          },
          {
            id: 'fly',
            name: 'Fly.io',
            description: 'Deploy close to your users',
            features: ['Global deployment', 'Edge computing', 'Auto-scaling', 'Postgres clusters'],
            pricing: 'Pay for resources used'
          }
        ]);
      }
    };

    loadProviders();
  }, []);

  const deploymentSteps = [
    { step: 1, title: 'Code Generation', status: currentProject ? 'completed' : 'pending', description: 'Backend code generated successfully' },
    { step: 2, title: 'Containerization', status: isDeploying ? 'in-progress' : 'pending', description: 'Docker image built and optimized' },
    { step: 3, title: 'Database Setup', status: 'pending', description: 'PostgreSQL database provisioned' },
    { step: 4, title: 'Environment Config', status: 'pending', description: 'Environment variables configured' },
    { step: 5, title: 'Deployment', status: 'pending', description: 'Deploying to production servers' },
    { step: 6, title: 'Health Check', status: 'pending', description: 'Verifying deployment health' },
    { step: 7, title: 'DNS Setup', status: 'pending', description: 'Configuring custom domain' }
  ];

  const handleDeploy = async () => {
    if (!currentProject) {
      toast.error('No project to deploy. Please generate code first.');
      return;
    }

    setIsDeploying(true);
    setDeploymentStatus('deploying');
    
    try {
      const result = await api.deployProject(currentProject.id, selectedProvider, deploymentConfig);
      setDeploymentStatus('success');
      setDeploymentUrl(result.url ?? null);
      updateProjectStatus(currentProject.id, 'deployed');
      toast.success('Simulated deployment complete (no cloud infrastructure was provisioned)');
      addNotification({
        type: 'success',
        title: 'Deployment Complete',
        message: `${currentProject.name} has been deployed successfully to ${selectedProvider}.`
      });
    } catch (error) {
      console.error('Deployment failed:', error);
      setDeploymentStatus('error');
      toast.error('Deployment failed. Please try again.');
      addNotification({
        type: 'error',
        title: 'Deployment Failed',
        message: 'Unable to deploy your project. Please check your configuration and try again.'
      });
    } finally {
      setIsDeploying(false);
    }
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-[#00ff88]" />;
      case 'in-progress':
        return <Loader2 className="w-5 h-5 text-[#00ccff] animate-spin" />;
      case 'pending':
        return <div className="w-5 h-5 rounded-full border-2 border-[#333333]" />;
      default:
        return <AlertCircle className="w-5 h-5 text-[#ff4444]" />;
    }
  };

  if (!currentProject) {
    return (
      <div className="h-full bg-[#0a0a0a] text-white flex items-center justify-center">
        <div className="max-w-2xl text-center space-y-8">
          <div className="space-y-4">
            <AlertTriangle className="w-16 h-16 text-[#ffaa00] mx-auto" />
            <h1 className="text-4xl font-bold text-white">No Project to Deploy</h1>
            <p className="text-gray-400">
              You need to generate a project first before you can deploy it. Please go back and create your backend code.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-[#0a0a0a] text-white overflow-auto">
      <div className="max-w-7xl mx-auto p-8 space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-white">Deploy Your Backend</h1>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Deploy your generated backend to the cloud with one click. Choose your preferred hosting provider and we'll handle the rest.
          </p>
        </div>

        {/* Honest disclosure: there is no real cloud deployment backend yet
            (see README "Project Status"). This page walks through the UX
            end to end, but nothing below actually provisions infrastructure. */}
        <div className="flex items-start space-x-3 bg-[#ffaa00]/10 border border-[#ffaa00]/30 rounded-lg p-4 max-w-3xl mx-auto">
          <AlertTriangle className="w-5 h-5 text-[#ffaa00] flex-shrink-0 mt-0.5" />
          <p className="text-sm text-[#ffaa00]">
            <strong>Simulated:</strong> deploying here does not provision any real cloud
            infrastructure - no server is created and the resulting URL will not resolve. This
            page demonstrates the intended UX ahead of a real deployment integration.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Provider Selection */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Choose Hosting Provider</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {providers.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider.id)}
                    className={`p-6 rounded-lg border transition-all text-left ${
                      selectedProvider === provider.id
                        ? 'bg-[#00ff88]/10 border-[#00ff88] text-[#00ff88]'
                        : 'bg-[#1a1a1a] border-[#333333] text-gray-300 hover:bg-[#222222] hover:border-[#444444]'
                    }`}
                  >
                    <div className="space-y-3">
                      <div className="flex items-center space-x-3">
                        <div>
                          <h3 className="font-semibold">{provider.name}</h3>
                          <p className="text-xs text-gray-400">{provider.pricing}</p>
                        </div>
                      </div>
                      <p className="text-sm">{provider.description}</p>
                      <div className="space-y-1">
                        {provider.features.map((feature: string, index: number) => (
                          <div key={index} className="flex items-center space-x-2">
                            <CheckCircle className="w-3 h-3 text-[#00ff88]" />
                            <span className="text-xs">{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Deployment Configuration */}
            <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Deployment Configuration</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Project Name
                  </label>
                  <input
                    type="text"
                    value={deploymentConfig.projectName}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, projectName: e.target.value }))}
                    className="w-full p-3 bg-[#1a1a1a] border border-[#333333] text-white rounded-lg focus:border-[#00ff88] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Environment
                  </label>
                  <select 
                    value={deploymentConfig.environment}
                    onChange={(e) => setDeploymentConfig(prev => ({ ...prev, environment: e.target.value }))}
                    className="w-full p-3 bg-[#1a1a1a] border border-[#333333] text-white rounded-lg focus:border-[#00ff88] focus:outline-none"
                  >
                    <option value="production">Production</option>
                    <option value="staging">Staging</option>
                    <option value="development">Development</option>
                  </select>
                </div>
              </div>
              
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Custom Domain (Optional)
                </label>
                <input
                  type="text"
                  placeholder="api.yourdomain.com"
                  value={deploymentConfig.customDomain}
                  onChange={(e) => setDeploymentConfig(prev => ({ ...prev, customDomain: e.target.value }))}
                  className="w-full p-3 bg-[#1a1a1a] border border-[#333333] text-white rounded-lg focus:border-[#00ff88] focus:outline-none placeholder-gray-500"
                />
              </div>
            </div>

            {/* Deploy Button */}
            <div className="text-center">
              <button
                onClick={handleDeploy}
                disabled={isDeploying}
                className="flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black rounded-lg font-semibold transition-all mx-auto hover:shadow-lg hover:shadow-[#00ff88]/25 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isDeploying ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Deploying...</span>
                  </>
                ) : (
                  <>
                    <Rocket className="w-5 h-5" />
                    <span>Deploy to {providers.find(p => p.id === selectedProvider)?.name}</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Deployment Status */}
          <div className="space-y-6">
            <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Deployment Status</h3>
              <div className="space-y-3">
                {deploymentSteps.map((step) => (
                  <div key={step.step} className="flex items-center space-x-3">
                    {getStepIcon(step.status)}
                    <div className="flex-1">
                      <div className="font-medium text-white text-sm">{step.title}</div>
                      <div className="text-xs text-gray-400">{step.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Deployment Info */}
            {deploymentStatus === 'success' && (
              <div className="bg-[#00ff88]/10 border border-[#00ff88]/50 rounded-lg p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <CheckCircle className="w-5 h-5 text-[#00ff88]" />
                  <h3 className="font-semibold text-[#00ff88]">Simulated Deployment Complete</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300">URL:</span>
                    <a
                      href={deploymentUrl ?? '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#00ccff] hover:text-[#00ff88] flex items-center space-x-1"
                    >
                      <span>{(deploymentUrl ?? '').replace(/^https?:\/\//, '')}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300">Status:</span>
                    <span className="text-[#ffaa00]">Simulated (not live)</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-300">Database:</span>
                    <span className="text-[#00ccff]">PostgreSQL</span>
                  </div>
                </div>
              </div>
            )}

            {/* Resource Usage */}
            <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Resource Overview</h3>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <Database className="w-5 h-5 text-[#00ccff]" />
                  <div>
                    <div className="text-white font-medium">Database</div>
                    <div className="text-sm text-gray-400">PostgreSQL 15</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <Globe className="w-5 h-5 text-[#00ff88]" />
                  <div>
                    <div className="text-white font-medium">Web Service</div>
                    <div className="text-sm text-gray-400">{currentProject.framework} + Docker</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <Shield className="w-5 h-5 text-purple-400" />
                  <div>
                    <div className="text-white font-medium">Security</div>
                    <div className="text-sm text-gray-400">HTTPS + JWT Auth</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Deploy;
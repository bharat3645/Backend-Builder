import React, { useState, useEffect } from 'react';
import { 
  Code, 
  Download, 
  Play,
  CheckCircle,
  Loader2,
  ArrowRight,
  AlertTriangle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import CodeEditor from '../components/CodeEditor';
import { api, Framework } from '../lib/api';
import { useProjectData, useUIState } from '../lib/store';

const CodeGenerator: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentDSL,
    currentProject,
    setCurrentProject,
    addProject,
    isGenerating,
    setIsGenerating
  } = useProjectData();
  const { addNotification } = useUIState();

  const [selectedFramework, setSelectedFramework] = useState('django');
  const [frameworks, setFrameworks] = useState<Framework[]>([]);

  useEffect(() => {
    // Load available frameworks
    const loadFrameworks = async () => {
      try {
        const result = await api.getFrameworks();
        setFrameworks(result.frameworks);
      } catch (error) {
        console.error('Failed to load frameworks:', error);
        addNotification({
          type: 'error',
          title: 'Failed to Load Frameworks',
          message: 'Unable to load available frameworks. Please refresh the page.'
        });
      }
    };

    loadFrameworks();
  }, [addNotification]);

  useEffect(() => {
    // Set framework from current DSL if available
    if (currentDSL?.meta.framework) {
      setSelectedFramework(currentDSL.meta.framework);
    }
  }, [currentDSL]);

  const handleGenerate = async () => {
    if (!currentDSL) {
      toast.error('No DSL specification found. Please create one first.');
      navigate('/prompt');
      return;
    }

    setIsGenerating(true);
    
    try {
      const project = await api.generateCode(currentDSL, selectedFramework);
      setCurrentProject(project);
      addProject(project);
      toast.success('Code generated successfully!');
      addNotification({
        type: 'success',
        title: 'Code Generated',
        message: `${selectedFramework} project generated successfully with ${Object.keys(project.files).length} files.`
      });
    } catch (error) {
      console.error('Generation failed:', error);
      toast.error('Failed to generate code. Please try again.');
      addNotification({
        type: 'error',
        title: 'Generation Failed',
        message: 'Unable to generate code. Please check your DSL and try again.'
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async () => {
    if (!currentProject) return;

    try {
      const blob = await api.downloadProject(currentProject);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentProject.name}-${currentProject.framework}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Project downloaded successfully!');
      addNotification({
        type: 'success',
        title: 'Download Complete',
        message: `${currentProject.name} has been downloaded successfully.`
      });
    } catch (error) {
      console.error('Download failed:', error);
      toast.error('Failed to download project');
      addNotification({
        type: 'error',
        title: 'Download Failed',
        message: 'Unable to download project files. Please try again.'
      });
    }
  };

  const handleDeploy = () => {
    if (currentProject) {
      navigate('/deploy');
    } else {
      toast.error('Please generate code first');
    }
  };

  if (!currentDSL) {
    return (
      <div className="h-full bg-[#0a0a0a] text-white flex items-center justify-center">
        <div className="max-w-2xl text-center space-y-8">
          <div className="space-y-4">
            <AlertTriangle className="w-16 h-16 text-[#ffaa00] mx-auto" />
            <h1 className="text-4xl font-bold text-white">No DSL Specification</h1>
            <p className="text-gray-400">
              No DSL specification found. Please create one first using our AI prompt or visual builder.
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate('/prompt')}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black rounded-lg font-semibold transition-all hover:shadow-lg hover:shadow-[#00ff88]/25"
            >
              <span>Create from Prompt</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate('/builder')}
              className="flex items-center space-x-2 px-6 py-3 bg-[#1a1a1a] border border-[#333333] text-white rounded-lg font-semibold transition-all hover:bg-[#222222]"
            >
              <span>Use DSL Builder</span>
              <ArrowRight className="w-4 h-4" />
            </button>
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
          <h1 className="text-4xl font-bold text-white">Code Generator</h1>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Generate production-ready backend code from your DSL specification in your preferred framework.
          </p>
        </div>

        {/* Project Info */}
        <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white">{currentDSL.meta.name}</h2>
              <p className="text-gray-400">{currentDSL.meta.description}</p>
              <div className="flex items-center space-x-4 mt-2">
                <span className="px-2 py-1 bg-[#00ccff]/20 text-[#00ccff] rounded text-sm">
                  v{currentDSL.meta.version}
                </span>
                <span className="px-2 py-1 bg-[#1a1a1a] text-gray-300 rounded text-sm">
                  {Object.keys(currentDSL.models).length} models
                </span>
                <span className="px-2 py-1 bg-[#1a1a1a] text-gray-300 rounded text-sm">
                  {currentDSL.meta.database}
                </span>
              </div>
            </div>
            {currentProject && (
              <div className="flex items-center space-x-2 text-[#00ff88]">
                <CheckCircle className="w-5 h-5" />
                <span>Generated</span>
              </div>
            )}
          </div>
        </div>

        {/* Framework Selection */}
        <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Choose Your Framework</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {frameworks.map((framework) => (
              <button
                key={framework.id}
                onClick={() => setSelectedFramework(framework.id)}
                disabled={isGenerating}
                className={`p-6 rounded-lg border transition-all text-left ${
                  selectedFramework === framework.id
                    ? 'bg-[#00ff88]/10 border-[#00ff88] text-[#00ff88]'
                    : 'bg-[#1a1a1a] border-[#333333] text-gray-300 hover:bg-[#222222] hover:border-[#444444]'
                } ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <div className="space-y-3">
                  <div>
                    <h3 className="font-semibold text-lg">{framework.name}</h3>
                    <p className="text-sm text-gray-400">{framework.language}</p>
                  </div>
                  <p className="text-sm">{framework.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {framework.features?.map((feature: string, index: number) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-[#333333] text-xs rounded text-gray-300"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Generate Button */}
        <div className="text-center">
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black rounded-lg font-semibold transition-all mx-auto hover:shadow-lg hover:shadow-[#00ff88]/25 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Generating Code...</span>
              </>
            ) : (
              <>
                <Code className="w-5 h-5" />
                <span>Generate {frameworks.find(f => f.id === selectedFramework)?.name} Code</span>
              </>
            )}
          </button>
        </div>

        {/* Generated Code */}
        {currentProject && (
          <>
            <CodeEditor files={currentProject.files} />
            
            {/* Action Buttons */}
            <div className="flex justify-center space-x-4">
              <button
                onClick={handleDownload}
                className="flex items-center space-x-2 px-6 py-3 bg-[#1a1a1a] border border-[#333333] text-white rounded-lg font-semibold transition-all hover:bg-[#222222]"
              >
                <Download className="w-5 h-5" />
                <span>Download Project</span>
              </button>
              <button
                onClick={handleDeploy}
                className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-[#8b5cf6] to-[#a855f7] text-white rounded-lg font-semibold transition-all hover:shadow-lg hover:shadow-purple-500/25"
              >
                <Play className="w-5 h-5" />
                <span>Deploy Now</span>
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default CodeGenerator;
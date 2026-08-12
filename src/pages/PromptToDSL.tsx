import React, { useState } from 'react';
import {
  Send,
  Sparkles,
  Code,
  MessageSquare,
  CheckCircle,
  AlertCircle,
  Loader2,
  Save,
  Lightbulb
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api, DSLSpec, ValidationResult } from '../lib/api';
import { useProjectData, useUIState } from '../lib/store';

const PromptToDSL: React.FC = () => {
  const navigate = useNavigate();
  const { setCurrentDSL, setIsGenerating, isGenerating } = useProjectData();
  const { addNotification } = useUIState();
  const [prompt, setPrompt] = useState('');
  const [generatedDSL, setGeneratedDSL] = useState<DSLSpec | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [activeExample, setActiveExample] = useState<number | null>(null);

  const examples = [
    {
      title: 'Blog API',
      description: 'A complete blog system with posts, comments, and user management',
      prompt: 'Create a blog API with users, posts, and comments. Users can register, login, create posts, and comment on posts. Posts should have titles, content, and publication status. Include user authentication and proper permissions.'
    },
    {
      title: 'E-commerce Store',
      description: 'Online store with products, orders, and inventory management',
      prompt: 'Build an e-commerce API with products, categories, shopping cart, and orders. Include user authentication, product inventory, order tracking, and payment integration. Products should have images, prices, and stock levels.'
    },
    {
      title: 'Task Management',
      description: 'Project management system with tasks, teams, and deadlines',
      prompt: 'Create a task management API with projects, tasks, and team collaboration. Users can create projects, assign tasks to team members, set deadlines, and track progress. Include user roles, notifications, and file attachments.'
    },
    {
      title: 'Social Media Platform',
      description: 'Social network with posts, followers, and real-time messaging',
      prompt: 'Design a social media API with user profiles, posts, followers, and messaging. Users can create posts, follow other users, like and comment on posts, and send direct messages. Include real-time notifications and content moderation.'
    }
  ];

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a description for your backend');
      return;
    }

    setIsGenerating(true);
    
    try {
      const result = await api.parsePrompt(prompt);
      setGeneratedDSL(result.dsl);
      
      // Validate the generated DSL
      const validation = await api.validateDSL(result.dsl);
      setValidationResult(validation);
      
      if (validation.valid) {
        toast.success('DSL generated successfully!');
        addNotification({
          type: 'success',
          title: 'DSL Generated',
          message: 'Your backend specification has been created successfully.'
        });
        setCurrentDSL(result.dsl);
      } else {
        toast.error('Generated DSL has validation errors');
        addNotification({
          type: 'warning',
          title: 'Validation Issues',
          message: 'The generated DSL has some validation issues that need attention.'
        });
      }
    } catch (error) {
      console.error('Generation failed:', error);
      toast.error('Failed to generate DSL. Please try again.');
      addNotification({
        type: 'error',
        title: 'Generation Failed',
        message: 'Unable to generate DSL specification. Please check your connection and try again.'
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExampleClick = (example: typeof examples[0], index: number) => {
    setActiveExample(index);
    setPrompt(example.prompt);
    setTimeout(() => setActiveExample(null), 2000);
  };

  const handleSaveAndContinue = () => {
    if (generatedDSL) {
      setCurrentDSL(generatedDSL);
      navigate('/builder');
    }
  };

  const handleGenerateCode = () => {
    if (generatedDSL) {
      setCurrentDSL(generatedDSL);
      navigate('/generate');
    }
  };

  return (
    <div className="h-full bg-[#0a0a0a] text-white overflow-auto">
      <div className="max-w-7xl mx-auto p-8 space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-white">
            Describe Your Backend
          </h1>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Tell us what you want to build in plain English, and our AI will generate a complete DSL specification for your backend service.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Input Section */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
              <div className="flex items-center space-x-3 mb-4">
                <MessageSquare className="w-6 h-6 text-[#00ff88]" />
                <h2 className="text-xl font-semibold text-white">Describe Your Backend</h2>
              </div>
              
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Example: Create a blog API with users, posts, and comments. Users can register, login, create posts, and comment on posts. Posts should have titles, content, and publication status. Include user authentication and proper permissions."
                className="w-full h-40 p-4 bg-[#1a1a1a] border border-[#333333] text-white rounded-lg focus:border-[#00ff88] focus:outline-none resize-none placeholder-gray-500"
                disabled={isGenerating}
              />
              
              <div className="flex items-center justify-between mt-4">
                <span className="text-sm text-gray-400">
                  {prompt.length}/1000 characters
                </span>
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating || !prompt.trim()}
                  className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-[#00ff88]/25"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      <span>Generate DSL</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Generated DSL */}
            {generatedDSL && (
              <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <Code className="w-6 h-6 text-[#00ff88]" />
                    <h2 className="text-xl font-semibold text-white">Generated DSL</h2>
                    {validationResult?.valid ? (
                      <CheckCircle className="w-5 h-5 text-[#00ff88]" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-[#ff4444]" />
                    )}
                  </div>
                  <button
                    onClick={handleSaveAndContinue}
                    className="flex items-center space-x-2 px-4 py-2 bg-[#1a1a1a] border border-[#333333] text-white rounded-lg font-semibold transition-all hover:bg-[#222222]"
                  >
                    <Save className="w-4 h-4" />
                    <span>Edit in Builder</span>
                  </button>
                </div>
                
                <pre className="bg-[#0f0f0f] border border-[#222222] p-4 rounded-lg text-[#00ff88] text-sm overflow-x-auto max-h-96 font-mono">
                  {JSON.stringify(generatedDSL, null, 2)}
                </pre>
                
                {/* Validation Results */}
                {validationResult && (
                  <div className="mt-4 space-y-2">
                    {validationResult.errors?.map((error: string, index: number) => (
                      <div key={index} className="flex items-center space-x-2 p-2 bg-[#ff4444]/10 border border-[#ff4444]/20 rounded text-[#ff4444]">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm">{error}</span>
                      </div>
                    ))}
                    {validationResult.warnings?.map((warning: string, index: number) => (
                      <div key={index} className="flex items-center space-x-2 p-2 bg-[#ffaa00]/10 border border-[#ffaa00]/20 rounded text-[#ffaa00]">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm">{warning}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="flex items-center justify-between mt-4">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      {validationResult?.valid ? (
                        <CheckCircle className="w-4 h-4 text-[#00ff88]" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-[#ff4444]" />
                      )}
                      <span className="text-sm text-gray-300">
                        {validationResult?.valid ? 'Valid DSL' : 'Has Errors'}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-[#00ccff]" />
                      <span className="text-sm text-gray-300">{generatedDSL.meta.framework} Ready</span>
                    </div>
                  </div>
                  <button
                    onClick={handleGenerateCode}
                    disabled={!validationResult?.valid}
                    className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-[#00ff88]/25"
                  >
                    <span>Generate Code</span>
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Examples Sidebar */}
          <div className="space-y-6">
            <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Example Prompts</h3>
              <div className="space-y-3">
                {examples.map((example, index) => (
                  <button
                    key={index}
                    onClick={() => handleExampleClick(example, index)}
                    disabled={isGenerating}
                    className={`w-full p-4 text-left rounded-lg border transition-all ${
                      activeExample === index
                        ? 'bg-[#00ff88]/10 border-[#00ff88] text-[#00ff88]'
                        : 'bg-[#1a1a1a] border-[#333333] text-gray-300 hover:bg-[#222222] hover:border-[#444444]'
                    } ${isGenerating ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <div className="font-medium mb-1">{example.title}</div>
                    <div className="text-sm text-gray-400">{example.description}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-[#111111] border border-[#333333] rounded-lg p-6">
              <div className="flex items-center space-x-3 mb-4">
                <Lightbulb className="w-5 h-5 text-[#ffaa00]" />
                <h3 className="text-lg font-semibold text-white">Tips</h3>
              </div>
              <ul className="space-y-2 text-sm text-gray-300">
                <li>• Be specific about your data models and relationships</li>
                <li>• Mention authentication and permission requirements</li>
                <li>• Include any special features or integrations needed</li>
                <li>• Describe the expected API endpoints and functionality</li>
                <li>• Consider scalability and performance requirements</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PromptToDSL;
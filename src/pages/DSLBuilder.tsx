import React, { useState, useEffect } from 'react';
import {
  Save,
  Code,
  ArrowRight,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import DSLEditor from '../components/DSLEditor';
import { api, DSLSpec, ValidationResult } from '../lib/api';
import { useProjectData, useUIState } from '../lib/store';

const DSLBuilder: React.FC = () => {
  const navigate = useNavigate();
  const { currentDSL, setCurrentDSL } = useProjectData();
  const { addNotification } = useUIState();
  const [dsl, setDSL] = useState<DSLSpec>(currentDSL || {
    meta: {
      name: 'my-api',
      description: 'Generated API',
      version: '1.0.0',
      framework: 'django',
      database: 'postgresql'
    },
    auth: {
      provider: 'jwt',
      user_model: 'User',
      required_fields: ['email', 'password']
    },
    models: {
      User: {
        fields: {
          id: { type: 'uuid', primary_key: true, auto_generated: true },
          email: { type: 'string', unique: true, required: true },
          password: { type: 'string', required: true, hashed: true }
        }
      }
    },
    api: {
      base_path: '/api/v1',
      endpoints: []
    }
  });
  
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (currentDSL) {
      setDSL(currentDSL);
    }
  }, [currentDSL]);

  useEffect(() => {
    // Validate DSL whenever it changes
    const validateDSL = async () => {
      try {
        const result = await api.validateDSL(dsl);
        setValidationResult(result);
      } catch (error) {
        console.error('Validation failed:', error);
      }
    };

    const timeoutId = setTimeout(validateDSL, 500);
    return () => clearTimeout(timeoutId);
  }, [dsl]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Validate first
      const validation = await api.validateDSL(dsl);
      if (!validation.valid) {
        toast.error('Please fix validation errors before saving');
        addNotification({
          type: 'error',
          title: 'Validation Failed',
          message: 'Please fix all validation errors before saving the DSL.'
        });
        return;
      }

      setCurrentDSL(dsl);
      toast.success('DSL saved successfully!');
      addNotification({
        type: 'success',
        title: 'DSL Saved',
        message: 'Your backend specification has been saved successfully.'
      });
    } catch (error) {
      console.error('Save failed:', error);
      toast.error('Failed to save DSL');
      addNotification({
        type: 'error',
        title: 'Save Failed',
        message: 'Unable to save DSL specification. Please try again.'
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerateCode = () => {
    if (validationResult?.valid) {
      setCurrentDSL(dsl);
      navigate('/generate');
    } else {
      toast.error('Please fix validation errors before generating code');
      addNotification({
        type: 'warning',
        title: 'Validation Required',
        message: 'Please fix all validation errors before proceeding to code generation.'
      });
    }
  };

  return (
    <div className="h-full bg-[#0a0a0a] text-white overflow-auto">
      <div className="max-w-7xl mx-auto p-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white">DSL Builder</h1>
            <p className="text-gray-400 mt-2">
              Use our visual builder to create and customize your backend specification with precision.
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Validation Status */}
            <div className="flex items-center space-x-2">
              {validationResult?.valid ? (
                <>
                  <CheckCircle className="w-5 h-5 text-[#00ff88]" />
                  <span className="text-[#00ff88] font-medium">Valid</span>
                </>
              ) : validationResult ? (
                <>
                  <AlertCircle className="w-5 h-5 text-[#ff4444]" />
                  <span className="text-[#ff4444] font-medium">
                    {validationResult.errors?.length || 0} errors
                  </span>
                </>
              ) : (
                <>
                  <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                  <span className="text-gray-400">Validating...</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* DSL Editor */}
        <DSLEditor dsl={dsl} onChange={setDSL} />

        {/* Action Buttons */}
        <div className="flex justify-center space-x-4">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center space-x-2 px-6 py-3 bg-[#1a1a1a] border border-[#333333] text-white rounded-lg font-semibold transition-all hover:bg-[#222222] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-5 h-5" />
            <span>{isSaving ? 'Saving...' : 'Save Project'}</span>
          </button>
          
          <button
            onClick={handleGenerateCode}
            disabled={!validationResult?.valid}
            className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black rounded-lg font-semibold transition-all hover:shadow-lg hover:shadow-[#00ff88]/25 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Code className="w-5 h-5" />
            <span>Generate Code</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default DSLBuilder;
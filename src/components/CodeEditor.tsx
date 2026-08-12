import React, { useState } from 'react';
import {
  FileText,
  Folder,
  FolderOpen,
  Copy,
  Check,
  Code
} from 'lucide-react';
import { useProjectData } from '../lib/store';

interface FileTreeProps {
  files: Record<string, string>;
  onFileSelect: (path: string) => void;
  selectedFile: string | null;
}

type FileTreeNode =
  | { type: 'file'; path: string }
  | { type: 'folder'; children: Record<string, FileTreeNode> };

const FileTree: React.FC<FileTreeProps> = ({ files, onFileSelect, selectedFile }) => {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['']));

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const buildFileTree = (files: Record<string, string>): Record<string, FileTreeNode> => {
    const tree: Record<string, FileTreeNode> = {};

    Object.keys(files).forEach(filePath => {
      const parts = filePath.split('/');
      let current = tree;

      parts.forEach((part, index) => {
        if (index === parts.length - 1) {
          // It's a file
          current[part] = { type: 'file', path: filePath };
        } else {
          // It's a folder
          let node = current[part];
          if (!node || node.type !== 'folder') {
            node = { type: 'folder', children: {} };
            current[part] = node;
          }
          current = node.children;
        }
      });
    });

    return tree;
  };

  const renderTree = (tree: Record<string, FileTreeNode>, currentPath = '', level = 0) => {
    return Object.entries(tree).map(([name, node]) => {
      const fullPath = currentPath ? `${currentPath}/${name}` : name;
      const isExpanded = expandedFolders.has(fullPath);
      
      if (node.type === 'folder') {
        return (
          <div key={fullPath}>
            <div
              className={`flex items-center space-x-2 p-2 cursor-pointer hover:bg-[#1a1a1a] rounded transition-colors`}
              style={{ paddingLeft: `${level * 16 + 8}px` }}
              onClick={() => toggleFolder(fullPath)}
            >
              {isExpanded ? (
                <FolderOpen className="w-4 h-4 text-[#00ccff]" />
              ) : (
                <Folder className="w-4 h-4 text-[#00ccff]" />
              )}
              <span className="text-sm text-gray-300">{name}</span>
            </div>
            {isExpanded && (
              <div>
                {renderTree(node.children, fullPath, level + 1)}
              </div>
            )}
          </div>
        );
      } else {
        return (
          <div
            key={fullPath}
            className={`flex items-center space-x-2 p-2 cursor-pointer rounded transition-colors ${
              selectedFile === node.path
                ? 'bg-[#00ff88]/10 text-[#00ff88] border border-[#00ff88]/20'
                : 'text-gray-300 hover:bg-[#1a1a1a]'
            }`}
            style={{ paddingLeft: `${level * 16 + 8}px` }}
            onClick={() => onFileSelect(node.path)}
          >
            <FileText className="w-4 h-4 text-gray-400" />
            <span className="text-sm">{name}</span>
          </div>
        );
      }
    });
  };

  const fileTree = buildFileTree(files);

  return (
    <div className="space-y-1">
      {renderTree(fileTree)}
    </div>
  );
};

interface CodeEditorProps {
  files: Record<string, string>;
  className?: string;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ files, className = '' }) => {
  const { activeFile, setActiveFile } = useProjectData();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (activeFile && files[activeFile]) {
      await navigator.clipboard.writeText(files[activeFile]);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getLanguage = (filePath: string) => {
    const ext = filePath.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'py': return 'python';
      case 'js': case 'ts': return 'javascript';
      case 'go': return 'go';
      case 'rb': return 'ruby';
      case 'yml': case 'yaml': return 'yaml';
      case 'json': return 'json';
      case 'sql': return 'sql';
      case 'md': return 'markdown';
      default: return 'text';
    }
  };

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-4 gap-6 ${className}`}>
      {/* File Explorer */}
      <div className="bg-[#111111] border border-[#333333] p-4 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Folder className="w-5 h-5 text-[#00ccff]" />
            <h3 className="font-semibold text-white">Project Files</h3>
          </div>
          <span className="text-xs text-gray-400">{Object.keys(files).length} files</span>
        </div>
        <FileTree 
          files={files} 
          onFileSelect={setActiveFile} 
          selectedFile={activeFile} 
        />
      </div>

      {/* Code Viewer */}
      <div className="lg:col-span-3 bg-[#111111] border border-[#333333] p-4 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Code className="w-5 h-5 text-[#00ccff]" />
            <h3 className="font-semibold text-white">
              {activeFile || 'Select a file'}
            </h3>
            {activeFile && (
              <span className="px-2 py-1 bg-[#333333] text-xs rounded text-gray-300">
                {getLanguage(activeFile)}
              </span>
            )}
          </div>
          {activeFile && (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleCopy}
                className="p-2 bg-[#1a1a1a] border border-[#333333] hover:bg-[#222222] text-white rounded-lg transition-colors"
                title="Copy to clipboard"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-[#00ff88]" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          )}
        </div>
        
        <div className="bg-[#0f0f0f] border border-[#222222] p-4 rounded-lg h-96 overflow-auto">
          {activeFile && files[activeFile] ? (
            <pre className="text-sm">
              <code className={`language-${getLanguage(activeFile)} text-[#00ff88] font-mono`}>
                {files[activeFile]}
              </code>
            </pre>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Select a file to view its content</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CodeEditor;
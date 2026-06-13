/**
 * Main App component — top-level layout for the workflow automation platform.
 */
import React, { useEffect, useCallback } from 'react';
import { ReactFlowProvider } from 'reactflow';
import { Toaster } from 'react-hot-toast';

import NodePanel from './components/NodePanel';
import WorkflowCanvas from './components/WorkflowCanvas';
import ConfigDrawer from './components/ConfigDrawer';
import LogConsole from './components/LogConsole';
import { useWorkflowStore } from './stores/workflowStore';

export default function App() {
  const fetchNodeTypes = useWorkflowStore((s) => s.fetchNodeTypes);
  const selectedNode = useWorkflowStore((s) => s.selectedNode);
  const workflowName = useWorkflowStore((s) => s.workflowName);
  const setWorkflowInfo = useWorkflowStore((s) => s.setWorkflowInfo);
  const unsavedChanges = useWorkflowStore((s) => s.unsavedChanges);
  const addNode = useWorkflowStore((s) => s.addNode);

  // Fetch executor types on mount
  useEffect(() => {
    fetchNodeTypes();
  }, [fetchNodeTypes]);

  // Listen for "panel-add-node" events (click-to-add from NodePanel)
  useEffect(() => {
    const handler = (e) => {
      addNode(e.detail.type, { x: 300 + Math.random() * 100, y: 200 + Math.random() * 100 });
    };
    window.addEventListener('panel-add-node', handler);
    return () => window.removeEventListener('panel-add-node', handler);
  }, [addNode]);

  // Warn before close if unsaved changes
  useEffect(() => {
    const handler = (e) => {
      if (unsavedChanges) {
        e.preventDefault();
        e.returnValue = '您有未保存的更改，确定离开吗？';
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [unsavedChanges]);

  const handleNameChange = useCallback(
    (e) => setWorkflowInfo(e.target.value),
    [setWorkflowInfo]
  );

  return (
    <ReactFlowProvider>
      <div className="h-full flex flex-col bg-[#111118]">
        {/* Top bar */}
        <header className="h-11 bg-surface border-b border-gray-700/50 flex items-center px-4 shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-lg">🔄</span>
            <span className="text-sm font-semibold text-gray-200">
              拖拽式工作流自动化平台
            </span>
          </div>
          <div className="mx-4 w-px h-5 bg-gray-700" />
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={workflowName}
              onChange={handleNameChange}
              className="bg-transparent border-b border-transparent hover:border-gray-600 focus:border-blue-500 text-sm text-gray-200 px-1 py-0.5 outline-none w-48 transition-colors"
              placeholder="工作流名称"
            />
            {unsavedChanges && (
              <span className="text-[10px] text-yellow-500 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                未保存
              </span>
            )}
          </div>
        </header>

        {/* Main content */}
        <div className="flex-1 flex overflow-hidden">
          <NodePanel />
          <WorkflowCanvas />
          {selectedNode && <ConfigDrawer />}
        </div>

        {/* Bottom log console */}
        <LogConsole />

        {/* Toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1e1e2e',
              color: '#e5e7eb',
              border: '1px solid #374151',
              fontSize: '13px',
            },
            duration: 3000,
          }}
        />
      </div>
    </ReactFlowProvider>
  );
}

/**
 * Main workflow canvas component using React Flow.
 */
import React, { useRef, useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Controls,
  Background,
  MiniMap,
  BackgroundVariant,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Sparkles as SparklesIcon } from 'lucide-react';

import WorkflowNode from './WorkflowNode';
import AIWorkflowGenerator from '../AIWorkflowGenerator';
import { useWorkflowStore } from '../../stores/workflowStore';

const nodeTypes = { workflowNode: WorkflowNode };

const miniMapStyle = {
  height: 120,
  backgroundColor: '#1e1e2e',
  maskColor: 'rgba(0,0,0,0.4)',
};

export default function WorkflowCanvas() {
  const reactFlowWrapper = useRef(null);
  const { screenToFlowPosition } = useReactFlow();

  const nodes = useWorkflowStore((s) => s.nodes);
  const edges = useWorkflowStore((s) => s.edges);
  const isRunning = useWorkflowStore((s) => s.isRunning);
  const selectedNode = useWorkflowStore((s) => s.selectedNode);
  const onNodesChange = useWorkflowStore((s) => s.onNodesChange);
  const onEdgesChange = useWorkflowStore((s) => s.onEdgesChange);
  const onConnect = useWorkflowStore((s) => s.onConnect);
  const addNode = useWorkflowStore((s) => s.addNode);
  const setSelectedNode = useWorkflowStore((s) => s.setSelectedNode);
  const removeNodes = useWorkflowStore((s) => s.removeNodes);
  const duplicateNode = useWorkflowStore((s) => s.duplicateNode);
  const autoLayout = useWorkflowStore((s) => s.autoLayout);
  const saveWorkflow = useWorkflowStore((s) => s.saveWorkflow);
  const executeWorkflow = useWorkflowStore((s) => s.executeWorkflow);
  const resetWorkflow = useWorkflowStore((s) => s.resetWorkflow);
  const loadWorkflow = useWorkflowStore((s) => s.loadWorkflow);
  const fetchWorkflowList = useWorkflowStore((s) => s.fetchWorkflowList);
  const workflowList = useWorkflowStore((s) => s.workflowList);
  const deleteWorkflow = useWorkflowStore((s) => s.deleteWorkflow);
  const previewEdge = useWorkflowStore((s) => s.previewEdge);
  const setPreviewEdge = useWorkflowStore((s) => s.setPreviewEdge);
  const clearPreview = useWorkflowStore((s) => s.clearPreview);
  const isSaving = useWorkflowStore((s) => s.isSaving);
  const [showAIModal, setShowAIModal] = useState(false);
  const [selectedWfId, setSelectedWfId] = useState('');

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveWorkflow();
      }
      if (e.key === 'Delete' || e.key === 'Backspace') {
        // Don't delete if editing an input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        const selectedNodes = nodes.filter((n) => n.selected);
        if (selectedNodes.length > 0) {
          removeNodes(selectedNodes.map((n) => n.id));
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [nodes, saveWorkflow, removeNodes]);

  // Fetch workflow list on mount
  useEffect(() => { fetchWorkflowList(); }, [fetchWorkflowList]);

  // Listen for node label edits
  useEffect(() => {
    const handler = (e) => {
      useWorkflowStore.getState().updateNodeLabel(e.detail.nodeId, e.detail.label);
    };
    window.addEventListener('node-label-edit', handler);
    return () => window.removeEventListener('node-label-edit', handler);
  }, []);

  // Drag & drop from node panel
  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const nodeType = event.dataTransfer.getData('application/reactflow-type');
      if (!nodeType) return;

      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      addNode(nodeType, position);
    },
    [screenToFlowPosition, addNode]
  );

  // Node click -> select for config
  const onNodeClick = useCallback(
    (_, node) => {
      setSelectedNode(node);
    },
    [setSelectedNode]
  );

  // Context menu
  const onNodeContextMenu = useCallback(
    (event, node) => {
      event.preventDefault();
      // Use a simple approach: browser confirm for actions
      const action = window.prompt(
        `节点操作:\n1. 复制节点\n2. 删除节点\n输入数字选择:`,
        ''
      );
      if (action === '1') duplicateNode(node.id);
      if (action === '2') removeNodes([node.id]);
    },
    [duplicateNode, removeNodes]
  );

  return (
    <div className="flex-1 flex flex-col h-full" ref={reactFlowWrapper}>
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 bg-surface border-b border-gray-700/50">
        <button
          onClick={() => setShowAIModal(true)}
          className="px-3 py-1.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white text-sm rounded-lg flex items-center gap-1.5 transition-all font-medium shadow-lg shadow-purple-600/20"
        >
          <SparklesIcon size={14} />
          AI 生成
        </button>
        <div className="w-px h-6 bg-gray-600" />
        <button
          onClick={saveWorkflow}
          disabled={isSaving}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded-lg flex items-center gap-1.5 transition-colors"
        >
          {isSaving ? '保存中...' : '💾 保存'}
        </button>
        <select
          value={selectedWfId}
          onChange={(e) => {
            const val = e.target.value;
            setSelectedWfId(val);
            if (val) loadWorkflow(Number(val));
          }}
          className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg cursor-pointer outline-none transition-colors"
          style={{ minWidth: 150 }}
        >
          <option value="">📂 加载工作流 ▾</option>
          {workflowList.map((w) => (
            <option key={w.id} value={w.id} className="bg-surface-light text-white">
              {w.name} (ID:{w.id})
            </option>
          ))}
        </select>
        <button
          onClick={fetchWorkflowList}
          className="px-2 py-1.5 bg-surface-light hover:bg-gray-700 text-gray-400 hover:text-gray-200 text-xs rounded-lg transition-colors"
          title="刷新列表"
        >
          🔄
        </button>
        <button
          onClick={() => {
            if (selectedWfId && confirm('确定要删除该工作流吗？此操作不可恢复。')) {
              deleteWorkflow(Number(selectedWfId));
              setSelectedWfId('');
            }
          }}
          disabled={!selectedWfId}
          className="px-2 py-1.5 bg-red-600/30 hover:bg-red-600/60 disabled:opacity-20 disabled:cursor-not-allowed text-red-300 text-xs rounded-lg transition-colors"
          title="删除选中工作流"
        >
          🗑️
        </button>
        <button
          onClick={executeWorkflow}
          disabled={isRunning || nodes.length === 0}
          className="px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm rounded-lg flex items-center gap-1.5 transition-colors"
        >
          {isRunning ? '⏳ 执行中...' : '▶️ 执行'}
        </button>
        <div className="w-px h-6 bg-gray-600" />
        <button
          onClick={autoLayout}
          disabled={nodes.length === 0}
          className="px-3 py-1.5 bg-surface-light hover:bg-gray-700 disabled:opacity-50 text-gray-200 text-sm rounded-lg flex items-center gap-1.5 transition-colors"
        >
          📐 自动布局
        </button>
        <button
          onClick={resetWorkflow}
          className="px-3 py-1.5 bg-surface-light hover:bg-gray-700 text-gray-200 text-sm rounded-lg flex items-center gap-1.5 transition-colors"
        >
          🗑️ 清空
        </button>
        <div className="flex-1" />
        <span className="text-xs text-gray-500">
          {nodes.length} 节点 | {edges.length} 连线
        </span>
      </div>

      {/* Canvas */}
      <div className="flex-1">
        {(() => {
          // Highlight preview edge
          const styledEdges = edges.map((e) =>
            e.id === previewEdge
              ? { ...e, style: { stroke: '#6366F1', strokeWidth: 3 }, animated: true }
              : e
          );
          return (
        <ReactFlow
          nodes={nodes}
          edges={styledEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onNodeContextMenu={onNodeContextMenu}
          onEdgeClick={(_, edge) => {
            const sourceNode = nodes.find((n) => n.id === edge.source);
            const targetNode = nodes.find((n) => n.id === edge.target);
            setPreviewEdge(edge.id, {
              source: { id: edge.source, type: sourceNode?.data?.nodeType, label: sourceNode?.data?.label },
              target: { id: edge.target, type: targetNode?.data?.nodeType, label: targetNode?.data?.label },
              sourceConfig: sourceNode?.data?.config || {},
            });
          }}
          onPaneClick={() => { setSelectedNode(null); clearPreview(); }}
          onDragOver={onDragOver}
          onDrop={onDrop}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          minZoom={0.2}
          maxZoom={2}
          snapToGrid
          snapGrid={[20, 20]}
          deleteKeyCode={['Delete', 'Backspace']}
          multiSelectionKeyCode="Shift"
          className="bg-[#111118]"
          defaultEdgeOptions={{
            type: 'smoothstep',
            animated: true,
            style: { stroke: '#555', strokeWidth: 2 },
            markerEnd: { type: 'arrowclosed', color: '#555' },
          }}
        >
          <Controls className="!bg-surface !border-gray-700 !rounded-lg" />
          <MiniMap
            style={miniMapStyle}
            nodeColor={(node) => node.data?.color || '#6B7280'}
            maskColor="rgba(0,0,0,0.5)"
            className="!rounded-lg"
          />
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#222" />
        </ReactFlow>
          );
        })()}
      </div>

      {/* Data Preview Popup */}
      {previewEdge && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30 bg-surface border border-gray-600 rounded-xl shadow-2xl p-4 min-w-[320px] max-w-[500px] drawer-enter">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-blue-400">🔗 数据流预览</span>
            <button onClick={clearPreview} className="text-gray-500 hover:text-gray-300 text-xs">✕</button>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
            <span className="px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded font-mono text-[10px]">
              {useWorkflowStore.getState().previewData?.source?.label || 'source'}
            </span>
            <span className="text-gray-600">→</span>
            <span className="px-2 py-0.5 bg-green-500/20 text-green-300 rounded font-mono text-[10px]">
              {useWorkflowStore.getState().previewData?.target?.label || 'target'}
            </span>
          </div>
          <div className="bg-gray-900 rounded-lg p-2 max-h-[160px] overflow-y-auto">
            <pre className="text-[10px] text-gray-300 font-mono whitespace-pre-wrap break-all">
              {JSON.stringify(useWorkflowStore.getState().previewData?.sourceConfig || {}, null, 1).substring(0, 800)}
            </pre>
          </div>
          <p className="text-[9px] text-gray-600 mt-2">
            💡 执行后可查看实际数据流。点击画布空白处关闭。
          </p>
        </div>
      )}

      {/* AI Workflow Generator Modal */}
      <AIWorkflowGenerator
        isOpen={showAIModal}
        onClose={() => setShowAIModal(false)}
      />
    </div>
  );
}

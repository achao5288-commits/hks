/**
 * Zustand store for workflow state management.
 */
import { create } from 'zustand';
import {
  addEdge as rfAddEdge,
  applyNodeChanges,
  applyEdgeChanges,
  MarkerType,
} from 'reactflow';
import toast from 'react-hot-toast';
import {
  saveWorkflow as apiSaveWorkflow,
  getWorkflow as apiGetWorkflow,
  getWorkflows as apiGetWorkflows,
  deleteWorkflow as apiDeleteWorkflow,
  executeWorkflow as apiExecuteWorkflow,
  getTaskStatus,
  getExecutors,
} from '../api/client';
import { createLogSocket } from '../api/client';

let idCounter = 0;
const genId = (prefix = 'node') => `${prefix}_${Date.now()}_${++idCounter}`;

const NODE_DEFAULTS = {
  web_crawler: { label: '网页抓取', icon: 'Globe', color: '#3B82F6' },
  rss_monitor: { label: 'RSS监控', icon: 'Rss', color: '#F97316' },
  data_process: { label: '数据清洗', icon: 'Filter', color: '#22C55E' },
  excel_chart: { label: 'Excel生成', icon: 'FileSpreadsheet', color: '#EAB308' },
  email_sender: { label: '邮件发送', icon: 'Mail', color: '#EF4444' },
  schedule_trigger: { label: '定时触发', icon: 'Clock', color: '#8B5CF6' },
};

export const useWorkflowStore = create((set, get) => ({
  // ---- State ----
  nodes: [],
  edges: [],
  selectedNode: null,
  workflowName: '未命名工作流',
  workflowDescription: '',
  workflowId: null,
  isRunning: false,
  isSaving: false,
  taskId: null,
  logs: [],
  nodeTypes: [],     // from backend
  configSchemas: {}, // typename -> JSON Schema
  presetConfigs: [],
  wsConnection: null,
  unsavedChanges: false,
  workflowList: [],  // all saved workflows for the load dropdown

  // ---- Workflow List ----

  fetchWorkflowList: async () => {
    try {
      const data = await apiGetWorkflows();
      set({ workflowList: data || [] });
    } catch (err) {
      console.error('Failed to fetch workflow list:', err);
    }
  },

  deleteWorkflow: async (id) => {
    try {
      await apiDeleteWorkflow(id);
      toast.success('工作流已删除');
      // Refresh list
      const data = await apiGetWorkflows();
      set({ workflowList: data || [] });
    } catch (err) {
      toast.error(`删除失败: ${err.message}`);
    }
  },

  // ---- Node Actions ----

  addNode: (type, position) => {
    const info = NODE_DEFAULTS[type] || { label: type, icon: 'Box', color: '#6B7280' };
    const schemas = get().configSchemas;
    const schema = schemas[type] || {};

    // Build default config from schema
    const defaultConfig = {};
    if (schema.properties) {
      for (const [key, prop] of Object.entries(schema.properties)) {
        if (prop.default !== undefined) {
          defaultConfig[key] = prop.default;
        }
      }
    }

    const newNode = {
      id: genId('node'),
      type: 'workflowNode',
      position: position || { x: 250, y: 150 },
      data: {
        nodeType: type,
        label: info.label,
        icon: info.icon,
        color: info.color,
        config: defaultConfig,
        status: 'pending',
      },
    };

    set((s) => ({ nodes: [...s.nodes, newNode], unsavedChanges: true }));
    toast.success(`已添加节点: ${info.label}`);
  },

  updateNodeConfig: (nodeId, config) => {
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === nodeId
          ? { ...n, data: { ...n.data, config } }
          : n
      ),
      unsavedChanges: true,
    }));
  },

  updateNodeLabel: (nodeId, label) => {
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === nodeId
          ? { ...n, data: { ...n.data, label } }
          : n
      ),
      unsavedChanges: true,
    }));
  },

  removeNodes: (nodeIds) => {
    set((s) => ({
      nodes: s.nodes.filter((n) => !nodeIds.includes(n.id)),
      edges: s.edges.filter((e) => !nodeIds.includes(e.source) && !nodeIds.includes(e.target)),
      selectedNode: nodeIds.includes(s.selectedNode?.id) ? null : s.selectedNode,
      unsavedChanges: true,
    }));
    toast.success(`已删除 ${nodeIds.length} 个节点`);
  },

  duplicateNode: (nodeId) => {
    const node = get().nodes.find((n) => n.id === nodeId);
    if (!node) return;
    const newNode = {
      ...node,
      id: genId('node'),
      position: { x: node.position.x + 50, y: node.position.y + 50 },
      data: { ...node.data, config: { ...node.data.config }, status: 'pending' },
      selected: false,
    };
    set((s) => ({ nodes: [...s.nodes, newNode], unsavedChanges: true }));
    toast.success('节点已复制');
  },

  // ---- Edge Actions ----

  addEdge: (source, target) => {
    const { edges, nodes } = get();
    const sourceNode = nodes.find((n) => n.id === source);
    const targetNode = nodes.find((n) => n.id === target);

    if (!sourceNode || !targetNode) return false;
    if (source === target) {
      toast.error('不允许自环连线');
      return false;
    }
    if (edges.some((e) => e.source === source && e.target === target)) {
      toast.error('不允许重复连线');
      return false;
    }

    const newEdge = {
      id: genId('edge'),
      source,
      target,
      type: 'smoothstep',
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed, color: '#555' },
    };

    set((s) => ({ edges: [...s.edges, newEdge], unsavedChanges: true }));
    return true;
  },

  removeEdges: (edgeIds) => {
    set((s) => ({
      edges: s.edges.filter((e) => !edgeIds.includes(e.id)),
      unsavedChanges: true,
    }));
  },

  // ---- Selection ----

  setSelectedNode: (node) => {
    set({ selectedNode: node });
  },

  setWorkflowInfo: (name, description) => {
    set({ workflowName: name, workflowDescription: description || '', unsavedChanges: true });
  },

  // ---- React Flow Callbacks ----

  onNodesChange: (changes) => {
    set((s) => ({ nodes: applyNodeChanges(changes, s.nodes) }));
  },

  onEdgesChange: (changes) => {
    set((s) => ({ edges: applyEdgeChanges(changes, s.edges) }));
  },

  onConnect: (connection) => {
    const { source, target } = connection;
    if (source && target) {
      get().addEdge(source, target);
    }
  },

  // ---- Persistence ----

  saveWorkflow: async () => {
    const { workflowName, workflowDescription, nodes, edges, workflowId } = get();
    set({ isSaving: true });
    try {
      const nodePayload = nodes.map((n) => ({
        id: n.id,
        type: n.data.nodeType,
        config: n.data.config || {},
        position: { x: n.position.x, y: n.position.y },
      }));
      const edgePayload = edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
      }));

      const result = await apiSaveWorkflow(workflowName, workflowDescription, nodePayload, edgePayload);
      set({ workflowId: result.id, unsavedChanges: false, isSaving: false });
      toast.success('工作流已保存');
    } catch (err) {
      set({ isSaving: false });
      toast.error(`保存失败: ${err.message}`);
    }
  },

  loadWorkflow: async (id) => {
    try {
      const data = await apiGetWorkflow(id);
      const nodesJson = JSON.parse(data.nodes_json || '[]');
      const edgesJson = JSON.parse(data.edges_json || '[]');

      const nodes = nodesJson.map((n) => {
        const info = NODE_DEFAULTS[n.type] || { label: n.type, icon: 'Box', color: '#6B7280' };
        return {
          id: n.id,
          type: 'workflowNode',
          position: n.position || { x: 0, y: 0 },
          data: {
            nodeType: n.type,
            label: info.label,
            icon: info.icon,
            color: info.color,
            config: n.config || {},
            status: 'pending',
          },
        };
      });

      const edges = edgesJson.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: 'smoothstep',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#555' },
      }));

      set({
        nodes,
        edges,
        workflowName: data.name,
        workflowDescription: data.description || '',
        workflowId: data.id,
        unsavedChanges: false,
      });
      toast.success(`已加载工作流: ${data.name}`);
    } catch (err) {
      toast.error(`加载失败: ${err.message}`);
    }
  },

  // ---- Execution ----

  executeWorkflow: async () => {
    const { workflowId, nodes, edges } = get();
    let wfId = workflowId;

    // Auto-save if not saved
    if (!wfId) {
      await get().saveWorkflow();
      wfId = get().workflowId;
      if (!wfId) {
        toast.error('请先保存工作流');
        return;
      }
    }

    set({ isRunning: true, logs: [] });

    // Reset node statuses
    set((s) => ({
      nodes: s.nodes.map((n) => ({
        ...n,
        data: { ...n.data, status: 'pending' },
      })),
    }));

    try {
      const result = await apiExecuteWorkflow(wfId);
      const taskId = result.task_id;
      set({ taskId, isRunning: true });

      // Connect WebSocket for logs
      const ws = createLogSocket(
        taskId,
        (logEntry) => {
          set((s) => ({ logs: [...s.logs, logEntry] }));
          // Update node status based on log
          if (logEntry.node_id && logEntry.node_id !== 'engine') {
            set((s) => ({
              nodes: s.nodes.map((n) =>
                n.id === logEntry.node_id
                  ? { ...n, data: { ...n.data, status: logEntry.level === 'error' ? 'failed' : logEntry.level === 'info' ? 'running' : n.data.status } }
                  : n
              ),
            }));
          }
        },
        () => {
          // WebSocket closed
        }
      );
      set({ wsConnection: ws });

      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const status = await getTaskStatus(taskId);
          if (status.status === 'completed') {
            clearInterval(poll);
            set({ isRunning: false });
            // Mark all nodes as success
            set((s) => ({
              nodes: s.nodes.map((n) => ({
                ...n,
                data: { ...n.data, status: 'success' },
              })),
            }));
            toast.success('工作流执行完成！');
            ws.close();
          } else if (status.status === 'failed') {
            clearInterval(poll);
            set({ isRunning: false });
            if (status.current_node) {
              set((s) => ({
                nodes: s.nodes.map((n) =>
                  n.id === status.current_node
                    ? { ...n, data: { ...n.data, status: 'failed' } }
                    : n
                ),
              }));
            }
            toast.error(`执行失败: ${status.error || '节点执行错误'}`);
            ws.close();
          }
        } catch {
          // Polling error, ignore
        }
      }, 500);
    } catch (err) {
      set({ isRunning: false });
      toast.error(`执行失败: ${err.message}`);
    }
  },

  clearLogs: () => set({ logs: [] }),

  // ---- Node Types ----

  fetchNodeTypes: async () => {
    try {
      const types = await getExecutors();
      const schemas = {};
      types.forEach((t) => {
        schemas[t.type] = t.config_schema || {};
      });
      set({ nodeTypes: types, configSchemas: schemas });
    } catch (err) {
      console.error('Failed to fetch node types:', err);
    }
  },

  // ---- Auto Layout ----

  autoLayout: () => {
    const { nodes, edges } = get();
    if (nodes.length === 0) return;

    // Simple topological layout
    const adj = {};
    const inDegree = {};
    nodes.forEach((n) => {
      adj[n.id] = [];
      inDegree[n.id] = 0;
    });
    edges.forEach((e) => {
      if (adj[e.source]) adj[e.source].push(e.target);
      if (inDegree[e.target] !== undefined) inDegree[e.target]++;
    });

    // BFS layers
    const layers = [];
    let queue = nodes.filter((n) => inDegree[n.id] === 0);
    const placed = new Set();

    while (queue.length > 0) {
      const layerNodes = queue;
      layers.push(layerNodes);
      placed.add(...layerNodes.map((n) => n.id));
      const nextQueue = [];
      for (const node of layerNodes) {
        for (const neighbor of (adj[node.id] || [])) {
          inDegree[neighbor]--;
          if (inDegree[neighbor] === 0 && !placed.has(neighbor)) {
            const n = nodes.find((x) => x.id === neighbor);
            if (n) nextQueue.push(n);
          }
        }
      }
      queue = nextQueue;
    }

    // Place nodes
    const SPACING_X = 280;
    const SPACING_Y = 160;
    const updatedNodes = nodes.map((n) => {
      for (let layerIdx = 0; layerIdx < layers.length; layerIdx++) {
        const layer = layers[layerIdx];
        const idx = layer.findIndex((x) => x.id === n.id);
        if (idx >= 0) {
          return {
            ...n,
            position: {
              x: 100 + layerIdx * SPACING_X,
              y: 80 + idx * SPACING_Y,
            },
          };
        }
      }
      return n;
    });

    set({ nodes: updatedNodes, unsavedChanges: true });
    toast.success('已自动布局');
  },

  resetWorkflow: () => {
    set({
      nodes: [],
      edges: [],
      selectedNode: null,
      workflowName: '未命名工作流',
      workflowDescription: '',
      workflowId: null,
      isRunning: false,
      taskId: null,
      logs: [],
      unsavedChanges: false,
    });
    toast.success('画布已清空');
  },
}));

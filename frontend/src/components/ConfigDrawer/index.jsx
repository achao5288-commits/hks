/**
 * Right-side config drawer for editing node configuration.
 * Dynamically generates form fields from JSON Schema.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { X, Save, RotateCcw, Sparkles, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { useWorkflowStore } from '../../stores/workflowStore';
import { generateAIConfig } from '../../api/client';

function JsonField({ fieldKey, schema, value, onChange }) {
  const fieldType = schema.type || 'string';
  const title = schema.title || fieldKey;
  const description = schema.description || '';
  const isRequired = false; // Handled at form level
  const defaultValue = schema.default;
  const enumValues = schema.enum;

  const displayValue = value !== undefined ? value : (defaultValue !== undefined ? defaultValue : '');

  if (enumValues) {
    return (
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-300 mb-1">
          {title}
          {description && <span className="text-gray-500 ml-1">— {description}</span>}
        </label>
        <select
          value={displayValue}
          onChange={(e) => onChange(fieldKey, e.target.value)}
          className="w-full px-2.5 py-1.5 bg-gray-800 border border-gray-600 rounded-lg text-sm text-gray-200 outline-none focus:border-blue-500"
        >
          {enumValues.map((v) => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>
      </div>
    );
  }

  switch (fieldType) {
    case 'boolean':
      return (
        <div className="mb-3 flex items-center justify-between">
          <div>
            <label className="text-xs font-medium text-gray-300">{title}</label>
            {description && <p className="text-[10px] text-gray-500">{description}</p>}
          </div>
          <button
            onClick={() => onChange(fieldKey, !displayValue)}
            className={`w-10 h-5 rounded-full transition-colors relative ${
              displayValue ? 'bg-blue-600' : 'bg-gray-600'
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-transform ${
                displayValue ? 'translate-x-5' : 'translate-x-0.5'
              }`}
            />
          </button>
        </div>
      );

    case 'number':
      return (
        <div className="mb-3">
          <label className="block text-xs font-medium text-gray-300 mb-1">
            {title}
            {description && <span className="text-gray-500 ml-1">— {description}</span>}
          </label>
          <input
            type="number"
            value={displayValue}
            onChange={(e) => {
              const v = e.target.value;
              onChange(fieldKey, v === '' ? '' : Number(v));
            }}
            className="w-full px-2.5 py-1.5 bg-gray-800 border border-gray-600 rounded-lg text-sm text-gray-200 outline-none focus:border-blue-500"
          />
        </div>
      );

    case 'array':
      return (
        <div className="mb-3">
          <label className="block text-xs font-medium text-gray-300 mb-1">
            {title}
            {description && <span className="text-gray-500 ml-1">— {description}</span>}
          </label>
          <textarea
            value={typeof displayValue === 'object' ? JSON.stringify(displayValue, null, 2) : displayValue}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                onChange(fieldKey, parsed);
              } catch {
                onChange(fieldKey, e.target.value);
              }
            }}
            rows={Math.min(6, Math.max(2, typeof displayValue === 'object' ? JSON.stringify(displayValue, null, 2).split('\n').length : 2))}
            className="w-full px-2.5 py-1.5 bg-gray-800 border border-gray-600 rounded-lg text-sm text-gray-200 font-mono outline-none focus:border-blue-500 resize-y"
            placeholder="[item1, item2]"
          />
        </div>
      );

    case 'object':
      return (
        <div className="mb-3">
          <label className="block text-xs font-medium text-gray-300 mb-1">
            {title}
            {description && <span className="text-gray-500 ml-1">— {description}</span>}
          </label>
          <textarea
            value={typeof displayValue === 'object' ? JSON.stringify(displayValue, null, 2) : displayValue}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                onChange(fieldKey, parsed);
              } catch {
                onChange(fieldKey, e.target.value);
              }
            }}
            rows={3}
            className="w-full px-2.5 py-1.5 bg-gray-800 border border-gray-600 rounded-lg text-sm text-gray-200 font-mono outline-none focus:border-blue-500 resize-y"
            placeholder='{"key": "value"}'
          />
        </div>
      );

    default: // string
      return (
        <div className="mb-3">
          <label className="block text-xs font-medium text-gray-300 mb-1">
            {title}
            {description && <span className="text-gray-500 ml-1">— {description}</span>}
          </label>
          <input
            type="text"
            value={displayValue}
            onChange={(e) => onChange(fieldKey, e.target.value)}
            placeholder={defaultValue ? String(defaultValue) : ''}
            className="w-full px-2.5 py-1.5 bg-gray-800 border border-gray-600 rounded-lg text-sm text-gray-200 outline-none focus:border-blue-500"
          />
        </div>
      );
  }
}

export default function ConfigDrawer() {
  const selectedNode = useWorkflowStore((s) => s.selectedNode);
  const setSelectedNode = useWorkflowStore((s) => s.setSelectedNode);
  const updateNodeConfig = useWorkflowStore((s) => s.updateNodeConfig);
  const configSchemas = useWorkflowStore((s) => s.configSchemas);

  const [formData, setFormData] = useState({});
  const [aiInput, setAiInput] = useState('');
  const [aiLoading, setAiLoading] = useState(false);

  // Load form data when selected node changes
  useEffect(() => {
    if (selectedNode) {
      setFormData({ ...(selectedNode.data?.config || {}) });
    }
  }, [selectedNode?.id]); // Only reset on node change

  const handleFieldChange = useCallback((key, value) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleSave = useCallback(() => {
    if (selectedNode) {
      updateNodeConfig(selectedNode.id, { ...formData });
    }
  }, [selectedNode, formData, updateNodeConfig]);

  const handleReset = useCallback(() => {
    if (selectedNode) {
      setFormData({ ...(selectedNode.data?.config || {}) });
    }
  }, [selectedNode]);

  const handleAIGenerate = useCallback(async () => {
    if (!aiInput.trim()) {
      toast.error('请输入你的需求描述');
      return;
    }
    const nodeType = selectedNode?.data?.nodeType;
    if (!nodeType) return;

    setAiLoading(true);
    try {
      const result = await generateAIConfig(aiInput.trim(), nodeType);
      const aiConfig = result.config || {};
      // Merge AI config with existing form data (AI values take priority)
      setFormData((prev) => ({ ...prev, ...aiConfig }));
      toast.success('AI 配置已生成！请检查并保存');
    } catch (err) {
      toast.error(`AI 生成失败: ${err.message || '未知错误'}`);
    } finally {
      setAiLoading(false);
    }
  }, [aiInput, selectedNode]);

  if (!selectedNode) return null;

  const nodeType = selectedNode.data?.nodeType || '';
  const schema = configSchemas[nodeType] || {};
  const properties = schema.properties || {};
  const required = schema.required || [];
  const fieldKeys = Object.keys(properties);

  return (
    <div className="w-[350px] bg-surface border-l border-gray-700/50 flex flex-col h-full shrink-0 drawer-enter">
      {/* Header */}
      <div className="p-4 border-b border-gray-700/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: selectedNode.data?.color || '#6B7280' }}
          />
          <h3 className="text-sm font-semibold text-gray-200">
            {selectedNode.data?.label || '节点配置'}
          </h3>
          {required.length > 0 && (
            <span className="text-[10px] text-red-400">*{required.length} 必填</span>
          )}
        </div>
        <button
          onClick={() => setSelectedNode(null)}
          className="p-1 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-gray-200 transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      {/* AI Auto-Config Panel */}
      <div className="p-4 border-b border-gray-700/50 bg-purple-900/10">
        <div className="flex items-center gap-1.5 mb-2">
          <Sparkles size={13} className="text-purple-400" />
          <span className="text-xs font-medium text-purple-300">AI 智能配置</span>
        </div>
        <textarea
          value={aiInput}
          onChange={(e) => setAiInput(e.target.value)}
          placeholder='例如："抓取世界杯比分，提取主队、客队、比分、日期"'
          rows={2}
          className="w-full px-2.5 py-1.5 bg-gray-800 border border-gray-600 rounded-lg text-xs text-gray-200 placeholder-gray-500 outline-none focus:border-purple-500 resize-none transition-colors"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
              handleAIGenerate();
            }
          }}
        />
        <button
          onClick={handleAIGenerate}
          disabled={aiLoading}
          className="mt-2 w-full px-3 py-1.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-xs rounded-lg flex items-center justify-center gap-1.5 transition-colors"
        >
          {aiLoading ? (
            <>
              <Loader2 size={12} className="animate-spin" />
              AI 分析中...
            </>
          ) : (
            <>
              <Sparkles size={12} />
              AI 自动填写 (Ctrl+Enter)
            </>
          )}
        </button>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-y-auto p-4">
        {fieldKeys.length === 0 && (
          <div className="text-center text-gray-500 text-sm py-8">
            该节点类型无配置项
          </div>
        )}
        {fieldKeys.map((key) => {
          const fieldSchema = properties[key];
          return (
            <div key={key}>
              <JsonField
                fieldKey={key}
                schema={fieldSchema}
                value={formData[key]}
                onChange={handleFieldChange}
              />
              {required.includes(key) && (
                <span className="text-[10px] text-red-400 -mt-2 mb-2 block">* 必填</span>
              )}
            </div>
          );
        })}

        {/* Expression hint */}
        <div className="mt-4 p-3 bg-blue-900/20 border border-blue-800/30 rounded-lg">
          <p className="text-[10px] text-blue-300 mb-1">💡 支持表达式引用上游数据</p>
          <code className="text-[10px] text-blue-200 font-mono break-all">
            {'${node_id.field.path}'}
          </code>
          <p className="text-[10px] text-blue-300/70 mt-1">
            例如: {'${node_1.data.title}'} 或 {'${node_1.data.items[0].link}'}
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="p-4 border-t border-gray-700/50 flex gap-2">
        <button
          onClick={handleReset}
          className="flex-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm rounded-lg flex items-center justify-center gap-1.5 transition-colors"
        >
          <RotateCcw size={14} />
          重置
        </button>
        <button
          onClick={handleSave}
          className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg flex items-center justify-center gap-1.5 transition-colors"
        >
          <Save size={14} />
          保存配置
        </button>
      </div>
    </div>
  );
}

/**
 * Left sidebar node panel — draggable node type cards.
 */
import React, { useState, useCallback } from 'react';
import {
  Globe, Rss, Filter, FileSpreadsheet, Mail, Clock, Search,
} from 'lucide-react';

const NODE_TYPES = [
  {
    type: 'web_crawler',
    label: '网页抓取',
    description: '抓取网页数据，支持CSS选择器',
    icon: Globe,
    color: '#3B82F6',
  },
  {
    type: 'rss_monitor',
    label: 'RSS监控',
    description: '监控RSS源更新，关键词过滤',
    icon: Rss,
    color: '#F97316',
  },
  {
    type: 'data_process',
    label: '数据清洗',
    description: '清洗转换数据，去重填充排序',
    icon: Filter,
    color: '#22C55E',
  },
  {
    type: 'excel_chart',
    label: 'Excel生成',
    description: '生成Excel表格和统计图表',
    icon: FileSpreadsheet,
    color: '#EAB308',
  },
  {
    type: 'email_sender',
    label: '邮件发送',
    description: '发送邮件报告，支持附件和重试',
    icon: Mail,
    color: '#EF4444',
  },
  {
    type: 'schedule_trigger',
    label: '定时触发',
    description: 'Cron表达式定时触发工作流',
    icon: Clock,
    color: '#8B5CF6',
  },
];

export default function NodePanel() {
  const [search, setSearch] = useState('');

  const filteredTypes = NODE_TYPES.filter(
    (t) =>
      t.label.includes(search) ||
      t.description.includes(search) ||
      t.type.includes(search)
  );

  const onDragStart = useCallback((event, nodeType) => {
    event.dataTransfer.setData('application/reactflow-type', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  }, []);

  const onCardClick = useCallback((nodeType) => {
    // Dispatch a custom event that the canvas can listen to for adding at center
    window.dispatchEvent(
      new CustomEvent('panel-add-node', { detail: { type: nodeType } })
    );
  }, []);

  return (
    <div className="w-[260px] bg-surface border-r border-gray-700/50 flex flex-col h-full shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-gray-700/50">
        <h2 className="text-sm font-semibold text-gray-200 mb-3">📦 节点库</h2>
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="搜索节点类型..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-gray-800 border border-gray-600 rounded-lg text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-blue-500 transition-colors"
          />
        </div>
      </div>

      {/* Node type cards */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {filteredTypes.length === 0 && (
          <div className="text-center text-gray-500 text-sm py-8">
            未找到匹配的节点类型
          </div>
        )}
        {filteredTypes.map((nodeType) => {
          const Icon = nodeType.icon;
          return (
            <div
              key={nodeType.type}
              draggable
              onDragStart={(e) => onDragStart(e, nodeType.type)}
              onClick={() => onCardClick(nodeType.type)}
              className="node-card group p-3 rounded-lg cursor-grab active:cursor-grabbing
                         border border-gray-700/50 hover:border-gray-500
                         transition-all duration-150 hover:shadow-lg hover:-translate-y-0.5"
              style={{
                backgroundColor: '#16162a',
              }}
              title={`拖拽到画布添加 ${nodeType.label} 节点`}
            >
              <div className="flex items-start gap-2.5">
                <div
                  className="p-1.5 rounded-lg shrink-0 mt-0.5"
                  style={{ backgroundColor: `${nodeType.color}18` }}
                >
                  <Icon size={16} color={nodeType.color} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-200">
                    {nodeType.label}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                    {nodeType.description}
                  </div>
                </div>
              </div>
              {/* Drag hint */}
              <div className="mt-2 flex items-center gap-1 text-[10px] text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity">
                <span>↕</span>
                <span>拖拽到画布</span>
                <span className="ml-auto">点击添加</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-gray-700/50 text-[10px] text-gray-600 text-center">
        拖拽节点到画布 | Delete 删除 | Ctrl+S 保存
      </div>
    </div>
  );
}

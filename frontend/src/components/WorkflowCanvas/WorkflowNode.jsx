/**
 * Custom React Flow node component for workflow nodes.
 */
import React, { useState, useCallback, memo } from 'react';
import { Handle, Position } from 'reactflow';
import {
  Globe, Rss, Filter, FileSpreadsheet, Mail, Clock, Box,
} from 'lucide-react';

const ICON_MAP = {
  Globe, Rss, Filter, FileSpreadsheet, Mail, Clock, Box,
};

const STATUS_COLORS = {
  pending: '#6B7280',
  running: '#3B82F6',
  success: '#22C55E',
  failed: '#EF4444',
};

function WorkflowNode({ id, data, selected }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(data.label || '');

  const IconComponent = ICON_MAP[data.icon] || Box;
  const statusColor = STATUS_COLORS[data.status] || STATUS_COLORS.pending;
  const borderColor = selected ? '#6366F1' : data.color || '#6B7280';
  const isRunning = data.status === 'running';

  const handleDoubleClick = useCallback((e) => {
    e.stopPropagation();
    setIsEditing(true);
    setEditValue(data.label || '');
  }, [data.label]);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
    if (editValue.trim() && editValue !== data.label) {
      // Dispatch custom event for the store to handle
      window.dispatchEvent(
        new CustomEvent('node-label-edit', { detail: { nodeId: id, label: editValue.trim() } })
      );
    }
  }, [editValue, data.label, id]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      handleBlur();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
      setEditValue(data.label || '');
    }
  }, [handleBlur, data.label]);

  return (
    <div
      className={`
        relative rounded-xl border-2 shadow-lg px-4 py-3
        min-w-[170px] cursor-pointer select-none
        transition-all duration-200
        ${isRunning ? 'node-running' : ''}
      `}
      style={{
        backgroundColor: '#1a1a2e',
        borderColor,
        boxShadow: selected
          ? `0 0 20px ${borderColor}44`
          : '0 4px 12px rgba(0,0,0,0.3)',
      }}
      onDoubleClick={handleDoubleClick}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          background: '#888',
          border: '2px solid #555',
          width: 12,
          height: 12,
          left: -6,
        }}
      />

      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <div
          className="p-1.5 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${data.color}22` }}
        >
          <IconComponent size={18} color={data.color} />
        </div>
        <div className="flex-1 min-w-0">
          {isEditing ? (
            <input
              autoFocus
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              className="bg-transparent border-b border-blue-400 text-white text-sm font-medium w-full outline-none"
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <div className="text-white text-sm font-medium truncate">
              {data.label || data.nodeType}
            </div>
          )}
        </div>
      </div>

      {/* Status dot */}
      <div className="flex items-center gap-1.5">
        <div
          className="rounded-full transition-colors"
          style={{
            width: 8,
            height: 8,
            backgroundColor: statusColor,
          }}
        />
        <span className="text-xs text-gray-400 capitalize">
          {data.status === 'pending' ? '待执行' :
           data.status === 'running' ? '执行中' :
           data.status === 'success' ? '已完成' :
           data.status === 'failed' ? '失败' : data.status}
        </span>
      </div>

      {/* Config summary */}
      {data.config && Object.keys(data.config).length > 0 && (
        <div className="mt-2 pt-2 border-t border-gray-700/50">
          <div className="text-[10px] text-gray-500 truncate">
            {Object.entries(data.config)
              .slice(0, 2)
              .map(([k, v]) => `${k}: ${typeof v === 'object' ? '...' : String(v).substring(0, 20)}`)
              .join(' | ')}
          </div>
        </div>
      )}

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        style={{
          background: '#888',
          border: '2px solid #555',
          width: 12,
          height: 12,
          right: -6,
        }}
      />
    </div>
  );
}

export default memo(WorkflowNode);

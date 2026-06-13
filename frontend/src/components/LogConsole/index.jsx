/**
 * Bottom log console panel for real-time execution logs.
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  ChevronUp, ChevronDown, Trash2, Download, Info, AlertTriangle, XCircle,
} from 'lucide-react';
import { useWorkflowStore } from '../../stores/workflowStore';

const LEVEL_CONFIG = {
  info: { icon: Info, color: '#3B82F6', bg: 'bg-blue-500/10' },
  warn: { icon: AlertTriangle, color: '#F59E0B', bg: 'bg-yellow-500/10' },
  error: { icon: XCircle, color: '#EF4444', bg: 'bg-red-500/10' },
};

export default function LogConsole() {
  const [isExpanded, setIsExpanded] = useState(true);
  const logs = useWorkflowStore((s) => s.logs);
  const clearLogs = useWorkflowStore((s) => s.clearLogs);
  const isRunning = useWorkflowStore((s) => s.isRunning);
  const scrollRef = useRef(null);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current && isExpanded) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isExpanded]);

  const handleDownload = () => {
    const text = logs
      .map((l) => `[${l.timestamp}] [${l.level.toUpperCase()}] [${l.node_id}] ${l.message}`)
      .join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow-logs-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const errorCount = logs.filter((l) => l.level === 'error').length;
  const warnCount = logs.filter((l) => l.level === 'warn').length;

  return (
    <div className="border-t border-gray-700/50 bg-surface shrink-0">
      {/* Header bar */}
      <div
        className="flex items-center justify-between px-4 py-1.5 cursor-pointer hover:bg-surface-light transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-300">
            📋 执行日志
          </span>
          <span className="text-[10px] text-gray-500">
            {logs.length} 条
          </span>
          {isRunning && (
            <span className="flex items-center gap-1 text-[10px] text-blue-400">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
              执行中
            </span>
          )}
          {errorCount > 0 && (
            <span className="text-[10px] text-red-400">({errorCount} 错误)</span>
          )}
          {warnCount > 0 && (
            <span className="text-[10px] text-yellow-400">({warnCount} 警告)</span>
          )}
        </div>
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={handleDownload}
            disabled={logs.length === 0}
            className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="下载日志"
          >
            <Download size={13} />
          </button>
          <button
            onClick={clearLogs}
            disabled={logs.length === 0}
            className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            title="清空日志"
          >
            <Trash2 size={13} />
          </button>
          <div className="text-gray-500">
            {isExpanded ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
          </div>
        </div>
      </div>

      {/* Log entries */}
      {isExpanded && (
        <div
          ref={scrollRef}
          className="overflow-y-auto border-t border-gray-700/30"
          style={{ maxHeight: 200 }}
        >
          {logs.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-xs text-gray-600">
              暂无日志，执行工作流后将在此显示实时日志
            </div>
          ) : (
            <div className="divide-y divide-gray-800/50">
              {logs.map((log, idx) => {
                const config = LEVEL_CONFIG[log.level] || LEVEL_CONFIG.info;
                const Icon = config.icon;
                return (
                  <div
                    key={idx}
                    className={`flex items-start gap-2 px-4 py-1.5 hover:bg-surface-light/50 transition-colors ${config.bg}`}
                  >
                    <Icon size={12} color={config.color} className="mt-0.5 shrink-0" />
                    <span className="text-[10px] text-gray-500 font-mono shrink-0 mt-0.5 min-w-[70px]">
                      {log.timestamp
                        ? new Date(log.timestamp).toLocaleTimeString('zh-CN', { hour12: false })
                        : '--:--:--'}
                    </span>
                    <span
                      className="text-[10px] font-mono shrink-0 mt-0.5 min-w-[80px] max-w-[120px] truncate"
                      style={{ color: config.color }}
                    >
                      [{log.node_id}]
                    </span>
                    <span className="text-xs text-gray-300 break-all flex-1">
                      {log.message}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

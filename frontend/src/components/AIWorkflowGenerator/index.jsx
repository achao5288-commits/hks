/**
 * AI full-workflow generator — one input, complete workflow.
 * User describes what they want, AI creates the entire workflow automatically.
 */
import React, { useState, useCallback } from 'react';
import { Sparkles, Loader2, X, Zap, Mail, Globe, Filter, FileSpreadsheet } from 'lucide-react';
import toast from 'react-hot-toast';
import { useWorkflowStore } from '../../stores/workflowStore';
import { generateAIConfig } from '../../api/client';

const EXAMPLE_PROMPTS = [
  '抓取世界杯淘汰赛比分数据，清洗后生成Excel报表，从2459669124@qq.com发送到17702229093@163.com，授权码ohdnflegyrxgecec',
  '监控百度热搜榜，生成每日热榜Excel并发送邮件报告',
  '抓取demo-news.html的舆情新闻，清洗去重后生成图表，通过QQ邮箱发送日报',
];

export default function AIWorkflowGenerator({ isOpen, onClose }) {
  const [requirement, setRequirement] = useState('');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [generatedWorkflow, setGeneratedWorkflow] = useState(null);

  const loadWorkflow = useWorkflowStore((s) => s.loadWorkflow);

  const addLog = useCallback((msg) => {
    setLogs((prev) => [...prev, msg]);
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!requirement.trim()) {
      toast.error('请输入你的需求描述');
      return;
    }

    setLoading(true);
    setLogs([]);
    setGeneratedWorkflow(null);

    try {
      addLog('🤔 AI 正在分析你的需求...');

      const response = await fetch('/api/ai/auto-workflow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requirement: requirement.trim() }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.message || '生成失败');
      }

      const data = await response.json();
      if (data.code !== 0) {
        throw new Error(data.message || '生成失败');
      }

      const wf = data.data;
      addLog(`✅ 工作流已生成: "${wf.name}"`);
      addLog(`📦 ${wf.nodes.length} 个节点, ${wf.edges.length} 条连线`);

      wf.nodes.forEach((n, i) => {
        const typeLabels = {
          schedule_trigger: '⏰ 定时触发',
          web_crawler: '🌐 网页抓取',
          rss_monitor: '📡 RSS监控',
          data_process: '🔧 数据清洗',
          excel_chart: '📊 Excel生成',
          email_sender: '📧 邮件发送',
        };
        addLog(`  ${typeLabels[n.type] || n.type}: ${Object.keys(n.config || {}).length}项配置`);
      });

      addLog('📂 正在加载到画布...');

      // Load into canvas
      await loadWorkflow(wf.id);

      addLog('✅ 完成！工作流已加载到画布');
      setGeneratedWorkflow(wf);
      toast.success(`AI 已生成工作流: ${wf.name}`);
    } catch (err) {
      addLog(`❌ 错误: ${err.message}`);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [requirement, loadWorkflow, addLog]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleGenerate();
    }
  }, [handleGenerate]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-surface rounded-2xl border border-gray-700 w-[640px] max-h-[85vh] flex flex-col shadow-2xl overflow-hidden drawer-enter">
        {/* Header */}
        <div className="p-5 border-b border-gray-700/50 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-purple-600/20 rounded-lg">
              <Zap size={18} className="text-purple-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">AI 智能工作流生成器</h3>
              <p className="text-[11px] text-gray-400">用一句话描述需求，AI 自动创建完整工作流</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Input area */}
        <div className="p-5 border-b border-gray-700/30">
          <textarea
            value={requirement}
            onChange={(e) => setRequirement(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="例如：抓取世界杯淘汰赛比分数据，清洗后生成Excel报表，从2459669124@qq.com发送到17702229093@163.com，授权码ohdnflegyrxgecec..."
            rows={4}
            disabled={loading}
            className="w-full px-3.5 py-3 bg-gray-800 border border-gray-600 rounded-xl text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-purple-500 resize-none transition-colors disabled:opacity-50"
            autoFocus
          />

          <div className="flex items-center justify-between mt-3">
            <div className="flex gap-1.5 flex-wrap">
              {EXAMPLE_PROMPTS.slice(0, 2).map((p, i) => (
                <button
                  key={i}
                  onClick={() => setRequirement(p)}
                  disabled={loading}
                  className="px-2 py-0.5 bg-gray-800 hover:bg-gray-700 border border-gray-600 rounded-md text-[10px] text-gray-400 hover:text-gray-200 truncate max-w-[240px] transition-colors disabled:opacity-50"
                >
                  {p.substring(0, 35)}...
                </button>
              ))}
            </div>
            <button
              onClick={handleGenerate}
              disabled={loading || !requirement.trim()}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-40 text-white text-sm rounded-xl flex items-center gap-2 transition-colors font-medium"
            >
              {loading ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles size={15} />
                  生成工作流
                </>
              )}
            </button>
          </div>
          <p className="text-[10px] text-gray-500 mt-2">Ctrl+Enter 快速生成</p>
        </div>

        {/* Log output */}
        <div className="flex-1 overflow-y-auto p-4 min-h-[180px] max-h-[300px] bg-[#0d0d1a]">
          {logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-600 gap-3 py-8">
              <Sparkles size={32} className="text-gray-700" />
              <p className="text-xs">输入需求后，AI 将自动设计并创建完整工作流</p>
              <div className="flex gap-4 mt-2">
                <div className="flex items-center gap-1.5 text-[10px]"><Globe size={10}/> 抓取</div>
                <span className="text-gray-700">→</span>
                <div className="flex items-center gap-1.5 text-[10px]"><Filter size={10}/> 清洗</div>
                <span className="text-gray-700">→</span>
                <div className="flex items-center gap-1.5 text-[10px]"><FileSpreadsheet size={10}/> 报表</div>
                <span className="text-gray-700">→</span>
                <div className="flex items-center gap-1.5 text-[10px]"><Mail size={10}/> 发送</div>
              </div>
            </div>
          ) : (
            <div className="space-y-1 font-mono text-xs">
              {logs.map((log, i) => (
                <div
                  key={i}
                  className={`px-2 py-1 rounded ${
                    log.startsWith('❌') ? 'text-red-400 bg-red-500/5' :
                    log.startsWith('✅') ? 'text-green-400' :
                    'text-gray-300'
                  }`}
                >
                  {log}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-700/30 flex items-center justify-between text-[10px] text-gray-600">
          <span>Powered by 硅基流动 DeepSeek-V3</span>
          {generatedWorkflow && (
            <button
              onClick={onClose}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-xs"
            >
              返回画布查看
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { X } from 'lucide-react';
import type { MCPTool } from '@/types';

interface MCPToolDetailModalProps {
  tool: MCPTool | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * MCP工具详情模态框组件
 */
const MCPToolDetailModal: React.FC<MCPToolDetailModalProps> = ({
  tool,
  isOpen,
  onClose
}) => {
  if (!isOpen || !tool) return null;

  // Helper function to render schema parameters
  const renderSchemaParameter = (paramName: string, paramData: any) => {
    const isRequired = paramData.required || false;
    const paramType = paramData.type || 'string';
    const description = paramData.description || '';

    return (
      <div key={paramName} className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="font-mono text-base text-gray-900">{paramName}</span>
          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded font-medium">
            {paramType}
          </span>
          {isRequired && (
            <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded font-medium">
              required
            </span>
          )}
        </div>
        {description && (
          <p className="text-sm text-gray-600 leading-relaxed ml-0">
            {description}
          </p>
        )}
      </div>
    );
  };

  // Extract schema parameters from input_schema
  const getSchemaParameters = () => {
    if (!tool.input_schema || !tool.input_schema.properties) {
      return [];
    }

    return Object.entries(tool.input_schema.properties).map(([key, value]: [string, any]) => ({
      name: key,
      ...value,
      required: tool.input_schema?.required?.includes(key) || false
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-8 py-6 border-b border-gray-200">
          <div>
            <h1 className="text-xl font-normal text-gray-900">
              <span className="text-gray-500">Tool Details - </span>
              <span className="text-gray-900 font-medium">{tool.name}</span>
            </h1>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-200px)]">
          <div className="px-8 py-6 space-y-8">
            {/* Description */}
            <div>
              <p className="text-gray-600 leading-relaxed text-base">
                {tool.description}
              </p>
            </div>

            {/* Schema Section */}
            <div>
              <h2 className="text-lg font-medium text-gray-900 mb-6">Schema</h2>
              <div className="bg-gray-50 rounded-lg p-6">
                {getSchemaParameters().length > 0 ? (
                  <div className="space-y-6">
                    {getSchemaParameters().map((param) =>
                      renderSchemaParameter(param.name, param)
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No schema parameters available</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 px-8 py-6 border-t border-gray-200 bg-white">
          <button
            onClick={onClose}
            className="px-6 py-2 text-sm font-medium text-white bg-teal-600 rounded-md hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default MCPToolDetailModal;

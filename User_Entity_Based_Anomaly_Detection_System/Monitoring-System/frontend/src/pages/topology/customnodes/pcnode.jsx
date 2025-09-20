import React from 'react';
import { Handle, Position } from 'reactflow';
import pcImg from '../../../assets/nodeicon/PC.svg';

const PCNode = ({ data }) => {
  const { selected, fullData } = data;

  if (selected) {
    return (
      <div className="flex flex-col items-start border border-blue-400 bg-blue-50 rounded shadow-md p-2 w-48 text-xs">
        <div className="flex items-center mb-2">
          <img src={pcImg} alt="PC" className="w-6 h-6 mr-2" />
          <div className="font-bold text-sm text-blue-800">{fullData.label}</div>
        </div>
        <div className="text-gray-700">
          <div><strong>IP address:</strong> {fullData.ip_address?.[0]}</div>
          <div><strong>MAC address:</strong> {fullData.mac_address?.[0]}</div>
          <div><strong>State:</strong> {fullData.state?.[0]}</div>
          <div><strong>User:</strong> {fullData.present_user_id ?? '없음'}</div>
          <div><strong>Access:</strong> {fullData.access_flag?.[0] ? '허용' : '차단'}</div>
        </div>

        <Handle type="source" position={Position.Right} />
        <Handle type="target" position={Position.Left} />
      </div>
    );
  }

  // 기본 PC 노드
  return (
    <div className="flex flex-col items-center border border-gray-300 bg-white rounded shadow-md p-2 w-32">
      <img src={pcImg} alt="PC" className="w-8 h-8 mb-1" />
      <div className="text-xs font-semibold text-center text-gray-800">{data.label}</div>
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </div>
  );
};

export default PCNode;

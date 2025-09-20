import React from 'react';
import { Handle, Position } from 'reactflow';
import routerImg from '../../../assets/nodeicon/router.svg';

const RouterNode = ({ data }) => {
  return (
    <div className="relative w-24 h-24 rounded-full bg-white border border-gray-400 shadow flex flex-col items-center justify-center">
      {/* 라우터 아이콘 */}
      <img src={routerImg} alt="Router" className="w-8 h-8 mb-1" />

      {/* 라벨 */}
      <div className="text-[10px] font-bold text-center text-gray-800">
        {data.label}
      </div>

      {/* 핸들 */}
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </div>
  );
};

export default RouterNode;

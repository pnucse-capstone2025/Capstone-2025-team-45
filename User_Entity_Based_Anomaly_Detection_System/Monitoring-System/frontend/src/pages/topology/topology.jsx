import React, { useState, useEffect } from 'react';
import { fetchTopologyData } from '../../services/TopologyService';
import TopologyFlow from './topologyflow';
import CommonCard from '../../components/common/card/CommonCard';

const Topology = () => {
  const [topology, setTopology] = useState(null);

  useEffect(() => {
    fetchTopologyData()
      .then(data => {
        setTopology(data);
        console.log('Fetched topology data:', data);
      })
      .catch(error => {
        console.error('Error fetching topology data:', error);
      });
  }, []);

  return (
    <div className="w-full px-6 py-6">
      <h1 className="text-2xl font-bold mb-2 text-gray-800">Network Topology</h1>
      <p className="text-gray-600 mb-6">
        조직의 네트워크 토폴로지를 시각화합니다. 각 노드는 라우터 또는 PC를 나타내며, 연결된 엣지로 네트워크 구조를 보여줍니다.
      </p>

      <CommonCard>
        {topology ? (
          <div className="w-full h-[600px]">
            <TopologyFlow topology={topology} />
          </div>
        ) : (
          <p className="text-center text-gray-500">Loading topology...</p>
        )}
      </CommonCard>
    </div>
  );
};

export default Topology;

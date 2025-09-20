import React, { useMemo, useState, useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';

import RouterNode from './customnodes/routernode';
import PCNode from './customnodes/pcnode';

const TopologyFlow = ({ topology }) => {
  const [selectedId, setSelectedId] = useState(null);

  const nodeTypes = useMemo(() => ({
    router: RouterNode,
    pc: PCNode,
  }), []);

  const initialNodes = useMemo(() => {
    const childrenCount = {};
    const offset = 80;

    const getIndex = (nodeId) => {
      const parents = topology.edges.filter(e => e.target === nodeId).map(e => e.source);
      const parent = parents[0] || '__root__';
      childrenCount[parent] = (childrenCount[parent] || 0) + 1;
      return childrenCount[parent] - 1;
    };

    return topology.nodes.map((node) => {
      let position = node.position;
      if (node.type === 'pc') {
        const idx = getIndex(node.id);
        position = { x: node.position.x, y: node.position.y + idx * offset };
      }
      return {
        id: node.id,
        data: { ...node.data, fullData: node, selected: false },
        position,
        type: node.type,
      };
    });
  }, [topology]);


  const initialEdges = useMemo(() => {
    return topology.edges.map((edge, index) => ({
      id: edge.id || `edge-${index}`,
      source: edge.source,
      target: edge.target,
      type: 'default',
    }));
  }, [topology]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const onNodeClick = useCallback((event, node) => {
    setNodes((nds) =>
      nds.map((n) => {
        const isClicked = n.id === node.id;
        const isAlreadySelected = n.data.selected;
        return {
          ...n,
          data: {
            ...n.data,
            selected: isClicked ? !isAlreadySelected : false,
          },
        };
      })
    );
    setSelectedId((prevId) => (prevId === node.id ? null : node.id));
  }, [setNodes]);

  return (
    <div style={{ width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
      >
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
};

export default TopologyFlow;

export const IncompleteFlowManager = ({ flows, onContinueFlow, onDeleteFlow, onBatchDelete, onViewDetails, isLoading }) => {
  return (
    <div className="p-4">
      <h3>Flow Manager - V2 Compatible</h3>
      <p>{flows.length} flows found</p>
      {flows.map(flow => (
        <div key={flow.flow_id} className="border p-2 mb-2">
          <p>Flow: {flow.flow_id}</p>
          <p>Status: {flow.status}</p>
          <button onClick={() => onContinueFlow(flow.flow_id)}>Continue</button>
          <button onClick={() => onViewDetails(flow.flow_id, flow.current_phase)}>View</button>
        </div>
      ))}
    </div>
  );
};

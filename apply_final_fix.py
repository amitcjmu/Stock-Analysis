import os

def apply_fix():
    """
    Reads the crewai_flow_service.py file and applies the circular dependency fix
    by directly inserting the corrected code.
    """
    file_path = "backend/app/services/crewai_flow_service.py"
    
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Find the line to remove
    line_to_remove = "from app.services.agent_learning_system import AgentLearningSystem, get_agent_learning_system\\n"
    if line_to_remove in lines:
        lines.remove(line_to_remove)
        print(f"✅ Removed line: {line_to_remove.strip()}")

    # Find the insertion point
    insertion_point = -1
    for i, line in enumerate(lines):
        if "async def _execute_agentic_flow_with_state" in line:
            insertion_point = i + 7  # Insert after the method signature
            break

    if insertion_point != -1:
        lines.insert(insertion_point, "        # LATE IMPORTS TO PREVENT CIRCULAR DEPENDENCIES\\n")
        lines.insert(insertion_point + 1, "        from app.services.asset_processing_service import asset_processing_service\\n")
        lines.insert(insertion_point + 2, "        from app.services.agent_learning_system import get_agent_learning_system\\n\\n")
        lines.insert(insertion_point + 3, "        agent_learning_system = get_agent_learning_system()\\n\\n")
        print("✅ Added late import to fix circular dependency.")

    with open(file_path, "w") as f:
        f.writelines(lines)

    print("🎉 Final fix applied successfully!")

if __name__ == "__main__":
    apply_fix() 
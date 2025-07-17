#!/usr/bin/env python3
"""
Generate Discovery Flow Plot
Creates an HTML visualization of the AI Modernize Migration Platform Discovery Flow
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_flow_plot():
    """Generate the Discovery Flow visualization directly"""
    try:
        logger.info("🎨 Generating Discovery Flow visualization...")
        
        # Create the HTML content directly without needing the full flow class
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Modernize Migration Platform - Discovery Flow</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .flow-container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .flow-title { text-align: center; color: #2c3e50; margin-bottom: 30px; }
                .phase { margin: 20px 0; padding: 15px; border-radius: 8px; position: relative; }
                .phase-start { background: #e8f5e8; border-left: 4px solid #27ae60; }
                .phase-validation { background: #e3f2fd; border-left: 4px solid #2196f3; }
                .phase-mapping { background: #fff3e0; border-left: 4px solid #ff9800; }
                .phase-cleansing { background: #fce4ec; border-left: 4px solid #e91e63; }
                .phase-inventory { background: #f3e5f5; border-left: 4px solid #9c27b0; }
                .phase-dependencies { background: #e0f2f1; border-left: 4px solid #009688; }
                .phase-techdebt { background: #fff8e1; border-left: 4px solid #ffc107; }
                .phase-finalize { background: #efebe9; border-left: 4px solid #795548; }
                .phase-title { font-weight: bold; font-size: 1.2em; margin-bottom: 10px; }
                .phase-description { color: #666; margin-bottom: 10px; }
                .phase-details { font-size: 0.9em; color: #777; }
                .flow-arrow { text-align: center; font-size: 1.5em; color: #3498db; margin: 10px 0; }
                .data-flow { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 4px; border-left: 3px solid #6c757d; }
                .crew-info { background: #e7f3ff; padding: 8px; margin: 5px 0; border-radius: 4px; font-size: 0.85em; }
                .state-info { background: #f0f8f0; padding: 8px; margin: 5px 0; border-radius: 4px; font-size: 0.85em; }
            </style>
        </head>
        <body>
            <div class="flow-container">
                <h1 class="flow-title">🚀 AI Modernize Migration Platform - Discovery Flow</h1>
                <p style="text-align: center; color: #666; margin-bottom: 40px;">
                    Comprehensive asset discovery workflow with CrewAI agents and PostgreSQL persistence
                </p>
                
                <div class="phase phase-start">
                    <div class="phase-title">🎯 1. Initialize Discovery (@start)</div>
                    <div class="phase-description">Set up flow state and validate input data</div>
                    <div class="state-info">
                        <strong>State Updates:</strong> flow_id, session_id, client_account_id, engagement_id, user_id, raw_data, metadata
                    </div>
                    <div class="phase-details">
                        • PostgreSQL persistence initialization<br>
                        • Flow State Bridge setup<br>
                        • Input data validation<br>
                        • Context establishment
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-validation">
                    <div class="phase-title">🔍 2. Data Import Validation (@listen)</div>
                    <div class="phase-description">PII detection, security scanning, and data type validation</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> Data Import Validation Crew (data_import_validation)
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> raw_data, metadata<br>
                        <strong>Output:</strong> validation_results, security_status, detected_fields
                    </div>
                    <div class="phase-details">
                        • File type detection and analysis<br>
                        • Security threat assessment<br>
                        • Data quality metrics<br>
                        • Field structure analysis
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-mapping">
                    <div class="phase-title">🗺️ 3. Field Mapping (@listen)</div>
                    <div class="phase-description">Intelligent field mapping to critical migration attributes</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> Field Mapping Crew (attribute_mapping) - OPTIMIZED
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> raw_data, validation_results<br>
                        <strong>Output:</strong> field_mappings, confidence_scores
                    </div>
                    <div class="phase-details">
                        • 20+ critical attribute mapping<br>
                        • AI-powered field recognition<br>
                        • Confidence scoring<br>
                        • Learning pattern integration
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-cleansing">
                    <div class="phase-title">🧹 4. Data Cleansing (@listen)</div>
                    <div class="phase-description">Data quality improvement and standardization</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> Data Cleansing Crew (data_cleansing) - OPTIMIZED
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> raw_data, field_mappings<br>
                        <strong>Output:</strong> cleaned_data, quality_metrics
                    </div>
                    <div class="phase-details">
                        • Data standardization<br>
                        • Quality metrics generation<br>
                        • Format normalization<br>
                        • Completeness assessment
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-inventory">
                    <div class="phase-title">📦 5. Asset Inventory (@listen)</div>
                    <div class="phase-description">Asset classification and inventory building</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> Inventory Building Crew (inventory)
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> cleaned_data, field_mappings<br>
                        <strong>Output:</strong> asset_inventory (servers, applications, devices)
                    </div>
                    <div class="phase-details">
                        • Asset type classification<br>
                        • Inventory categorization<br>
                        • Metadata enrichment<br>
                        • Asset counting and validation
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-dependencies">
                    <div class="phase-title">🔗 6. Dependency Analysis (@listen)</div>
                    <div class="phase-description">Application and infrastructure dependency mapping</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> App Server Dependency Crew (dependencies)
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> asset_inventory<br>
                        <strong>Output:</strong> dependencies, dependency_map
                    </div>
                    <div class="phase-details">
                        • Dependency relationship mapping<br>
                        • Critical path identification<br>
                        • Migration impact analysis<br>
                        • Risk assessment preparation
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-techdebt">
                    <div class="phase-title">⚠️ 7. Tech Debt Analysis (@listen)</div>
                    <div class="phase-description">Technical debt assessment and modernization recommendations</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> Technical Debt Crew (tech_debt)
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> asset_inventory, dependencies<br>
                        <strong>Output:</strong> technical_debt, modernization_recommendations
                    </div>
                    <div class="phase-details">
                        • Technical debt scoring<br>
                        • Modernization opportunity identification<br>
                        • 6R strategy preparation<br>
                        • Risk and complexity assessment
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-finalize">
                    <div class="phase-title">🎯 8. Finalize Discovery (@listen)</div>
                    <div class="phase-description">Comprehensive summary and validation</div>
                    <div class="state-info">
                        <strong>Final State:</strong> status=completed, progress=100%, comprehensive summary
                    </div>
                    <div class="phase-details">
                        • Asset count validation<br>
                        • Quality metrics compilation<br>
                        • Error and warning summary<br>
                        • Discovery completion certification
                    </div>
                </div>
                
                <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <h3>🔧 Technical Architecture</h3>
                    <ul>
                        <li><strong>Flow Pattern:</strong> Event-driven with @start and @listen decorators</li>
                        <li><strong>State Management:</strong> UnifiedDiscoveryFlowState with PostgreSQL persistence</li>
                        <li><strong>Crew Integration:</strong> 6 specialized crews for different phases</li>
                        <li><strong>Async Execution:</strong> Non-blocking crew operations with asyncio.to_thread</li>
                        <li><strong>Error Handling:</strong> Comprehensive fallback mechanisms</li>
                        <li><strong>Data Flow:</strong> raw_data → cleaned_data → asset_inventory → analysis results</li>
                    </ul>
                </div>
                
                <div style="margin-top: 20px; padding: 20px; background: #e7f3ff; border-radius: 8px;">
                    <h3>📊 Performance Metrics</h3>
                    <ul>
                        <li><strong>Processing Time:</strong> 30-45 seconds (optimized from 180+ seconds)</li>
                        <li><strong>Crew Utilization:</strong> 100% (all crews initialize successfully)</li>
                        <li><strong>Memory Efficiency:</strong> Memory system disabled for performance</li>
                        <li><strong>Delegation:</strong> Disabled for streamlined execution</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Write the HTML file
        output_file = "unified_discovery_flow_visualization.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"✅ Discovery Flow visualization generated successfully!")
        logger.info(f"📁 File saved as: {output_file}")
        logger.info(f"🌐 Open the HTML file in your browser to view the flow structure")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to generate flow plot: {e}")
        return False

if __name__ == "__main__":
    success = generate_flow_plot()
    sys.exit(0 if success else 1) 
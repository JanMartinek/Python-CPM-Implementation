"""
Advanced CPM Template Processing Demo

This example demonstrates advanced features of the Python implementation:
1. Quality analysis and scoring
2. Agent overlap detection and merging strategy
3. Multi-format transformation (EMBRC)
4. Validation with JSON schema
5. Transformation pipelines
"""

from pathlib import Path
import json
from src.cpm.template import (
    TraversalInformationDeserializer,
    TraversalInformationSerializer,
    TemplateSchemaValidator,
    TemplateTransformationPipeline,
    TemplateAgentAnalyzer,
    TraversalInformationTemplate,
    MainActivityTemplate,
    ConnectorTemplate,
    AgentTemplate
)
from src.cpm.model import CpmDocument


def demo_basic_workflow():
    """Demonstrate basic template workflow"""
    print("=" * 60)
    print("DEMO 1: Basic Template Workflow")
    print("=" * 60)

    # Create a simple template programmatically
    template = TraversalInformationTemplate(
        prefixes={
            'cpm': 'http://provcpm.org/',
            'ex': 'http://example.org/'
        },
        bundle_name='ex:bundle1',
        main_activity=MainActivityTemplate(
            id='ex:mainActivity',
            start_time='2024-01-01T10:00:00',
            end_time='2024-01-01T11:00:00'
        ),
        forward_connectors=[
            ConnectorTemplate(id='ex:forwardConn1')
        ],
        sender_agents=[
            AgentTemplate(id='ex:senderAgent1')
        ]
    )

    # Serialize to JSON
    json_output = TraversalInformationSerializer.to_json(template, indent=2)
    print("\nSerialized Template:")
    print(json_output[:500] + "...")

    # Deserialize back
    template_roundtrip = TraversalInformationDeserializer.from_json(json_output)
    print(f"\n✅ Round-trip successful! Bundle: {template_roundtrip.bundle_name}")



def demo_quality_analysis():
    """Demonstrate quality analysis (Python-exclusive)"""
    print("\n" + "=" * 60)
    print("DEMO 2: Quality Analysis (Python-EXCLUSIVE)")
    print("=" * 60)

    # Create template with various quality indicators
    template = TraversalInformationTemplate(
        prefixes={
            'cpm': 'http://provcpm.org/',
            'ex': 'http://example.org/',
            'dct': 'http://purl.org/dc/terms/',
            'prov': 'http://www.w3.org/ns/prov#'
        },
        bundle_name='ex:highQualityBundle',
        main_activity=MainActivityTemplate(
            id='ex:mainActivity',
            start_time='2024-01-01T10:00:00',
            end_time='2024-01-01T11:00:00',
            attributes={'ex:importance': 'high'}
        ),
        backward_connectors=[
            ConnectorTemplate(
                id='ex:backwardConn1',
                referenced_bundle_id='ex:previousBundle',
                hash_alg='SHA-256',
                referenced_bundle_hash_value='abc123def456'
            )
        ],
        forward_connectors=[
            ConnectorTemplate(
                id='ex:forwardConn1',
                derived_from=['ex:backwardConn1']
            )
        ],
        sender_agents=[AgentTemplate(id='ex:agent1')],
        receiver_agents=[AgentTemplate(id='ex:agent2')]
    )

    # Analyze quality using pipeline
    pipeline = TemplateTransformationPipeline()
    analysis = pipeline.analyze_template_quality(template)

    print("\n Quality Metrics:")
    for key, value in analysis['quality_metrics'].items():
        print(f"  {key}: {value}")

    print(f"\n Quality Level: {analysis['quality_metrics']['quality_level']}")
    print(f" Quality Score: {analysis['quality_metrics']['quality_score']}/6")

    print("\n Statistics:")
    for key, value in analysis['statistics'].items():
        print(f"  {key}: {value}")

    print("\n✅ Python provides comprehensive template analysis")


def demo_agent_overlap_analysis():
    """Demonstrate agent overlap detection (Python-exclusive)"""
    print("\n" + "=" * 60)
    print("DEMO 3: Agent Overlap Analysis (Python-EXCLUSIVE)")
    print("=" * 60)

    # Create template with overlapping agents (same ID as sender and receiver)
    template = TraversalInformationTemplate(
        prefixes={'cpm': 'http://provcpm.org/', 'ex': 'http://example.org/'},
        bundle_name='ex:bundle1',
        main_activity=MainActivityTemplate(id='ex:mainActivity'),
        sender_agents=[
            AgentTemplate(id='ex:agent1', attributes={'role': 'sender'}),
            AgentTemplate(id='ex:agent2')
        ],
        receiver_agents=[
            AgentTemplate(id='ex:agent1', attributes={'role': 'receiver'}),  # Same ID!
            AgentTemplate(id='ex:agent3')
        ]
    )

    # Analyze agent overlap
    analyzer = TemplateAgentAnalyzer(merge_agents=True)
    overlap = analyzer.analyze_agent_overlap(template)

    print(f"\n Total Senders: {overlap['total_senders']}")
    print(f" Total Receivers: {overlap['total_receivers']}")
    print(f" Overlapping Agents: {overlap['overlapping_count']}")
    print(f" Overlapping IDs: {overlap['overlapping_ids']}")
    print(f" Merge Recommended: {overlap['merge_recommended']}")

    if overlap['overlap_details']:
        print("\n Overlap Details:")
        for agent_id, details in overlap['overlap_details'].items():
            print(f"  Agent: {agent_id}")
            print(f"    Conflicts: {details['conflicts']}")
            print(f"    Total attributes: {details['total_attributes']}")

    print("\n✅ Python automates agent overlap detection and merging")


def demo_validation():
    """Demonstrate validation (Python-exclusive features)"""
    print("\n" + "=" * 60)
    print("DEMO 4: Enhanced Validation (Python-EXCLUSIVE)")
    print("=" * 60)

    # Test basic validation (always works)
    validator = TemplateSchemaValidator()

    # Valid template
    valid_data = {
        'bundleName': 'ex:bundle1',
        'mainActivity': {'id': 'ex:mainActivity'},
        'prefixes': {'ex': 'http://example.org/'}
    }

    try:
        validator.validate_template(valid_data)
        print("✅ Valid template passed validation")
    except Exception as e:
        print(f"❌ Validation failed: {e}")

    # Invalid template (missing required field)
    invalid_data = {
        'mainActivity': {'id': 'ex:mainActivity'}
        # Missing bundleName!
    }

    try:
        validator.validate_template(invalid_data)
        print("❌ Should have failed!")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")

    print("\n✅ Python provides enhanced validation with JSON schema")



def demo_full_pipeline():
    """Demonstrate complete processing pipeline (Python-exclusive)"""
    print("\n" + "=" * 60)
    print("DEMO 5: Complete Processing Pipeline (Python-EXCLUSIVE)")
    print("=" * 60)

    # Simulate EMBRC-format data
    embrc_data = {
        'bundleName': 'ex:embrcBundle',
        'mainActivity': {
            'id': 'ex:mainActivity',
            'startTime': '2024-01-01T10:00:00',
            'endTime': '2024-01-01T11:00:00'
        },
        'prefixes': {'ex': 'http://example.org/'}
    }

    # Process through full pipeline
    pipeline = TemplateTransformationPipeline()
    result = pipeline.full_pipeline(embrc_data, source_format="standard")

    print(f"\n✅ Processing successful: {result['processing_successful']}")
    print(f" Source format: {result['source_format']}")
    print(f" Quality level: {result['analysis']['quality_metrics']['quality_level']}")

    # Show statistics
    stats = result['analysis']['statistics']
    print(f"\n Processed template contains:")
    print(f"  - {stats.get('forward_connectors', 0)} forward connectors")
    print(f"  - {stats.get('backward_connectors', 0)} backward connectors")
    print(f"  - {stats.get('sender_agents', 0)} sender agents")
    print(f"  - {stats.get('receiver_agents', 0)} receiver agents")

    print("\n✅ Python provides automated transformation pipelines")





if __name__ == "__main__":
    print("CPM Template Processing - Advanced Features Demo")
    print("Demonstrating Python CPM implementation capabilities\n")

    demo_basic_workflow()
    demo_quality_analysis()
    demo_agent_overlap_analysis()
    demo_validation()
    demo_full_pipeline()


    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

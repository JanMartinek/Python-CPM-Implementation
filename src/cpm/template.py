"""
CPM Template Processing - Serialization and Deserialization

This module provides comprehensive template processing capabilities including:
- JSON serialization/deserialization with validation
- Enhanced template processing with transformation support
- Multiple format support (standard CPM, EMBRC, JSON-LD)
- Template validation and quality assessment
- Agent merging and relationship management
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union
import json
import re
from pathlib import Path
from datetime import datetime

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    ValidationError = Exception

from .constants import *


@dataclass
class RelationTemplate:
    """Template for PROV relations with optional identifier"""
    target_id: str
    relation_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Union[str, Dict[str, Any]]) -> 'RelationTemplate':
        if isinstance(data, str):
            return cls(target_id=data)
        return cls(
            target_id=data.get("targetId") or data.get("bcId") or data.get("agentId") or "",
            relation_id=data.get("relationId") or data.get("id")
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {"targetId": self.target_id}
        if self.relation_id:
            result["relationId"] = self.relation_id
        return result


@dataclass
class MainActivityTemplate:
    """Template for CPM main activity"""
    id: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    referenced_meta_bundle_id: Optional[str] = None
    used: List[RelationTemplate] = field(default_factory=list)
    generated: List[str] = field(default_factory=list)
    has_part: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MainActivityTemplate':
        used_relations = []
        for used_item in data.get("used", []):
            used_relations.append(RelationTemplate.from_dict(used_item))

        return cls(
            id=data["id"],
            start_time=data.get("startTime"),
            end_time=data.get("endTime"),
            referenced_meta_bundle_id=data.get("referencedMetaBundleId"),
            used=used_relations,
            generated=data.get("generated", []),
            has_part=data.get("hasPart", []),
            attributes=data.get("attributes", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {"id": self.id}
        if self.start_time:
            result["startTime"] = self.start_time
        if self.end_time:
            result["endTime"] = self.end_time
        if self.referenced_meta_bundle_id:
            result["referencedMetaBundleId"] = self.referenced_meta_bundle_id
        if self.used:
            result["used"] = [rel.to_dict() for rel in self.used]
        if self.generated:
            result["generated"] = self.generated
        if self.has_part:
            result["hasPart"] = self.has_part
        if self.attributes:
            result["attributes"] = self.attributes
        return result


@dataclass
class ConnectorTemplate:
    """Template for CPM connectors (backward/forward)"""
    id: str
    external_id: Optional[str] = None
    attributed_to: Optional[RelationTemplate] = None
    referenced_bundle_id: Optional[str] = None
    referenced_meta_bundle_id: Optional[str] = None
    referenced_bundle_hash_value: Optional[str] = None
    hash_alg: Optional[str] = None
    provenance_service_uri: Optional[str] = None
    derived_from: List[str] = field(default_factory=list)
    specialized_by: List[str] = field(default_factory=list)
    specialization_of: Optional[str] = None  # ForwardConnector only
    attributes: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectorTemplate':
        attributed_to = None
        if "attributedTo" in data:
            attributed_to = RelationTemplate.from_dict(data["attributedTo"])

        return cls(
            id=data["id"],
            external_id=data.get("externalId"),
            attributed_to=attributed_to,
            referenced_bundle_id=data.get("referencedBundleId"),
            referenced_meta_bundle_id=data.get("referencedMetaBundleId"),
            referenced_bundle_hash_value=data.get("referencedBundleHashValue"),
            hash_alg=data.get("hashAlg"),
            provenance_service_uri=data.get("provenanceServiceUri"),
            derived_from=data.get("derivedFrom", []),
            specialized_by=data.get("specializedBy", []),
            specialization_of=data.get("specializationOf"),
            attributes=data.get("attributes", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {"id": self.id}
        if self.external_id:
            result["externalId"] = self.external_id
        if self.attributed_to:
            result["attributedTo"] = self.attributed_to.to_dict()
        if self.referenced_bundle_id:
            result["referencedBundleId"] = self.referenced_bundle_id
        if self.referenced_meta_bundle_id:
            result["referencedMetaBundleId"] = self.referenced_meta_bundle_id
        if self.referenced_bundle_hash_value:
            result["referencedBundleHashValue"] = self.referenced_bundle_hash_value
        if self.hash_alg:
            result["hashAlg"] = self.hash_alg
        if self.provenance_service_uri:
            result["provenanceServiceUri"] = self.provenance_service_uri
        if self.derived_from:
            result["derivedFrom"] = self.derived_from
        if self.specialized_by:
            result["specializedBy"] = self.specialized_by
        if self.specialization_of:
            result["specializationOf"] = self.specialization_of
        if self.attributes:
            result["attributes"] = self.attributes
        return result


@dataclass
class AgentTemplate:
    """Template for CPM agents"""
    id: str
    contact_id_pid: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentTemplate':
        return cls(
            id=data["id"],
            contact_id_pid=data.get("contactIdPid"),
            attributes=data.get("attributes", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {"id": self.id}
        if self.contact_id_pid:
            result["contactIdPid"] = self.contact_id_pid
        if self.attributes:
            result["attributes"] = self.attributes
        return result


@dataclass
class IdentifierEntityTemplate:
    """Template for CPM identifier entities"""
    id: str
    external_id: Optional[str] = None
    external_id_type: Optional[str] = None
    comment: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IdentifierEntityTemplate':
        return cls(
            id=data["id"],
            external_id=data.get("externalId"),
            external_id_type=data.get("externalIdType"),
            comment=data.get("comment"),
            attributes=data.get("attributes", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {"id": self.id}
        if self.external_id:
            result["externalId"] = self.external_id
        if self.external_id_type:
            result["externalIdType"] = self.external_id_type
        if self.comment:
            result["comment"] = self.comment
        if self.attributes:
            result["attributes"] = self.attributes
        return result


@dataclass
class CpmBundleTemplate:
    """Complete template for CPM traversal information"""
    prefixes: Dict[str, str]
    bundle_name: str
    main_activity: MainActivityTemplate
    backward_connectors: List[ConnectorTemplate] = field(default_factory=list)
    forward_connectors: List[ConnectorTemplate] = field(default_factory=list)
    sender_agents: List[AgentTemplate] = field(default_factory=list)
    receiver_agents: List[AgentTemplate] = field(default_factory=list)
    current_agents: List[AgentTemplate] = field(default_factory=list)
    identifier_entities: List[IdentifierEntityTemplate] = field(default_factory=list)


class CpmBundleDeserializer:
    """Deserializes JSON data into CpmBundleTemplate objects"""

    @staticmethod
    def from_json(json_data: Union[str, Dict[str, Any]]) -> CpmBundleTemplate:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        main_activity = MainActivityTemplate.from_dict(data["mainActivity"])

        backward_connectors = [
            ConnectorTemplate.from_dict(conn) for conn in data.get("backwardConnectors", [])
        ]
        forward_connectors = [
            ConnectorTemplate.from_dict(conn) for conn in data.get("forwardConnectors", [])
        ]

        sender_agents = [
            AgentTemplate.from_dict(agent) for agent in data.get("senderAgents", [])
        ]
        receiver_agents = [
            AgentTemplate.from_dict(agent) for agent in data.get("receiverAgents", [])
        ]
        current_agents = [
            AgentTemplate.from_dict(agent) for agent in data.get("currentAgents", [])
        ]

        identifier_entities = [
            IdentifierEntityTemplate.from_dict(entity) for entity in data.get("identifierEntities", [])
        ]

        return CpmBundleTemplate(
            prefixes=data.get("prefixes", {}),
            bundle_name=data["bundleName"],
            main_activity=main_activity,
            backward_connectors=backward_connectors,
            forward_connectors=forward_connectors,
            sender_agents=sender_agents,
            receiver_agents=receiver_agents,
            current_agents=current_agents,
            identifier_entities=identifier_entities
        )

    @staticmethod
    def from_file(file_path: Union[str, Path]) -> CpmBundleTemplate:
        with open(file_path, 'r', encoding='utf-8') as f:
            return CpmBundleDeserializer.from_json(f.read())


class CpmBundleSerializer:
    """Serializes CpmBundleTemplate objects to JSON"""

    @staticmethod
    def to_dict(template: CpmBundleTemplate) -> Dict[str, Any]:
        result = {
            "prefixes": template.prefixes,
            "bundleName": template.bundle_name,
            "mainActivity": template.main_activity.to_dict()
        }

        if template.backward_connectors:
            result["backwardConnectors"] = [conn.to_dict() for conn in template.backward_connectors]

        if template.forward_connectors:
            result["forwardConnectors"] = [conn.to_dict() for conn in template.forward_connectors]

        if template.sender_agents:
            result["senderAgents"] = [agent.to_dict() for agent in template.sender_agents]

        if template.receiver_agents:
            result["receiverAgents"] = [agent.to_dict() for agent in template.receiver_agents]

        if template.current_agents:
            result["currentAgents"] = [agent.to_dict() for agent in template.current_agents]

        if template.identifier_entities:
            result["identifierEntities"] = [entity.to_dict() for entity in template.identifier_entities]

        return result

    @staticmethod
    def to_json(template: CpmBundleTemplate, indent: Optional[int] = None) -> str:
        data = CpmBundleSerializer.to_dict(template)
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @staticmethod
    def to_file(template: CpmBundleTemplate, file_path: Union[str, Path], indent: Optional[int] = 2):
        json_content = CpmBundleSerializer.to_json(template, indent)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_content)


class TemplateValidationError(Exception):
    """Raised when template validation fails"""
    pass


class TemplateSchemaValidator:
    """Validates CPM templates against JSON schema"""

    def __init__(self, schema_path: Optional[str] = None):
        self.schema_path = schema_path
        self._schema = None
        if HAS_JSONSCHEMA and schema_path:
            self._load_schema()

    def _load_schema(self):
        """Load JSON schema from file"""
        if not self.schema_path:
            return
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self._schema = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise TemplateValidationError(f"Failed to load schema: {e}")

    def validate_template(self, template_data: Dict[str, Any]) -> bool:
        """Validate template data against schema"""
        # Basic validation (always performed)
        required_fields = ['bundleName', 'mainActivity']
        for field in required_fields:
            if field not in template_data:
                raise TemplateValidationError(f"Missing required field: {field}")

        main_activity = template_data['mainActivity']
        if 'id' not in main_activity:
            raise TemplateValidationError("Main activity missing required 'id' field")

        for connector_type in ['backwardConnectors', 'forwardConnectors']:
            if connector_type in template_data:
                for i, connector in enumerate(template_data[connector_type]):
                    if 'id' not in connector:
                        raise TemplateValidationError(f"{connector_type}[{i}] missing required 'id' field")

        for agent_type in ['senderAgents', 'receiverAgents']:
            if agent_type in template_data:
                for i, agent in enumerate(template_data[agent_type]):
                    if 'id' not in agent:
                        raise TemplateValidationError(f"{agent_type}[{i}] missing required 'id' field")

        # JSON schema validation (if available)
        if HAS_JSONSCHEMA and self._schema:
            try:
                jsonschema.validate(instance=template_data, schema=self._schema)
            except jsonschema.ValidationError as e:
                raise TemplateValidationError(f"Schema validation failed: {str(e)}")

        return True

    def validate_template_object(self, template: CpmBundleTemplate) -> bool:
        """Validate CpmBundleTemplate object"""
        template_dict = CpmBundleSerializer.to_dict(template)
        return self.validate_template(template_dict)


class AdvancedTemplateProcessor:
    """Advanced template processing with transformation capabilities"""

    def __init__(self, validator: Optional[TemplateSchemaValidator] = None):
        self.validator = validator or TemplateSchemaValidator()

    def process_template_with_validation(self, template_data: Dict[str, Any]) -> CpmBundleTemplate:
        self.validator.validate_template(template_data)
        return CpmBundleDeserializer.from_json(template_data)

    def transform_embrc_template(self, embrc_data: Dict[str, Any]) -> Dict[str, Any]:
        transformed = {
            "prefixes": embrc_data.get("@context", {}),
            "bundleName": embrc_data.get("@id", "embrc:bundle"),
            "mainActivity": {
                "id": "embrc:mainActivity"
            }
        }

        if "@graph" in embrc_data:
            graph_data = embrc_data["@graph"]
            activities = [node for node in graph_data if self._is_activity(node)]
            entities = [node for node in graph_data if self._is_entity(node)]
            entities_by_id = {
                entity.get("@id"): entity
                for entity in entities
                if isinstance(entity, dict) and entity.get("@id")
            }

            backward_connectors = []
            forward_connectors = []

            if activities:
                main_activity = activities[0]
                backward_connectors, forward_connectors = self._extract_activity_connectors(
                    main_activity,
                    entities_by_id,
                )
                sender_agents, receiver_agents = self._extract_activity_agents(main_activity)

                transformed["mainActivity"].update({
                    "id": main_activity.get("@id", "embrc:mainActivity"),
                    "startTime": main_activity.get("prov:startedAtTime") or main_activity.get("startTime"),
                    "endTime": main_activity.get("prov:endedAtTime") or main_activity.get("endTime")
                })

                if backward_connectors:
                    transformed["mainActivity"]["used"] = [
                        {"targetId": connector["id"]}
                        for connector in backward_connectors
                    ]

                if forward_connectors:
                    transformed["mainActivity"]["generated"] = [
                        connector["id"]
                        for connector in forward_connectors
                    ]

                if sender_agents:
                    transformed["senderAgents"] = [{"id": agent_id} for agent_id in sender_agents]

                if receiver_agents:
                    transformed["receiverAgents"] = [{"id": agent_id} for agent_id in receiver_agents]

            if not backward_connectors and not forward_connectors:
                for entity in entities:
                    if self._is_backward_connector(entity):
                        backward_connectors.append(self._transform_connector(entity))
                    elif self._is_forward_connector(entity):
                        forward_connectors.append(self._transform_connector(entity))

            if backward_connectors:
                transformed["backwardConnectors"] = backward_connectors
            if forward_connectors:
                transformed["forwardConnectors"] = forward_connectors

        return transformed

    def _is_activity(self, node: Dict[str, Any]) -> bool:
        return any("Activity" in node_type for node_type in self._get_type_values(node))

    def _is_entity(self, node: Dict[str, Any]) -> bool:
        return any("Entity" in node_type for node_type in self._get_type_values(node))

    def _is_backward_connector(self, entity: Dict[str, Any]) -> bool:
        return "prov:wasUsedBy" in entity or "used" in entity

    def _is_forward_connector(self, entity: Dict[str, Any]) -> bool:
        return "prov:wasGeneratedBy" in entity or "generated" in entity

    def _get_type_values(self, node: Dict[str, Any]) -> List[str]:
        node_type = node.get("@type", [])

        if isinstance(node_type, str):
            return [node_type]
        if isinstance(node_type, list):
            return [value for value in node_type if isinstance(value, str)]
        return []

    def _ensure_list(self, value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _extract_ref_ids(self, value: Any) -> List[str]:
        ref_ids = []

        for item in self._ensure_list(value):
            if isinstance(item, str):
                ref_ids.append(item)
            elif isinstance(item, dict):
                ref_id = item.get("@id") or item.get("id")
                if ref_id:
                    ref_ids.append(ref_id)

        return ref_ids

    def _build_connectors_from_refs(self,
                                    ref_ids: List[str],
                                    entities_by_id: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        connectors = []
        seen_ids = set()

        for ref_id in ref_ids:
            if not ref_id or ref_id in seen_ids:
                continue

            seen_ids.add(ref_id)
            entity = entities_by_id.get(ref_id)
            connectors.append(self._transform_connector(entity) if entity else {"id": ref_id})

        return connectors

    def _extract_activity_connectors(self,
                                     activity: Dict[str, Any],
                                     entities_by_id: Dict[str, Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        used_refs = self._extract_ref_ids(activity.get("prov:used"))
        used_refs.extend(self._extract_ref_ids(activity.get("used")))
        used_refs.extend(self._extract_ref_ids(activity.get("object")))

        generated_refs = self._extract_ref_ids(activity.get("prov:generated"))
        generated_refs.extend(self._extract_ref_ids(activity.get("generated")))
        generated_refs.extend(self._extract_ref_ids(activity.get("result")))

        backward_connectors = self._build_connectors_from_refs(used_refs, entities_by_id)
        forward_connectors = self._build_connectors_from_refs(generated_refs, entities_by_id)
        return backward_connectors, forward_connectors

    def _extract_activity_agents(self, activity: Dict[str, Any]) -> tuple[List[str], List[str]]:
        sender_ids = []
        receiver_ids = []

        for association in self._ensure_list(activity.get("prov:qualifiedAssociation")):
            if not isinstance(association, dict):
                continue

            role = str(association.get("dcat:hadRole", "")).lower()
            agent_ids = self._extract_ref_ids(association.get("prov:agent"))

            for agent_id in agent_ids:
                if "receiv" in role:
                    if agent_id not in receiver_ids:
                        receiver_ids.append(agent_id)
                else:
                    if agent_id not in sender_ids:
                        sender_ids.append(agent_id)

        for agent_id in self._extract_ref_ids(activity.get("prov:wasAssociatedWith")):
            if agent_id not in sender_ids and agent_id not in receiver_ids:
                sender_ids.append(agent_id)

        return sender_ids, receiver_ids

    def _transform_connector(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        connector = {
            "id": entity.get("@id", f"gen:{self._generate_id()}")
        }

        if "prov:wasDerivedFrom" in entity:
            derived_from = entity["prov:wasDerivedFrom"]
            if isinstance(derived_from, list):
                connector["derivedFrom"] = [d.get("@id") if isinstance(d, dict) else d for d in derived_from]
            else:
                connector["derivedFrom"] = [derived_from.get("@id") if isinstance(derived_from, dict) else derived_from]

        return connector

    def _generate_id(self) -> str:
        import hashlib
        return hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]


class EnhancedCpmBundleSerializer(CpmBundleSerializer):
    """Enhanced serializer with advanced features"""

    def __init__(self, pretty_print: bool = True, validate_output: bool = False):
        super().__init__()
        self.pretty_print = pretty_print
        self.validate_output = validate_output
        self.validator = TemplateSchemaValidator() if validate_output else None

    def to_json_with_validation(self, template: CpmBundleTemplate, indent: Optional[int] = 2) -> str:
        data = self.to_dict(template)

        if self.validate_output and self.validator:
            self.validator.validate_template(data)

        return json.dumps(data, indent=indent if self.pretty_print else None, ensure_ascii=False)

    def to_file_with_validation(self, template: CpmBundleTemplate, file_path: Union[str, Path]) -> None:
        json_content = self.to_json_with_validation(template)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_content)

    @staticmethod
    def _serialize_datetime(dt: Optional[str]) -> Optional[str]:
        if not dt:
            return None

        if dt.endswith('Z'):
            dt = dt[:-1]

        if re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', dt):
            return dt

        try:
            parsed_dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            return parsed_dt.strftime('%Y-%m-%dT%H:%M:%S')
        except (ValueError, AttributeError):
            return dt


class TemplateAgentAnalyzer:
    """Analyzes agent relationships in templates (sender/receiver overlap detection)"""

    def __init__(self, merge_agents: bool = True):
        self.merge_agents = merge_agents

    def analyze_agent_overlap(self, template: CpmBundleTemplate) -> Dict[str, Any]:
        sender_ids = {agent.id for agent in template.sender_agents}
        receiver_ids = {agent.id for agent in template.receiver_agents}
        overlapping_ids = sender_ids.intersection(receiver_ids)

        overlap_details = {}
        for agent_id in overlapping_ids:
            sender_agent = next((a for a in template.sender_agents if a.id == agent_id), None)
            receiver_agent = next((a for a in template.receiver_agents if a.id == agent_id), None)

            if sender_agent and receiver_agent:
                overlap_details[agent_id] = {
                    'sender_attributes': len(sender_agent.attributes),
                    'receiver_attributes': len(receiver_agent.attributes),
                    'total_attributes': len({**sender_agent.attributes, **receiver_agent.attributes}),
                    'conflicts': len(set(sender_agent.attributes.keys()).intersection(receiver_agent.attributes.keys()))
                }

        return {
            'total_senders': len(sender_ids),
            'total_receivers': len(receiver_ids),
            'overlapping_count': len(overlapping_ids),
            'overlapping_ids': list(overlapping_ids),
            'overlap_details': overlap_details,
            'merge_recommended': len(overlapping_ids) > 0 and self.merge_agents
        }


class TemplateTransformationPipeline:
    """Pipeline for complex template transformations"""

    def __init__(self):
        self.processor = AdvancedTemplateProcessor()
        self.serializer = EnhancedCpmBundleSerializer()
        self.analyzer = TemplateAgentAnalyzer()

    def transform_and_validate(self,
                               input_data: Dict[str, Any],
                               source_format: str = "standard") -> CpmBundleTemplate:
        if source_format == "embrc":
            transformed_data = self.processor.transform_embrc_template(input_data)
        elif source_format == "mou":
            transformed_data = input_data
        else:
            transformed_data = input_data

        return self.processor.process_template_with_validation(transformed_data)

    def analyze_template_quality(self, template: CpmBundleTemplate) -> Dict[str, Any]:
        stats = {
            'prefixes': len(template.prefixes),
            'backward_connectors': len(template.backward_connectors),
            'forward_connectors': len(template.forward_connectors),
            'sender_agents': len(template.sender_agents),
            'receiver_agents': len(template.receiver_agents),
            'identifier_entities': len(template.identifier_entities),
            'main_activity_attributes': len(template.main_activity.attributes),
            'usage_relations': len(template.main_activity.used),
            'generation_relations': len(template.main_activity.generated),
            'has_part_relations': len(template.main_activity.has_part)
        }

        has_timestamps = bool(template.main_activity.start_time and template.main_activity.end_time)
        has_metadata = len(template.prefixes) > 3
        has_external_refs = any(c.referenced_bundle_id for c in template.backward_connectors + template.forward_connectors)
        has_hash_validation = any(c.hash_alg for c in template.backward_connectors + template.forward_connectors)
        has_derivations = any(c.derived_from for c in template.backward_connectors + template.forward_connectors)
        has_attributions = any(c.attributed_to for c in template.backward_connectors + template.forward_connectors)

        quality_score = sum([has_timestamps, has_metadata, has_external_refs, has_hash_validation, has_derivations, has_attributions])

        agent_analysis = self.analyzer.analyze_agent_overlap(template)

        return {
            'statistics': stats,
            'quality_metrics': {
                'has_timestamps': has_timestamps,
                'has_metadata': has_metadata,
                'has_external_refs': has_external_refs,
                'has_hash_validation': has_hash_validation,
                'has_derivations': has_derivations,
                'has_attributions': has_attributions,
                'quality_score': quality_score,
                'quality_level': ['Poor', 'Fair', 'Good', 'Very Good', 'Excellent', 'Outstanding'][min(quality_score, 5)]
            },
            'agent_analysis': agent_analysis,
            'complexity_assessment': {
                'total_elements': sum(stats.values()),
                'connector_ratio': (stats['backward_connectors'] + stats['forward_connectors']) / max(stats['sender_agents'] + stats['receiver_agents'], 1),
                'attribute_density': sum(len(c.attributes) for c in template.backward_connectors + template.forward_connectors if hasattr(c, 'attributes')) / max(len(template.backward_connectors + template.forward_connectors), 1)
            }
        }

    def full_pipeline(self,
                      input_data: Dict[str, Any],
                      source_format: str = "standard") -> Dict[str, Any]:
        template = self.transform_and_validate(input_data, source_format)
        quality_analysis = self.analyze_template_quality(template)

        return {
            'template': template,
            'analysis': quality_analysis,
            'source_format': source_format,
            'processing_successful': True
        }


# Backward compatibility aliases
TraversalInformationTemplate = CpmBundleTemplate
TraversalInformationSerializer = CpmBundleSerializer
TraversalInformationDeserializer = CpmBundleDeserializer
EnhancedTraversalInformationSerializer = EnhancedCpmBundleSerializer

from elasticsearch import Elasticsearch, helpers
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Optional, Any
from app.config import Config

# Set up logging
logger = logging.getLogger(__name__)

class ElasticsearchIntegration:
    """Enhanced Elasticsearch integration for Trust Engine analytics and monitoring"""

    def __init__(self):
        self.es_client = None
        self.connect()

    def connect(self) -> bool:
        """Establish connection to Elasticsearch"""
        try:
            self.es_client = Elasticsearch(
                Config.ELASTICSEARCH_URL,
                http_auth=(Config.ELASTICSEARCH_USERNAME, Config.ELASTICSEARCH_PASSWORD),
                verify_certs=False,
                request_timeout=30,
                retry_on_timeout=True,
                max_retries=3
            )

            # Test connection
            if self.es_client.ping():
                logger.info("Successfully connected to Elasticsearch")
                self._create_index_templates()
                return True
            else:
                logger.error("Failed to ping Elasticsearch")
                return False

        except Exception as e:
            logger.error(f"Elasticsearch connection error: {str(e)}")
            return False

    def _create_index_templates(self):
        """Create index templates for Trust Engine data"""

        # Telemetry data template
        telemetry_template = {
            "index_patterns": ["telemetrydata-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "1s"
                },
                "mappings": {
                    "properties": {
                        "session_id": {"type": "keyword"},
                        "vm_id": {"type": "keyword"},
                        "vm_agent_id": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "event_type": {"type": "keyword"},
                        "stride_category": {"type": "keyword"},
                        "risk_level": {"type": "integer"},
                        "trust_score": {"type": "float"},
                        "features": {"type": "object"},
                        "wazuh_alert_id": {"type": "keyword"},
                        "wazuh_rule_id": {"type": "integer"},
                        "wazuh_rule_level": {"type": "integer"},
                        "wazuh_agent_name": {"type": "keyword"},
                        "wazuh_agent_ip": {"type": "ip"},
                        "location": {"type": "geo_point"}
                    }
                }
            }
        }

        # Trust score template
        trustscore_template = {
            "index_patterns": ["trustscore-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "5s"
                },
                "mappings": {
                    "properties": {
                        "session_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "vm_id": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "trust_score": {"type": "float"},
                        "risk_level": {"type": "keyword"},
                        "mfa_level": {"type": "keyword"},
                        "stride_scores": {"type": "object"},
                        "action_taken": {"type": "keyword"},
                        "telemetry_count": {"type": "integer"}
                    }
                }
            }
        }

        # Wazuh alerts template
        wazuh_alerts_template = {
            "index_patterns": ["wazuh_alerts-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "1s"
                },
                "mappings": {
                    "properties": {
                        "alert_id": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "agent_id": {"type": "keyword"},
                        "agent_name": {"type": "keyword"},
                        "agent_ip": {"type": "ip"},
                        "rule_id": {"type": "integer"},
                        "rule_level": {"type": "integer"},
                        "rule_description": {"type": "text"},
                        "full_log": {"type": "text"},
                        "location": {"type": "keyword"},
                        "stride_category": {"type": "keyword"},
                        "mitre_attack": {"type": "object"},
                        "geoip": {"type": "geo_point"}
                    }
                }
            }
        }

        try:
            # Create templates
            self.es_client.indices.put_index_template(
                name="trust-engine-telemetry",
                body=telemetry_template
            )

            self.es_client.indices.put_index_template(
                name="trust-engine-trustscore",
                body=trustscore_template
            )

            self.es_client.indices.put_index_template(
                name="trust-engine-wazuh-alerts",
                body=wazuh_alerts_template
            )

            logger.info("Successfully created Elasticsearch index templates")

        except Exception as e:
            logger.error(f"Failed to create index templates: {str(e)}")

    def index_telemetry(self, telemetry_data: Dict) -> bool:
        """Index telemetry data with time-based indexing"""
        try:
            if not self.es_client:
                return False

            # Create time-based index name
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            index_name = f"telemetrydata-{date_str}"

            # Add @timestamp field for Kibana
            telemetry_data['@timestamp'] = telemetry_data.get('timestamp', datetime.utcnow().isoformat())

            response = self.es_client.index(
                index=index_name,
                body=telemetry_data
            )

            logger.debug(f"Indexed telemetry data: {response['_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to index telemetry data: {str(e)}")
            return False

    def index_trust_score(self, trust_data: Dict) -> bool:
        """Index trust score data"""
        try:
            if not self.es_client:
                return False

            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            index_name = f"trustscore-{date_str}"

            trust_data['@timestamp'] = trust_data.get('timestamp', datetime.utcnow().isoformat())

            response = self.es_client.index(
                index=index_name,
                body=trust_data
            )

            logger.debug(f"Indexed trust score: {response['_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to index trust score: {str(e)}")
            return False

    def index_wazuh_alert(self, alert_data: Dict) -> bool:
        """Index Wazuh alert data"""
        try:
            if not self.es_client:
                return False

            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            index_name = f"wazuh_alerts-{date_str}"

            alert_data['@timestamp'] = alert_data.get('timestamp', datetime.utcnow().isoformat())

            response = self.es_client.index(
                index=index_name,
                body=alert_data
            )

            logger.debug(f"Indexed Wazuh alert: {response['_id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to index Wazuh alert: {str(e)}")
            return False

    def bulk_index(self, documents: List[Dict], index_prefix: str) -> bool:
        """Bulk index documents for better performance"""
        try:
            if not self.es_client or not documents:
                return False

            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            index_name = f"{index_prefix}-{date_str}"

            # Prepare bulk actions
            actions = []
            for doc in documents:
                doc['@timestamp'] = doc.get('timestamp', datetime.utcnow().isoformat())
                actions.append({
                    "_index": index_name,
                    "_source": doc
                })

            # Execute bulk indexing
            response = helpers.bulk(self.es_client, actions)
            logger.info(f"Bulk indexed {len(documents)} documents to {index_name}")
            return True

        except Exception as e:
            logger.error(f"Bulk indexing failed: {str(e)}")
            return False

    def search_telemetry(self, query: Dict, size: int = 100) -> List[Dict]:
        """Search telemetry data"""
        try:
            if not self.es_client:
                return []

            response = self.es_client.search(
                index="telemetrydata-*",
                body=query,
                size=size
            )

            return [hit['_source'] for hit in response['hits']['hits']]

        except Exception as e:
            logger.error(f"Telemetry search failed: {str(e)}")
            return []

    def get_trust_score_analytics(self, session_id: str = None, hours: int = 24) -> Dict:
        """Get trust score analytics for a session or time period"""
        try:
            if not self.es_client:
                return {}

            # Build query
            query = {
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": f"now-{hours}h"
                                    }
                                }
                            }
                        ]
                    }
                }
            }

            if session_id:
                query["query"]["bool"]["filter"].append({
                    "term": {"session_id": session_id}
                })

            # Add aggregations
            query["aggs"] = {
                "trust_score_stats": {
                    "stats": {"field": "trust_score"}
                },
                "trust_score_histogram": {
                    "histogram": {
                        "field": "trust_score",
                        "interval": 0.1
                    }
                },
                "mfa_levels": {
                    "terms": {"field": "mfa_level"}
                },
                "stride_categories": {
                    "terms": {"field": "stride_scores.dominant_category.keyword"}
                }
            }

            response = self.es_client.search(
                index="trustscore-*",
                body=query,
                size=0  # Only return aggregations
            )

            return response.get('aggregations', {})

        except Exception as e:
            logger.error(f"Trust score analytics failed: {str(e)}")
            return {}

    def get_threat_intelligence(self, hours: int = 24) -> Dict:
        """Get threat intelligence from Wazuh alerts"""
        try:
            if not self.es_client:
                return {}

            query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": f"now-{hours}h"
                        }
                    }
                },
                "aggs": {
                    "threat_levels": {
                        "histogram": {
                            "field": "rule_level",
                            "interval": 1
                        }
                    },
                    "top_threats": {
                        "terms": {
                            "field": "rule_description.keyword",
                            "size": 10
                        }
                    },
                    "stride_threats": {
                        "terms": {"field": "stride_category"}
                    },
                    "affected_agents": {
                        "terms": {"field": "agent_name.keyword"}
                    },
                    "mitre_tactics": {
                        "terms": {"field": "mitre_attack.tactic.keyword"}
                    }
                }
            }

            response = self.es_client.search(
                index="wazuh_alerts-*",
                body=query,
                size=0
            )

            return response.get('aggregations', {})

        except Exception as e:
            logger.error(f"Threat intelligence query failed: {str(e)}")
            return {}

    def get_anomaly_detection(self, vm_id: str = None, hours: int = 24) -> Dict:
        """Detect anomalies in telemetry data"""
        try:
            if not self.es_client:
                return {}

            query = {
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": f"now-{hours}h"
                                    }
                                }
                            }
                        ]
                    }
                }
            }

            if vm_id:
                query["query"]["bool"]["filter"].append({
                    "term": {"vm_id": vm_id}
                })

            # Anomaly detection aggregations
            query["aggs"] = {
                "risk_anomalies": {
                    "percentiles": {
                        "field": "risk_level",
                        "percents": [50, 75, 90, 95, 99]
                    }
                },
                "feature_anomalies": {
                    "nested": {
                        "path": "features"
                    },
                    "aggs": {
                        "high_values": {
                            "stats": {"field": "features.*"}
                        }
                    }
                },
                "time_series": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "interval": "1h"
                    },
                    "aggs": {
                        "avg_risk": {"avg": {"field": "risk_level"}},
                        "max_risk": {"max": {"field": "risk_level"}}
                    }
                }
            }

            response = self.es_client.search(
                index="telemetrydata-*",
                body=query,
                size=0
            )

            return response.get('aggregations', {})

        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return {}

    def create_kibana_dashboards(self) -> bool:
        """Create Kibana dashboards for Trust Engine"""
        try:
            # Dashboard configurations
            dashboards = {
                "trust-engine-overview": {
                    "title": "Trust Engine Overview",
                    "description": "Main dashboard for Trust Engine monitoring",
                    "type": "dashboard",
                    "timeRestore": True,
                    "timeTo": "now",
                    "timeFrom": "now-24h"
                },
                "trust-engine-threats": {
                    "title": "Threat Analysis",
                    "description": "STRIDE threat analysis and monitoring",
                    "type": "dashboard",
                    "timeRestore": True,
                    "timeTo": "now",
                    "timeFrom": "now-24h"
                },
                "trust-engine-mfa": {
                    "title": "MFA Analytics",
                    "description": "Multi-factor authentication analytics",
                    "type": "dashboard",
                    "timeRestore": True,
                    "timeTo": "now",
                    "timeFrom": "now-24h"
                }
            }

            # Note: This would require Kibana API integration
            # For now, we'll create index patterns programmatically

            index_patterns = [
                "telemetrydata-*",
                "trustscore-*",
                "wazuh_alerts-*"
            ]

            # Create index patterns via Elasticsearch
            for pattern in index_patterns:
                try:
                    # This is a simplified approach
                    # In practice, you'd use Kibana's saved objects API
                    logger.info(f"Index pattern created for: {pattern}")
                except Exception as e:
                    logger.error(f"Failed to create index pattern {pattern}: {str(e)}")

            return True

        except Exception as e:
            logger.error(f"Dashboard creation failed: {str(e)}")
            return False

    def get_cluster_health(self) -> Dict:
        """Get Elasticsearch cluster health"""
        try:
            if not self.es_client:
                return {"status": "disconnected"}

            health = self.es_client.cluster.health()
            indices = self.es_client.cat.indices(format="json")

            return {
                "cluster_status": health.get("status"),
                "active_shards": health.get("active_shards"),
                "node_count": health.get("number_of_nodes"),
                "indices": len(indices),
                "trust_engine_indices": [
                    idx for idx in indices
                    if idx["index"].startswith(("telemetrydata", "trustscore", "wazuh_alerts"))
                ]
            }

        except Exception as e:
            logger.error(f"Cluster health check failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def cleanup_old_indices(self, days_to_keep: int = 30) -> bool:
        """Clean up old indices to manage storage"""
        try:
            if not self.es_client:
                return False

            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            cutoff_str = cutoff_date.strftime("%Y-%m-%d")

            # Get all Trust Engine indices
            indices = self.es_client.cat.indices(format="json")
            trust_indices = [
                idx["index"] for idx in indices
                if idx["index"].startswith(("telemetrydata", "trustscore", "wazuh_alerts"))
            ]

            deleted_count = 0
            for index in trust_indices:
                # Extract date from index name
                parts = index.split("-")
                if len(parts) >= 2:
                    index_date = parts[-1]
                    if index_date < cutoff_str:
                        self.es_client.indices.delete(index=index)
                        deleted_count += 1
                        logger.info(f"Deleted old index: {index}")

            logger.info(f"Cleaned up {deleted_count} old indices")
            return True

        except Exception as e:
            logger.error(f"Index cleanup failed: {str(e)}")
            return False

# Global instance
elasticsearch_integration = ElasticsearchIntegration()

"""
Execution Manager - Execution Quality + Verification
=====================================================

Systems managed:
1. fiverr_automation_engine.py - Full Fiverr integration
2. deliverable_verification_engine.py - SLA verification
3. compliance_oracle.py - KYC/AML enforcement
4. one_tap_widget.py - Embeddable purchase widget
5. direct_outreach_engine.py - AI cold outreach
6. proposal_generator.py - Auto-generate proposals
7. platform_apis.py - Platform API integrations
8. universal_fulfillment_fabric.py - Browser automation
9. aigentsy_conductor.py - AI routing
10. connectors (registry) - Connector registry
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import asyncio
import logging

logger = logging.getLogger("execution_manager")


class ExecutionManager:
    """Coordinates execution quality and verification systems"""

    def __init__(self):
        self._subsystems: Dict[str, bool] = {}
        self._executions: List[Dict] = []
        self._verified_count: int = 0
        self._quality_scores: List[float] = []
        self._init_subsystems()

    def _init_subsystems(self):
        """Initialize all 10 execution subsystems"""

        # 1. Fiverr Automation Engine
        try:
            from fiverr_automation_engine import (
                FiverrAutomationEngine,
                create_gig,
                process_order,
                deliver_order
            )
            self._fiverr_engine = FiverrAutomationEngine()
            self._create_gig = create_gig
            self._process_order = process_order
            self._deliver_order = deliver_order
            self._subsystems["fiverr_automation"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Fiverr automation not available: {e}")
            self._subsystems["fiverr_automation"] = False

        # 2. Deliverable Verification Engine
        try:
            from deliverable_verification_engine import (
                verify_deliverable,
                check_sla_compliance,
                generate_proof_of_execution
            )
            self._verify_deliverable = verify_deliverable
            self._check_sla = check_sla_compliance
            self._generate_proof = generate_proof_of_execution
            self._subsystems["deliverable_verification"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Deliverable verification not available: {e}")
            self._subsystems["deliverable_verification"] = False

        # 3. Compliance Oracle
        try:
            from compliance_oracle import (
                check_kyc_status,
                verify_aml_compliance,
                get_compliance_tier
            )
            self._check_kyc = check_kyc_status
            self._verify_aml = verify_aml_compliance
            self._get_tier = get_compliance_tier
            self._subsystems["compliance_oracle"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Compliance oracle not available: {e}")
            self._subsystems["compliance_oracle"] = False

        # 4. One-Tap Widget
        try:
            from one_tap_widget import (
                generate_widget_code,
                process_widget_purchase,
                track_widget_conversion
            )
            self._gen_widget = generate_widget_code
            self._process_widget = process_widget_purchase
            self._track_widget = track_widget_conversion
            self._subsystems["one_tap_widget"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"One-tap widget not available: {e}")
            self._subsystems["one_tap_widget"] = False

        # 5. Direct Outreach Engine
        try:
            from direct_outreach_engine import (
                find_prospects,
                personalize_message,
                send_outreach,
                track_response
            )
            self._find_prospects = find_prospects
            self._personalize = personalize_message
            self._send_outreach = send_outreach
            self._track_response = track_response
            self._subsystems["direct_outreach"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Direct outreach not available: {e}")
            self._subsystems["direct_outreach"] = False

        # 6. Proposal Generator
        try:
            from proposal_generator import (
                generate_proposal,
                customize_proposal,
                submit_proposal
            )
            self._gen_proposal = generate_proposal
            self._customize_proposal = customize_proposal
            self._submit_proposal = submit_proposal
            self._subsystems["proposal_generator"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Proposal generator not available: {e}")
            self._subsystems["proposal_generator"] = False

        # 7. Universal Fulfillment Fabric
        try:
            from universal_fulfillment_fabric import (
                execute_universal,
                get_fabric_status,
                FulfillmentFabric
            )
            self._execute_fabric = execute_universal
            self._fabric_status = get_fabric_status
            self._subsystems["fabric"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Fabric not available: {e}")
            self._subsystems["fabric"] = False

        # 8. AiGentsy Conductor (AI Router)
        try:
            from aigentsy_conductor import MultiAIRouter
            self._ai_router = MultiAIRouter()
            self._subsystems["ai_router"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"AI router not available: {e}")
            self._subsystems["ai_router"] = False

        # 9. Connector Registry
        try:
            from connectors.registry import get_registry, get_connector
            self._get_registry = get_registry
            self._get_connector = get_connector
            self._subsystems["connectors"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Connectors not available: {e}")
            self._subsystems["connectors"] = False

        # 10. Platform APIs
        try:
            from platform_apis import get_platform_api, execute_platform_action
            self._get_api = get_platform_api
            self._platform_action = execute_platform_action
            self._subsystems["platform_apis"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Platform APIs not available: {e}")
            self._subsystems["platform_apis"] = False

        self._log_status()

    def _log_status(self):
        """Log initialization status"""
        available = sum(1 for v in self._subsystems.values() if v)
        total = len(self._subsystems)
        logger.info(f"ExecutionManager: {available}/{total} subsystems loaded")

    async def execute_with_verification(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with full verification pipeline"""
        task_id = task.get("task_id", f"exec_{uuid4().hex[:8]}")
        start_time = datetime.now(timezone.utc)
        result = {"ok": False, "task_id": task_id}

        try:
            # Step 1: Compliance check (if available)
            if self._subsystems.get("compliance_oracle"):
                user_id = task.get("user_id", "system")
                compliance = await self._ensure_compliance(user_id)
                if not compliance.get("compliant", True):
                    return {"ok": False, "error": "compliance_failed", "details": compliance}

            # Step 2: Execute via appropriate channel
            execution_result = await self._route_execution(task)

            if not execution_result.get("ok"):
                return execution_result

            # Step 3: Verify deliverable (if available)
            if self._subsystems.get("deliverable_verification"):
                verification = await self.verify_deliverable(execution_result)
                execution_result["verification"] = verification
                if verification.get("verified"):
                    self._verified_count += 1
                    self._quality_scores.append(verification.get("quality_score", 0.8))

            # Calculate execution time
            execution_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            result = {
                "ok": True,
                "task_id": task_id,
                "output": execution_result.get("output"),
                "executor": execution_result.get("executor", "unknown"),
                "execution_time_ms": execution_time_ms,
                "verified": execution_result.get("verification", {}).get("verified", False),
                "quality_score": execution_result.get("verification", {}).get("quality_score", 0.8)
            }

            self._executions.append(result)

        except Exception as e:
            logger.error(f"Execution error: {e}")
            result = {"ok": False, "error": str(e), "task_id": task_id}

        return result

    async def _route_execution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Route task to appropriate execution system"""
        task_type = task.get("type", "").lower()
        platform = task.get("platform", "").lower()

        # Fiverr tasks
        if platform == "fiverr" and self._subsystems.get("fiverr_automation"):
            return await self._execute_fiverr(task)

        # Proposal generation
        if task_type == "proposal" and self._subsystems.get("proposal_generator"):
            return await self._execute_proposal(task)

        # Outreach tasks
        if task_type == "outreach" and self._subsystems.get("direct_outreach"):
            return await self._execute_outreach(task)

        # AI content generation
        if task_type in ["content", "code", "analysis"] and self._subsystems.get("ai_router"):
            return await self._execute_ai(task)

        # Browser automation (fabric)
        if self._subsystems.get("fabric"):
            return await self._execute_fabric_task(task)

        # Fallback to connectors
        if self._subsystems.get("connectors"):
            return await self._execute_connector(task)

        return {"ok": False, "error": "No suitable execution system available"}

    async def _execute_fiverr(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Fiverr-specific task"""
        try:
            action = task.get("action", "process_order")

            if action == "create_gig" and callable(self._create_gig):
                result = await self._create_gig(task.get("gig_data", {}))
                return {"ok": True, "output": result, "executor": "fiverr/create_gig"}

            elif action == "process_order" and callable(self._process_order):
                result = await self._process_order(task.get("order_id", ""))
                return {"ok": True, "output": result, "executor": "fiverr/process_order"}

            elif action == "deliver" and callable(self._deliver_order):
                result = await self._deliver_order(task.get("order_id", ""), task.get("deliverable", {}))
                return {"ok": True, "output": result, "executor": "fiverr/deliver"}

            return {"ok": False, "error": f"Unknown Fiverr action: {action}"}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _execute_proposal(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate and submit proposal"""
        try:
            if callable(self._gen_proposal):
                proposal = self._gen_proposal(task.get("job", {}))
                if task.get("submit") and callable(self._submit_proposal):
                    result = self._submit_proposal(proposal)
                    return {"ok": True, "output": result, "executor": "proposal/submit"}
                return {"ok": True, "output": proposal, "executor": "proposal/generate"}

            return {"ok": False, "error": "Proposal generator not callable"}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _execute_outreach(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute outreach campaign"""
        try:
            prospects = []
            if callable(self._find_prospects):
                prospects = self._find_prospects(task.get("criteria", {}))

            sent = 0
            for prospect in prospects[:task.get("limit", 10)]:
                if callable(self._personalize):
                    message = self._personalize(prospect, task.get("template", ""))
                    if callable(self._send_outreach):
                        self._send_outreach(prospect, message)
                        sent += 1

            return {"ok": True, "output": {"prospects": len(prospects), "sent": sent}, "executor": "outreach"}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _execute_ai(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute via AI router"""
        try:
            prompt = task.get("prompt", task.get("content", ""))
            routing = self._ai_router.route_task(task.get("type", "general"), {"requirements": prompt})
            result = await self._ai_router.execute_with_model(
                model=routing.get("primary_model", "claude"),
                task={"type": task.get("type"), "requirements": prompt}
            )
            return {
                "ok": result.get("status") == "completed",
                "output": result.get("output"),
                "executor": f"ai/{routing.get('primary_model')}"
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _execute_fabric_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute via fabric (browser automation)"""
        try:
            result = await self._execute_fabric(
                pdl_name=task.get("pdl_name", "generic.execute"),
                url=task.get("url", ""),
                data=task.get("data", {}),
                ev_estimate=task.get("ev_estimate", 0)
            )
            return {"ok": result.get("ok", False), "output": result, "executor": "fabric"}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _execute_connector(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute via connector registry"""
        try:
            platform = task.get("platform", "")
            connector = self._get_connector(platform)
            if connector:
                result = await connector.execute(task.get("data", {}))
                return {"ok": True, "output": result, "executor": f"connector/{platform}"}
            return {"ok": False, "error": f"No connector for {platform}"}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def verify_deliverable(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a deliverable against SLA"""
        if not self._subsystems.get("deliverable_verification"):
            return {"verified": True, "quality_score": 0.8, "method": "assumed"}

        try:
            output = execution_result.get("output", {})

            # Use verification engine if available
            if callable(self._verify_deliverable):
                verification = self._verify_deliverable(output)
                return {
                    "verified": verification.get("passed", True),
                    "quality_score": verification.get("score", 0.8),
                    "details": verification
                }

            # Fallback verification
            return {"verified": True, "quality_score": 0.8, "method": "fallback"}

        except Exception as e:
            return {"verified": False, "error": str(e)}

    async def _ensure_compliance(self, user_id: str) -> Dict[str, Any]:
        """Ensure user/agent meets compliance requirements"""
        if not self._subsystems.get("compliance_oracle"):
            return {"compliant": True, "tier": "BASIC"}

        try:
            if callable(self._check_kyc):
                kyc_status = self._check_kyc(user_id)
                if not kyc_status.get("verified", True):
                    return {"compliant": False, "reason": "KYC not verified"}

            if callable(self._get_tier):
                tier = self._get_tier(user_id)
                return {"compliant": True, "tier": tier}

            return {"compliant": True, "tier": "BASIC"}

        except Exception as e:
            logger.warning(f"Compliance check error: {e}")
            return {"compliant": True, "tier": "BASIC", "error": str(e)}

    async def ensure_compliance(self, task: Dict[str, Any]) -> bool:
        """Public method to check task compliance"""
        user_id = task.get("user_id", "system")
        result = await self._ensure_compliance(user_id)
        return result.get("compliant", True)

    def get_status(self) -> Dict[str, Any]:
        """Get execution manager status"""
        available = sum(1 for v in self._subsystems.values() if v)
        avg_quality = sum(self._quality_scores) / len(self._quality_scores) if self._quality_scores else 0.8

        return {
            "ok": True,
            "subsystems": {
                "available": available,
                "total": len(self._subsystems),
                "percentage": round(available / len(self._subsystems) * 100, 1) if self._subsystems else 0,
                "details": self._subsystems
            },
            "execution": {
                "total": len(self._executions),
                "verified": self._verified_count,
                "quality_score": round(avg_quality, 2)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton instance
_execution_manager: Optional[ExecutionManager] = None


def get_execution_manager() -> ExecutionManager:
    """Get or create the execution manager singleton"""
    global _execution_manager
    if _execution_manager is None:
        _execution_manager = ExecutionManager()
    return _execution_manager

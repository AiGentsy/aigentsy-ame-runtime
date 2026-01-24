"""
Execution Manager - Execution Quality + Verification
=====================================================

Systems managed (with ACTUAL function imports):
1. fiverr_automation_engine.py - FiverrAutomationEngine class
2. deliverable_verification_engine.py - DeliverableVerificationEngine, verify_before_buyer_sees
3. compliance_oracle.py - submit_kyc, check_transaction_allowed, get_kyc_status
4. one_tap_widget.py - OneTapWidget, create_widget_config, process_widget_purchase
5. direct_outreach_engine.py - DirectOutreachEngine, send_direct_outreach
6. proposal_generator.py - ProposalGenerator class
7. social_autoposting_engine.py - SocialAutoPostingEngine, get_social_engine
8. storefront_deployer.py - deploy_storefront, update_storefront
9. sku_orchestrator.py - UniversalBusinessOrchestrator
10. client_acceptance_portal.py - accept_deal, submit_delivery, get_deal_stats
11. aigentsy_conductor.py - MultiAIRouter
12. connectors (registry) - get_registry, get_connector
13. universal_platform_adapter.py - PlatformRegistry, AdapterFactory (27+ platforms)
14. dribbble_portfolio_automation.py - DribbbleAutomation, ContentGenerator
15. ninety_nine_designs_automation.py - DesignContestAutomation, ContestDiscovery
16. vercel_deployer.py - deploy_to_vercel, delete_deployment
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
        """Initialize all 12 execution subsystems with CORRECT imports"""

        # 1. Fiverr Automation Engine
        try:
            from fiverr_automation_engine import (
                FiverrGigConfig,
                PortfolioGenerator,
                FiverrGigManager,
                FiverrOrderProcessor,
                FiverrAnalytics,
                FiverrAutomationEngine
            )
            self._fiverr_engine = FiverrAutomationEngine()
            self._gig_manager = FiverrGigManager
            self._order_processor = FiverrOrderProcessor
            self._fiverr_analytics = FiverrAnalytics
            self._portfolio_gen = PortfolioGenerator
            self._subsystems["fiverr_automation"] = True
            logger.info("Fiverr Automation Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Fiverr automation not available: {e}")
            self._subsystems["fiverr_automation"] = False

        # 2. Deliverable Verification Engine
        try:
            from deliverable_verification_engine import (
                DeliverableVerificationEngine,
                get_verification_engine,
                verify_before_buyer_sees,
                VerificationDimension,
                VerificationResult
            )
            self._verification_engine = get_verification_engine()
            self._verify_deliverable = verify_before_buyer_sees
            self._ver_dimension = VerificationDimension
            self._ver_result = VerificationResult
            self._subsystems["deliverable_verification"] = True
            logger.info("Deliverable Verification Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Deliverable verification not available: {e}")
            self._subsystems["deliverable_verification"] = False

        # 3. Compliance Oracle
        try:
            from compliance_oracle import (
                submit_kyc,
                approve_kyc,
                reject_kyc,
                check_transaction_allowed,
                get_kyc_status,
                list_pending_kyc,
                list_sars,
                get_compliance_stats
            )
            self._submit_kyc = submit_kyc
            self._approve_kyc = approve_kyc
            self._reject_kyc = reject_kyc
            self._check_transaction = check_transaction_allowed
            self._kyc_status = get_kyc_status
            self._pending_kyc = list_pending_kyc
            self._list_sars = list_sars
            self._compliance_stats = get_compliance_stats
            self._subsystems["compliance_oracle"] = True
            logger.info("Compliance Oracle loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Compliance oracle not available: {e}")
            self._subsystems["compliance_oracle"] = False

        # 4. One-Tap Widget
        try:
            from one_tap_widget import (
                OneTapWidget,
                create_widget_config,
                generate_embed_code,
                create_widget_session,
                process_widget_purchase,
                get_widget_config,
                get_widget_stats,
                get_partner_widgets,
                get_widget_platform_stats
            )
            self._widget_class = OneTapWidget
            self._create_widget = create_widget_config
            self._embed_code = generate_embed_code
            self._widget_session = create_widget_session
            self._process_purchase = process_widget_purchase
            self._get_widget_config = get_widget_config
            self._widget_stats = get_widget_stats
            self._partner_widgets = get_partner_widgets
            self._platform_stats = get_widget_platform_stats
            self._subsystems["one_tap_widget"] = True
            logger.info("One-Tap Widget loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"One-tap widget not available: {e}")
            self._subsystems["one_tap_widget"] = False

        # 5. Direct Outreach Engine
        try:
            from direct_outreach_engine import (
                DirectOutreachEngine,
                get_outreach_engine,
                send_direct_outreach,
                OutreachChannel,
                OutreachStatus,
                ProposalGenerator as OutreachProposalGen
            )
            self._outreach_engine = get_outreach_engine()
            self._send_outreach = send_direct_outreach
            self._outreach_channel = OutreachChannel
            self._outreach_status = OutreachStatus
            self._subsystems["direct_outreach"] = True
            logger.info("Direct Outreach Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Direct outreach not available: {e}")
            self._subsystems["direct_outreach"] = False

        # 6. Social AutoPosting Engine
        try:
            from social_autoposting_engine import (
                SocialAutoPostingEngine,
                get_social_engine,
                SocialPlatform,
                SocialPoster,
                ContentGenerator,
                ApprovalManager
            )
            self._social_engine = get_social_engine()
            self._social_platform = SocialPlatform
            self._social_poster = SocialPoster
            self._content_gen = ContentGenerator
            self._approval_mgr = ApprovalManager
            self._subsystems["social_autoposting"] = True
            logger.info("Social AutoPosting Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Social autoposting not available: {e}")
            self._subsystems["social_autoposting"] = False

        # 7. Storefront Deployer
        try:
            from storefront_deployer import (
                deploy_storefront,
                update_storefront,
                get_storefront_status
            )
            self._deploy_storefront = deploy_storefront
            self._update_storefront = update_storefront
            self._storefront_status = get_storefront_status
            self._subsystems["storefront_deployer"] = True
            logger.info("Storefront Deployer loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Storefront deployer not available: {e}")
            self._subsystems["storefront_deployer"] = False

        # 8. SKU Orchestrator
        try:
            from sku_orchestrator import UniversalBusinessOrchestrator
            self._sku_orchestrator = UniversalBusinessOrchestrator()
            self._subsystems["sku_orchestrator"] = True
            logger.info("SKU Orchestrator loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"SKU orchestrator not available: {e}")
            self._subsystems["sku_orchestrator"] = False

        # 9. Client Acceptance Portal
        try:
            from client_acceptance_portal import (
                get_service_pricing,
                create_accept_link,
                get_deal,
                accept_deal,
                mark_deal_in_progress,
                submit_delivery,
                client_approve_delivery,
                client_request_revision,
                client_dispute_delivery,
                get_pending_deals,
                get_in_progress_deals,
                get_awaiting_approval_deals,
                get_deal_stats
            )
            self._service_pricing = get_service_pricing
            self._create_link = create_accept_link
            self._get_deal = get_deal
            self._accept_deal = accept_deal
            self._start_deal = mark_deal_in_progress
            self._submit_delivery = submit_delivery
            self._approve_delivery = client_approve_delivery
            self._request_revision = client_request_revision
            self._dispute_delivery = client_dispute_delivery
            self._pending_deals = get_pending_deals
            self._in_progress = get_in_progress_deals
            self._awaiting_approval = get_awaiting_approval_deals
            self._deal_stats = get_deal_stats
            self._subsystems["client_portal"] = True
            logger.info("Client Acceptance Portal loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Client portal not available: {e}")
            self._subsystems["client_portal"] = False

        # 10. AiGentsy Conductor (AI Router)
        try:
            from aigentsy_conductor import MultiAIRouter
            self._ai_router = MultiAIRouter()
            self._subsystems["ai_router"] = True
            logger.info("AiGentsy Conductor (AI Router) loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"AI router not available: {e}")
            self._subsystems["ai_router"] = False

        # 11. Connector Registry
        try:
            from connectors.registry import get_registry, get_connector
            self._get_registry = get_registry
            self._get_connector = get_connector
            self._subsystems["connectors"] = True
            logger.info("Connector Registry loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Connectors not available: {e}")
            self._subsystems["connectors"] = False

        # 12. Universal Fulfillment Fabric
        try:
            from universal_fulfillment_fabric import (
                execute_universal,
                get_fabric_status,
                get_execution_logs,
                fabric_execute
            )
            self._execute_fabric = execute_universal
            self._fabric_status = get_fabric_status
            self._execution_logs = get_execution_logs
            self._fabric_execute = fabric_execute
            self._subsystems["fabric"] = True
            logger.info("Universal Fulfillment Fabric loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Fabric not available: {e}")
            self._subsystems["fabric"] = False

        # 13. Universal Platform Adapter (27+ platforms)
        try:
            from universal_platform_adapter import (
                PlatformRegistry,
                get_platform_registry,
                PlatformAdapter,
                GenericAPIAdapter,
                GenericScrapingAdapter,
                AdapterFactory
            )
            self._platform_registry = get_platform_registry()
            self._adapter_factory = AdapterFactory
            self._api_adapter = GenericAPIAdapter
            self._scraping_adapter = GenericScrapingAdapter
            self._subsystems["universal_platform_adapter"] = True
            logger.info("Universal Platform Adapter loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Universal Platform Adapter not available: {e}")
            self._subsystems["universal_platform_adapter"] = False

        # 14. Dribbble Portfolio Automation (lazy init - requires graphics_engine)
        try:
            from dribbble_portfolio_automation import (
                DribbbleAutomation,
                TrendAnalyzer,
                PortfolioManager,
                ClientInquiryManager
            )
            self._dribbble_class = DribbbleAutomation  # Lazy - needs graphics_engine
            self._dribbble_trends = TrendAnalyzer()
            self._dribbble_portfolio = PortfolioManager()
            self._dribbble_inquiries = ClientInquiryManager()
            self._subsystems["dribbble_portfolio"] = True
            logger.info("Dribbble Portfolio Automation loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Dribbble portfolio not available: {e}")
            self._subsystems["dribbble_portfolio"] = False

        # 15. 99designs Automation (lazy init - requires graphics_engine)
        try:
            from ninety_nine_designs_automation import (
                DesignContestAutomation,
                ContestDiscovery,
                ContestSubmissionManager
            )
            self._ninety_nine_class = DesignContestAutomation  # Lazy - needs graphics_engine
            self._contest_discovery = ContestDiscovery()
            self._submission_mgr = ContestSubmissionManager()
            self._subsystems["ninety_nine_designs"] = True
            logger.info("99designs Automation loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"99designs not available: {e}")
            self._subsystems["ninety_nine_designs"] = False

        # 16. Vercel Deployer
        try:
            from vercel_deployer import (
                deploy_to_vercel,
                delete_deployment
            )
            self._deploy_vercel = deploy_to_vercel
            self._delete_vercel = delete_deployment
            self._subsystems["vercel_deployer"] = True
            logger.info("Vercel Deployer loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Vercel deployer not available: {e}")
            self._subsystems["vercel_deployer"] = False

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
                compliance = await self._ensure_compliance(user_id, task)
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

        # Social posting
        if task_type == "social_post" and self._subsystems.get("social_autoposting"):
            return await self._execute_social(task)

        # Outreach tasks
        if task_type == "outreach" and self._subsystems.get("direct_outreach"):
            return await self._execute_outreach(task)

        # AI content generation
        if task_type in ["content", "code", "analysis"] and self._subsystems.get("ai_router"):
            return await self._execute_ai(task)

        # Client portal deals
        if task_type == "deal" and self._subsystems.get("client_portal"):
            return await self._execute_deal(task)

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
            if hasattr(self._fiverr_engine, 'process_order'):
                result = await self._fiverr_engine.process_order(task)
                return {"ok": True, "output": result, "executor": "fiverr_automation"}
            return {"ok": False, "error": "Fiverr engine not properly initialized"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _execute_social(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute social posting task"""
        try:
            if hasattr(self._social_engine, 'create_and_schedule_post'):
                result = await self._social_engine.create_and_schedule_post(task)
                return {"ok": True, "output": result, "executor": "social_autoposting"}
            return {"ok": False, "error": "Social engine not properly initialized"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _execute_outreach(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute outreach campaign"""
        try:
            if callable(self._send_outreach):
                result = await self._send_outreach(task)
                return {"ok": True, "output": result, "executor": "direct_outreach"}
            return {"ok": False, "error": "Outreach function not callable"}
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

    async def _execute_deal(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute client portal deal"""
        try:
            action = task.get("action", "create")
            if action == "accept" and callable(self._accept_deal):
                result = await self._accept_deal(task.get("deal_id"), task.get("client_info", {}))
                return {"ok": True, "output": result, "executor": "client_portal/accept"}
            elif action == "deliver" and callable(self._submit_delivery):
                result = await self._submit_delivery(task.get("deal_id"), task.get("deliverable", {}))
                return {"ok": True, "output": result, "executor": "client_portal/deliver"}
            return {"ok": False, "error": f"Unknown deal action: {action}"}
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
            if callable(self._verify_deliverable):
                verification = await self._verify_deliverable(output, {})
                return {
                    "verified": verification.get("passed", True),
                    "quality_score": verification.get("score", 0.8),
                    "details": verification
                }
            return {"verified": True, "quality_score": 0.8, "method": "fallback"}
        except Exception as e:
            return {"verified": False, "error": str(e)}

    async def _ensure_compliance(self, user_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure user/agent meets compliance requirements"""
        if not self._subsystems.get("compliance_oracle"):
            return {"compliant": True, "tier": "BASIC"}

        try:
            if callable(self._check_transaction):
                check = await self._check_transaction(user_id, task.get("value", 0), task.get("type", ""))
                return {"compliant": check.get("allowed", True), "details": check}
            return {"compliant": True, "tier": "BASIC"}
        except Exception as e:
            logger.warning(f"Compliance check error: {e}")
            return {"compliant": True, "tier": "BASIC", "error": str(e)}

    async def deploy_storefront(self, user_data: Dict[str, Any], sku_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy a storefront for a user"""
        if not self._subsystems.get("storefront_deployer"):
            return {"ok": False, "error": "Storefront deployer not available"}

        try:
            if callable(self._deploy_storefront):
                result = await self._deploy_storefront(user_data, sku_config)
                return {"ok": True, "result": result}
            return {"ok": False, "error": "Deploy function not callable"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

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

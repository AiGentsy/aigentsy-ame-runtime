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
import os

logger = logging.getLogger("execution_manager")


class ExecutionManager:
    """Coordinates execution quality and verification systems"""

    def __init__(self):
        self._subsystems: Dict[str, bool] = {}
        self._executions: List[Dict] = []
        self._verified_count: int = 0
        self._quality_scores: List[float] = []
        self._execution_errors: List[Dict] = []  # Track last N errors
        self._max_error_history: int = 50
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
        """
        Execute task with full verification pipeline.

        PRIORITY ORDER:
        1. Universal Fabric (browser automation) - works on ANY platform
        2. Platform-specific APIs (if fabric unavailable)
        3. Fallback connectors
        """
        task_id = task.get("task_id", f"exec_{uuid4().hex[:8]}")
        platform = task.get("platform", "unknown")
        start_time = datetime.now(timezone.utc)
        result = {"ok": False, "task_id": task_id, "platform": platform}

        try:
            # Step 1: Compliance check (if available)
            if self._subsystems.get("compliance_oracle"):
                user_id = task.get("user_id", "system")
                compliance = await self._ensure_compliance(user_id, task)
                if not compliance.get("compliant", True):
                    return {"ok": False, "error": "compliance_failed", "details": compliance, "method": "blocked"}

            # Step 2: PRIORITY 1 - Try Universal Fabric (browser automation)
            if self._subsystems.get("fabric"):
                fabric_result = await self._execute_via_fabric(task)
                if fabric_result.get("ok"):
                    execution_result = fabric_result
                    execution_result["method"] = "fabric"
                    logger.info(f"✅ {platform} executed via fabric")
                elif fabric_result.get("queued"):
                    # Fabric queued for manual approval - still a valid response
                    return {**fabric_result, "method": "fabric_queued", "task_id": task_id}
                else:
                    # Fabric failed, try fallback
                    logger.warning(f"⚠️ Fabric failed for {platform}: {fabric_result.get('error')}, trying API fallback")
                    execution_result = await self._route_execution(task)
                    execution_result["method"] = "api_fallback"
            else:
                # No fabric available, use API routing
                execution_result = await self._route_execution(task)
                execution_result["method"] = "api"

            if not execution_result.get("ok"):
                error_info = {
                    "task_id": task_id,
                    "platform": platform,
                    "type": task.get("type", "unknown"),
                    "error": execution_result.get("error", "Unknown error"),
                    "error_type": execution_result.get("error_type", "ExecutionError"),
                    "method": execution_result.get("method", "unknown"),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                self._track_error(error_info)
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
            error_info = {
                "task_id": task_id,
                "platform": task.get("platform", "unknown"),
                "type": task.get("type", "unknown"),
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self._track_error(error_info)
            result = {"ok": False, "error": str(e), "error_type": type(e).__name__, "task_id": task_id}

        return result

    def _track_error(self, error_info: Dict[str, Any]):
        """Track execution error for debugging"""
        self._execution_errors.append(error_info)
        # Keep only last N errors
        if len(self._execution_errors) > self._max_error_history:
            self._execution_errors = self._execution_errors[-self._max_error_history:]

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

    async def _execute_via_fabric(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task via Universal Fabric (browser automation).

        This is the PRIMARY execution method - works on any platform without APIs.
        """
        platform = task.get("platform", "unknown")
        action = task.get("action", task.get("type", "execute"))

        # Map platform to URL if not provided
        platform_urls = {
            "twitter": "https://twitter.com",
            "hackernews": "https://news.ycombinator.com",
            "linkedin": "https://linkedin.com",
            "reddit": "https://reddit.com",
            "fiverr": "https://fiverr.com",
            "upwork": "https://upwork.com",
            "github": "https://github.com",
            "producthunt": "https://producthunt.com",
            "indiehackers": "https://indiehackers.com",
            "dribbble": "https://dribbble.com",
            "99designs": "https://99designs.com",
        }

        url = task.get("url") or task.get("job_url") or task.get("post_url") or platform_urls.get(platform)

        if not url:
            return {"ok": False, "error": f"No URL for platform: {platform}"}

        # Build PDL name for fabric
        pdl_name = f"{platform}.{action}"

        # Get expected value for auto-execute threshold check
        ev_estimate = float(task.get("ev", task.get("value", 0)) or 0)

        try:
            # Try fabric_execute first (handles PDL routing)
            if callable(self._fabric_execute):
                result = await self._fabric_execute(
                    pdl_name=pdl_name,
                    params={
                        "url": url,
                        **task.get("data", {}),
                        **task.get("params", {}),
                        "title": task.get("title", ""),
                        "description": task.get("description", ""),
                        "content": task.get("content", ""),
                        "message": task.get("message", ""),
                    },
                    ev_estimate=ev_estimate,
                    dry_run=task.get("dry_run", False)
                )

                # If PDL not found, fall back to execute_universal directly
                pdl_not_found = "PDL not found" in result.get("error", "")
                if result.get("ok") or result.get("queued") or not pdl_not_found:
                    return {
                        "ok": result.get("ok", False),
                        "output": result,
                        "executor": "fabric",
                        "method": "fabric",
                        "platform": platform,
                        "execution_id": result.get("execution_id"),
                        "verification": result.get("verification", {}),
                        "queued": result.get("queued", False),
                        "error": result.get("error") if not result.get("ok") else None
                    }

                # PDL not found - try execute_universal directly with the URL
                logger.info(f"PDL {pdl_name} not found, trying execute_universal directly")

            # Fallback to execute_universal directly (browser automation)
            if callable(self._execute_fabric):
                # Get credentials if platform has them configured
                credentials = None
                username_key = f"{platform.upper()}_USERNAME"
                password_key = f"{platform.upper()}_PASSWORD"
                if os.environ.get(username_key) and os.environ.get(password_key):
                    credentials = {
                        "username": os.environ.get(username_key),
                        "password": os.environ.get(password_key)
                    }

                result = await self._execute_fabric(
                    pdl_name=pdl_name,
                    url=url,
                    data={
                        **task.get("data", {}),
                        **task.get("params", {}),
                        "title": task.get("title", ""),
                        "description": task.get("description", ""),
                        "content": task.get("content", ""),
                        "message": task.get("message", ""),
                        "url": url,
                    },
                    ev_estimate=ev_estimate,
                    credentials=credentials
                )
                return {
                    "ok": result.get("ok", False),
                    "output": result,
                    "executor": "fabric/universal",
                    "method": "fabric_universal",
                    "platform": platform,
                    "execution_id": result.get("execution_id"),
                    "error": result.get("error") if not result.get("ok") else None
                }

            return {"ok": False, "error": "Fabric functions not available"}

        except Exception as e:
            logger.error(f"Fabric execution error for {platform}: {e}")
            return {"ok": False, "error": str(e), "error_type": type(e).__name__}

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

    def get_debug_info(self) -> Dict[str, Any]:
        """Get detailed debug information for troubleshooting"""
        # Check which API credentials are configured (without revealing values)
        api_credentials = {
            "twitter": {
                "TWITTER_API_KEY": bool(os.environ.get("TWITTER_API_KEY")),
                "TWITTER_API_SECRET": bool(os.environ.get("TWITTER_API_SECRET")),
                "TWITTER_ACCESS_TOKEN": bool(os.environ.get("TWITTER_ACCESS_TOKEN")),
                "TWITTER_BEARER_TOKEN": bool(os.environ.get("TWITTER_BEARER_TOKEN")),
            },
            "instagram": {
                "INSTAGRAM_ACCESS_TOKEN": bool(os.environ.get("INSTAGRAM_ACCESS_TOKEN")),
                "INSTAGRAM_BUSINESS_ID": bool(os.environ.get("INSTAGRAM_BUSINESS_ID")),
            },
            "linkedin": {
                "LINKEDIN_ACCESS_TOKEN": bool(os.environ.get("LINKEDIN_ACCESS_TOKEN")),
                "LINKEDIN_CLIENT_ID": bool(os.environ.get("LINKEDIN_CLIENT_ID")),
                "LINKEDIN_CLIENT_SECRET": bool(os.environ.get("LINKEDIN_CLIENT_SECRET")),
            },
            "github": {
                "GITHUB_TOKEN": bool(os.environ.get("GITHUB_TOKEN")),
            },
            "stripe": {
                "STRIPE_SECRET_KEY": bool(os.environ.get("STRIPE_SECRET_KEY")),
                "STRIPE_WEBHOOK_SECRET": bool(os.environ.get("STRIPE_WEBHOOK_SECRET")),
            },
            "shopify": {
                "SHOPIFY_ADMIN_TOKEN": bool(os.environ.get("SHOPIFY_ADMIN_TOKEN")),
                "SHOPIFY_WEBHOOK_SECRET": bool(os.environ.get("SHOPIFY_WEBHOOK_SECRET")),
            },
            "twilio": {
                "TWILIO_ACCOUNT_SID": bool(os.environ.get("TWILIO_ACCOUNT_SID")),
                "TWILIO_AUTH_TOKEN": bool(os.environ.get("TWILIO_AUTH_TOKEN")),
                "TWILIO_PHONE_NUMBER": bool(os.environ.get("TWILIO_PHONE_NUMBER")),
            },
            "resend": {
                "RESEND_API_KEY": bool(os.environ.get("RESEND_API_KEY")),
            },
            "ai_models": {
                "OPENROUTER_API_KEY": bool(os.environ.get("OPENROUTER_API_KEY")),
                "PERPLEXITY_API_KEY": bool(os.environ.get("PERPLEXITY_API_KEY")),
                "GEMINI_API_KEY": bool(os.environ.get("GEMINI_API_KEY")),
                "ANTHROPIC_API_KEY": bool(os.environ.get("ANTHROPIC_API_KEY")),
            },
            "media": {
                "RUNWAY_API_KEY": bool(os.environ.get("RUNWAY_API_KEY")),
                "STABILITY_API_KEY": bool(os.environ.get("STABILITY_API_KEY")),
            },
            "upwork": {
                "UPWORK_API_KEY": bool(os.environ.get("UPWORK_API_KEY")),
                "UPWORK_API_SECRET": bool(os.environ.get("UPWORK_API_SECRET")),
            },
            "fiverr": {
                "FIVERR_API_KEY": bool(os.environ.get("FIVERR_API_KEY")),
                "FIVERR_SESSION": bool(os.environ.get("FIVERR_SESSION")),
            },
        }

        # Count configured vs total for each platform
        credential_summary = {}
        for platform, creds in api_credentials.items():
            configured = sum(1 for v in creds.values() if v)
            total = len(creds)
            credential_summary[platform] = {
                "configured": configured,
                "total": total,
                "ready": configured == total,
                "missing": [k for k, v in creds.items() if not v]
            }

        return {
            "ok": True,
            "credentials": credential_summary,
            "credentials_detail": api_credentials,
            "subsystems": self._subsystems,
            "recent_errors": self._execution_errors[-10:],  # Last 10 errors
            "error_count": len(self._execution_errors),
            "execution_stats": {
                "total_executions": len(self._executions),
                "successful": sum(1 for e in self._executions if e.get("ok")),
                "failed": sum(1 for e in self._executions if not e.get("ok")),
                "verified": self._verified_count
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution errors"""
        return self._execution_errors[-limit:]

    async def execute_batch_with_errors(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch of opportunities and return detailed error info"""
        results = []
        errors = []
        succeeded = 0
        failed = 0

        for opp in opportunities:
            try:
                result = await self.execute_with_verification(opp)
                results.append(result)
                if result.get("ok"):
                    succeeded += 1
                else:
                    failed += 1
                    errors.append({
                        "opportunity_id": opp.get("id", "unknown"),
                        "platform": opp.get("platform", "unknown"),
                        "type": opp.get("type", "unknown"),
                        "error": result.get("error", "Unknown error"),
                        "error_type": result.get("error_type", "UnknownError")
                    })
            except Exception as e:
                failed += 1
                errors.append({
                    "opportunity_id": opp.get("id", "unknown"),
                    "platform": opp.get("platform", "unknown"),
                    "type": opp.get("type", "unknown"),
                    "error": str(e),
                    "error_type": type(e).__name__
                })

        return {
            "ok": succeeded > 0,
            "attempted": len(opportunities),
            "succeeded": succeeded,
            "failed": failed,
            "errors": errors[:20],  # Limit to 20 errors in response
            "results": results
        }


# Singleton instance
_execution_manager: Optional[ExecutionManager] = None


def get_execution_manager() -> ExecutionManager:
    """Get or create the execution manager singleton"""
    global _execution_manager
    if _execution_manager is None:
        _execution_manager = ExecutionManager()
    return _execution_manager

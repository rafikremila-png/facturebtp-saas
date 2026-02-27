"""
Admin Metrics Service for BTP Facture
Handles MRR, ARR, Churn and subscriber analytics
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio

logger = logging.getLogger(__name__)

# Plan monthly prices for MRR calculation
PLAN_PRICES = {
    "essentiel": 19.00,
    "pro": 29.00,
    "business": 59.00,
    "trial": 0.00
}

# Cache for metrics (10 minutes)
_metrics_cache = {
    "data": None,
    "timestamp": None,
    "ttl_seconds": 600  # 10 minutes
}


class AdminMetricsService:
    """Service for calculating admin SaaS metrics"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db.users
    
    def _get_month_range(self, months_ago: int = 0) -> tuple:
        """Get start and end of a month (current or past)"""
        now = datetime.now(timezone.utc)
        
        # Calculate target month
        year = now.year
        month = now.month - months_ago
        
        while month <= 0:
            month += 12
            year -= 1
        
        first_of_month = datetime(year, month, 1, tzinfo=timezone.utc)
        
        # Calculate last day of month
        if month == 12:
            next_month = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        
        return first_of_month, next_month
    
    async def get_metrics(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get all admin metrics (cached)"""
        global _metrics_cache
        
        # Check cache
        if not force_refresh and _metrics_cache["data"] and _metrics_cache["timestamp"]:
            age = (datetime.now(timezone.utc) - _metrics_cache["timestamp"]).total_seconds()
            if age < _metrics_cache["ttl_seconds"]:
                logger.debug(f"Returning cached metrics (age: {age:.0f}s)")
                return _metrics_cache["data"]
        
        # Calculate fresh metrics
        logger.info("Calculating fresh admin metrics...")
        
        try:
            metrics = await self._calculate_all_metrics()
            
            # Update cache
            _metrics_cache["data"] = metrics
            _metrics_cache["timestamp"] = datetime.now(timezone.utc)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            # Return cached data if available, even if stale
            if _metrics_cache["data"]:
                return _metrics_cache["data"]
            raise
    
    async def _calculate_all_metrics(self) -> Dict[str, Any]:
        """Calculate all metrics using aggregation pipelines"""
        
        # Run all calculations in parallel
        results = await asyncio.gather(
            self._get_subscriber_counts(),
            self._get_mrr(),
            self._get_plan_breakdown(),
            self._get_churn_rate(),
            self._get_new_subscribers_this_month(),
            self._get_mrr_history(6),
            return_exceptions=True
        )
        
        # Handle any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Metric calculation {i} failed: {result}")
                results[i] = {}
        
        subscriber_counts, mrr_data, plan_breakdown, churn_data, new_subs, mrr_history = results
        
        return {
            "mrr": mrr_data.get("mrr", 0),
            "arr": mrr_data.get("mrr", 0) * 12,
            "active_subscribers": subscriber_counts.get("active", 0),
            "trial_users": subscriber_counts.get("trial", 0),
            "expired_users": subscriber_counts.get("expired", 0),
            "total_users": subscriber_counts.get("total", 0),
            "churn_rate": churn_data.get("churn_rate", 0),
            "churn_count": churn_data.get("churned_count", 0),
            "new_subscribers_this_month": new_subs.get("count", 0),
            "plan_breakdown": plan_breakdown,
            "mrr_history": mrr_history,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def _get_subscriber_counts(self) -> Dict[str, int]:
        """Count subscribers by status"""
        pipeline = [
            {
                "$group": {
                    "_id": "$subscription_status",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        result = await self.users.aggregate(pipeline).to_list(100)
        
        counts = {
            "active": 0,
            "trial": 0,
            "expired": 0,
            "canceled": 0,
            "total": 0
        }
        
        for item in result:
            status = item["_id"]
            count = item["count"]
            counts["total"] += count
            
            if status == "active":
                counts["active"] = count
            elif status == "trial":
                counts["trial"] = count
            elif status == "expired":
                counts["expired"] = count
            elif status == "canceled":
                counts["canceled"] = count
        
        return counts
    
    async def _get_mrr(self) -> Dict[str, float]:
        """Calculate Monthly Recurring Revenue"""
        pipeline = [
            {
                "$match": {
                    "subscription_status": "active"
                }
            },
            {
                "$group": {
                    "_id": "$subscription_plan",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        result = await self.users.aggregate(pipeline).to_list(100)
        
        mrr = 0.0
        for item in result:
            plan = item["_id"]
            count = item["count"]
            price = PLAN_PRICES.get(plan, 0)
            mrr += price * count
        
        return {"mrr": mrr}
    
    async def _get_plan_breakdown(self) -> List[Dict[str, Any]]:
        """Get count of users per plan"""
        pipeline = [
            {
                "$match": {
                    "subscription_status": {"$in": ["active", "trial"]}
                }
            },
            {
                "$group": {
                    "_id": {
                        "plan": "$subscription_plan",
                        "status": "$subscription_status"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"_id.plan": 1}
            }
        ]
        
        result = await self.users.aggregate(pipeline).to_list(100)
        
        # Organize by plan
        plans_data = {}
        for item in result:
            plan = item["_id"]["plan"] or "trial"
            status = item["_id"]["status"]
            count = item["count"]
            
            if plan not in plans_data:
                plans_data[plan] = {"plan": plan, "active": 0, "trial": 0, "total": 0}
            
            if status == "active":
                plans_data[plan]["active"] = count
            elif status == "trial":
                plans_data[plan]["trial"] = count
            plans_data[plan]["total"] += count
        
        # Add plan details
        for plan_id, data in plans_data.items():
            data["price"] = PLAN_PRICES.get(plan_id, 0)
            data["mrr_contribution"] = data["active"] * data["price"]
        
        # Return as list, not dict
        return list(plans_data.values()) if plans_data else []
    
    async def _get_churn_rate(self) -> Dict[str, Any]:
        """Calculate churn rate for current month"""
        # Get date ranges
        current_start, current_end = self._get_month_range(0)
        prev_start, prev_end = self._get_month_range(1)
        
        # Count users who were active last month
        prev_active = await self.users.count_documents({
            "subscription_status": "active",
            "updated_at": {"$lt": current_start.isoformat()}
        })
        
        # Count users who cancelled/expired this month
        # (status changed to expired/canceled this month)
        churned = await self.users.count_documents({
            "subscription_status": {"$in": ["expired", "canceled"]},
            "updated_at": {
                "$gte": current_start.isoformat(),
                "$lt": current_end.isoformat()
            }
        })
        
        # Calculate churn rate
        if prev_active > 0:
            churn_rate = (churned / prev_active) * 100
        else:
            churn_rate = 0
        
        return {
            "churn_rate": round(churn_rate, 2),
            "churned_count": churned,
            "prev_month_active": prev_active
        }
    
    async def _get_new_subscribers_this_month(self) -> Dict[str, int]:
        """Count new paid subscribers this month"""
        current_start, current_end = self._get_month_range(0)
        
        # Count users whose subscription started this month
        count = await self.users.count_documents({
            "subscription_status": "active",
            "$or": [
                {
                    "subscription_start": {
                        "$gte": current_start.isoformat(),
                        "$lt": current_end.isoformat()
                    }
                },
                {
                    "created_at": {
                        "$gte": current_start.isoformat(),
                        "$lt": current_end.isoformat()
                    },
                    "subscription_plan": {"$in": ["essentiel", "pro", "business"]}
                }
            ]
        })
        
        return {"count": count}
    
    async def _get_mrr_history(self, months: int = 6) -> List[Dict[str, Any]]:
        """Get MRR for the last N months"""
        history = []
        
        for i in range(months - 1, -1, -1):
            month_start, month_end = self._get_month_range(i)
            
            # For simplicity, we'll estimate MRR based on current data
            # In production, you'd want to track historical snapshots
            
            # Get active subscribers at end of that month
            # This is an approximation - ideally you'd store monthly snapshots
            pipeline = [
                {
                    "$match": {
                        "subscription_status": "active",
                        "subscription_plan": {"$in": ["essentiel", "pro", "business"]}
                    }
                },
                {
                    "$group": {
                        "_id": "$subscription_plan",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            result = await self.users.aggregate(pipeline).to_list(100)
            
            mrr = 0.0
            for item in result:
                plan = item["_id"]
                count = item["count"]
                price = PLAN_PRICES.get(plan, 0)
                mrr += price * count
            
            history.append({
                "month": month_start.strftime("%Y-%m"),
                "month_label": month_start.strftime("%b %Y"),
                "mrr": mrr
            })
        
        return history
    
    async def get_detailed_subscribers(
        self, 
        status: Optional[str] = None,
        plan: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """Get detailed list of subscribers with filters"""
        query = {}
        
        if status:
            query["subscription_status"] = status
        
        if plan:
            query["subscription_plan"] = plan
        
        # Get total count
        total = await self.users.count_documents(query)
        
        # Get subscribers
        cursor = self.users.find(
            query,
            {
                "_id": 0,
                "id": 1,
                "email": 1,
                "name": 1,
                "company_name": 1,
                "subscription_plan": 1,
                "subscription_status": 1,
                "trial_start": 1,
                "trial_end": 1,
                "created_at": 1
            }
        ).sort("created_at", -1).skip(skip).limit(limit)
        
        subscribers = []
        async for doc in cursor:
            subscribers.append(doc)
        
        return {
            "subscribers": subscribers,
            "total": total,
            "page_size": limit,
            "offset": skip
        }


def get_admin_metrics_service(db: AsyncIOMotorDatabase) -> AdminMetricsService:
    """Factory function"""
    return AdminMetricsService(db)

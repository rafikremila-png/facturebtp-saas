"""
Financial Dashboard Service
Pennylane-style financial analytics
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from collections import defaultdict
import logging

from app.core.database import db, is_mongodb

logger = logging.getLogger(__name__)

class FinancialDashboardService:
    """Service for financial analytics and dashboard data"""
    
    @staticmethod
    async def get_summary(user_id: str, start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive financial summary"""
        if not start_date:
            start_date = datetime.now(timezone.utc).replace(month=1, day=1, hour=0, minute=0, second=0)
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        summary = {
            "total_revenue": 0,
            "total_unpaid": 0,
            "total_overdue": 0,
            "total_paid": 0,
            "average_payment_delay": 0,
            "total_vat_collected": 0,
            "total_quotes": 0,
            "total_invoices": 0,
            "conversion_rate": 0
        }
        
        if is_mongodb():
            # Get all invoices in period
            invoices = await db.invoices.find({
                "user_id": user_id,
                "invoice_date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }, {"_id": 0}).to_list(length=10000)
            
            summary["total_invoices"] = len(invoices)
            
            # Calculate metrics
            total_paid = 0
            total_unpaid = 0
            total_overdue = 0
            total_vat = 0
            payment_delays = []
            
            now = datetime.now(timezone.utc)
            
            for inv in invoices:
                total_ttc = inv.get("total_ttc", 0)
                amount_paid = inv.get("amount_paid", 0)
                total_vat += inv.get("total_vat", 0)
                
                if inv.get("status") == "paid":
                    total_paid += total_ttc
                    # Calculate payment delay
                    if inv.get("paid_date") and inv.get("invoice_date"):
                        try:
                            invoice_date = datetime.fromisoformat(inv["invoice_date"].replace("Z", "+00:00"))
                            paid_date = datetime.fromisoformat(inv["paid_date"].replace("Z", "+00:00"))
                            delay = (paid_date - invoice_date).days
                            payment_delays.append(delay)
                        except:
                            pass
                elif inv.get("status") in ["sent", "partial"]:
                    unpaid_amount = total_ttc - amount_paid
                    total_unpaid += unpaid_amount
                    
                    # Check if overdue
                    due_date_str = inv.get("due_date")
                    if due_date_str:
                        try:
                            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                            if due_date < now:
                                total_overdue += unpaid_amount
                        except:
                            pass
            
            summary["total_revenue"] = total_paid
            summary["total_paid"] = total_paid
            summary["total_unpaid"] = total_unpaid
            summary["total_overdue"] = total_overdue
            summary["total_vat_collected"] = total_vat
            summary["average_payment_delay"] = sum(payment_delays) / len(payment_delays) if payment_delays else 0
            
            # Get quotes count
            quotes_count = await db.quotes.count_documents({
                "user_id": user_id,
                "quote_date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            })
            summary["total_quotes"] = quotes_count
            
            # Conversion rate
            if quotes_count > 0:
                converted = await db.invoices.count_documents({
                    "user_id": user_id,
                    "quote_id": {"$ne": None},
                    "invoice_date": {
                        "$gte": start_date.isoformat(),
                        "$lte": end_date.isoformat()
                    }
                })
                summary["conversion_rate"] = round((converted / quotes_count) * 100, 1)
        
        return summary
    
    @staticmethod
    async def get_monthly_revenue(user_id: str, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly revenue breakdown"""
        monthly_data = []
        
        if is_mongodb():
            now = datetime.now(timezone.utc)
            
            for i in range(months - 1, -1, -1):
                # Calculate month boundaries
                month_date = now.replace(day=1) - timedelta(days=i * 30)
                year = month_date.year
                month = month_date.month
                
                start = datetime(year, month, 1, tzinfo=timezone.utc)
                if month == 12:
                    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
                else:
                    end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
                
                # Query invoices
                pipeline = [
                    {
                        "$match": {
                            "user_id": user_id,
                            "status": "paid",
                            "paid_date": {
                                "$gte": start.isoformat(),
                                "$lt": end.isoformat()
                            }
                        }
                    },
                    {
                        "$group": {
                            "_id": None,
                            "revenue": {"$sum": "$total_ttc"},
                            "vat": {"$sum": "$total_vat"},
                            "count": {"$sum": 1}
                        }
                    }
                ]
                
                result = await db.invoices.aggregate(pipeline).to_list(length=1)
                
                month_names = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", 
                              "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
                
                monthly_data.append({
                    "month": f"{month_names[month - 1]} {year}",
                    "year": year,
                    "month_num": month,
                    "revenue": result[0]["revenue"] if result else 0,
                    "vat": result[0]["vat"] if result else 0,
                    "invoice_count": result[0]["count"] if result else 0
                })
        
        return monthly_data
    
    @staticmethod
    async def get_cashflow(user_id: str, months: int = 6) -> List[Dict[str, Any]]:
        """Get cashflow data (income vs expenses)"""
        cashflow_data = []
        
        if is_mongodb():
            now = datetime.now(timezone.utc)
            
            for i in range(months - 1, -1, -1):
                month_date = now.replace(day=1) - timedelta(days=i * 30)
                year = month_date.year
                month = month_date.month
                
                start = datetime(year, month, 1, tzinfo=timezone.utc)
                if month == 12:
                    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
                else:
                    end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
                
                # Income from paid invoices
                income_pipeline = [
                    {
                        "$match": {
                            "user_id": user_id,
                            "status": "paid",
                            "paid_date": {"$gte": start.isoformat(), "$lt": end.isoformat()}
                        }
                    },
                    {"$group": {"_id": None, "total": {"$sum": "$amount_paid"}}}
                ]
                
                income_result = await db.invoices.aggregate(income_pipeline).to_list(length=1)
                income = income_result[0]["total"] if income_result else 0
                
                # For expenses, we'd need a separate expenses collection
                # For now, estimate based on project costs
                expenses_pipeline = [
                    {
                        "$match": {
                            "user_id": user_id,
                            "updated_at": {"$gte": start.isoformat(), "$lt": end.isoformat()}
                        }
                    },
                    {"$group": {"_id": None, "total": {"$sum": "$actual_cost"}}}
                ]
                
                expenses_result = await db.projects.aggregate(expenses_pipeline).to_list(length=1)
                expenses = expenses_result[0]["total"] if expenses_result else 0
                
                month_names = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
                              "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
                
                cashflow_data.append({
                    "month": f"{month_names[month - 1]} {year}",
                    "income": income,
                    "expenses": expenses,
                    "net": income - expenses
                })
        
        return cashflow_data
    
    @staticmethod
    async def get_invoice_status_breakdown(user_id: str) -> Dict[str, int]:
        """Get invoice count by status"""
        breakdown = {
            "draft": 0,
            "sent": 0,
            "paid": 0,
            "partial": 0,
            "overdue": 0,
            "cancelled": 0
        }
        
        if is_mongodb():
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            
            results = await db.invoices.aggregate(pipeline).to_list(length=10)
            
            for result in results:
                status = result["_id"]
                if status in breakdown:
                    breakdown[status] = result["count"]
        
        return breakdown
    
    @staticmethod
    async def get_top_clients(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top clients by revenue"""
        top_clients = []
        
        if is_mongodb():
            pipeline = [
                {"$match": {"user_id": user_id, "status": "paid"}},
                {
                    "$group": {
                        "_id": "$client_id",
                        "total_revenue": {"$sum": "$total_ttc"},
                        "invoice_count": {"$sum": 1}
                    }
                },
                {"$sort": {"total_revenue": -1}},
                {"$limit": limit}
            ]
            
            results = await db.invoices.aggregate(pipeline).to_list(length=limit)
            
            # Get client details
            for result in results:
                client_id = result["_id"]
                if client_id:
                    client = await db.clients.find_one({"id": client_id}, {"_id": 0, "name": 1, "company_name": 1})
                    top_clients.append({
                        "client_id": client_id,
                        "name": client.get("company_name") or client.get("name") if client else "Client inconnu",
                        "total_revenue": result["total_revenue"],
                        "invoice_count": result["invoice_count"]
                    })
        
        return top_clients
    
    @staticmethod
    async def get_vat_summary(user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get VAT summary for accounting"""
        vat_summary = {
            "total_vat_collected": 0,
            "vat_by_rate": {},
            "invoices_count": 0
        }
        
        if is_mongodb():
            invoices = await db.invoices.find({
                "user_id": user_id,
                "status": {"$in": ["paid", "sent", "partial"]},
                "invoice_date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }, {"_id": 0, "items": 1, "total_vat": 1}).to_list(length=10000)
            
            vat_by_rate = defaultdict(float)
            total_vat = 0
            
            for inv in invoices:
                total_vat += inv.get("total_vat", 0)
                
                # Break down by rate
                for item in inv.get("items", []):
                    rate = str(item.get("vat_rate", 20.0))
                    quantity = item.get("quantity", 1)
                    unit_price = item.get("unit_price", 0)
                    item_ht = quantity * unit_price
                    item_vat = item_ht * float(rate) / 100
                    vat_by_rate[rate] += item_vat
            
            vat_summary["total_vat_collected"] = total_vat
            vat_summary["vat_by_rate"] = dict(vat_by_rate)
            vat_summary["invoices_count"] = len(invoices)
        
        return vat_summary
    
    @staticmethod
    async def get_aging_report(user_id: str) -> List[Dict[str, Any]]:
        """Get accounts receivable aging report"""
        aging = {
            "current": [],      # Not yet due
            "1-30": [],         # 1-30 days overdue
            "31-60": [],        # 31-60 days overdue
            "61-90": [],        # 61-90 days overdue
            "90+": []           # > 90 days overdue
        }
        
        if is_mongodb():
            now = datetime.now(timezone.utc)
            
            invoices = await db.invoices.find({
                "user_id": user_id,
                "status": {"$in": ["sent", "partial", "overdue"]}
            }, {"_id": 0}).to_list(length=1000)
            
            for inv in invoices:
                due_date_str = inv.get("due_date")
                if not due_date_str:
                    continue
                
                try:
                    due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                except:
                    continue
                
                days_overdue = (now - due_date).days
                amount_due = inv.get("total_ttc", 0) - inv.get("amount_paid", 0)
                
                invoice_data = {
                    "invoice_id": inv["id"],
                    "invoice_number": inv.get("invoice_number"),
                    "client_id": inv.get("client_id"),
                    "amount_due": amount_due,
                    "due_date": due_date_str,
                    "days_overdue": max(0, days_overdue)
                }
                
                if days_overdue <= 0:
                    aging["current"].append(invoice_data)
                elif days_overdue <= 30:
                    aging["1-30"].append(invoice_data)
                elif days_overdue <= 60:
                    aging["31-60"].append(invoice_data)
                elif days_overdue <= 90:
                    aging["61-90"].append(invoice_data)
                else:
                    aging["90+"].append(invoice_data)
        
        # Calculate totals
        result = []
        for period, invoices in aging.items():
            total = sum(inv["amount_due"] for inv in invoices)
            result.append({
                "period": period,
                "count": len(invoices),
                "total": total,
                "invoices": invoices[:5]  # Limit to 5 per category
            })
        
        return result


# Create singleton instance
financial_dashboard_service = FinancialDashboardService()

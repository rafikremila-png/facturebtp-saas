"""
Admin Analytics Dashboard Service
Provides metrics for admin users including:
- User statistics
- Profile completion rates
- Subscription analytics
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User, UserSettings, Invoice, Quote, Client, Project
from app.core.security import ROLE_ADMIN, ROLE_SUPER_ADMIN

logger = logging.getLogger(__name__)


class AdminDashboardService:
    """Service for admin analytics and metrics"""
    
    # Profile completion fields
    PROFILE_FIELDS = {
        'profile': ['name', 'phone', 'email_verified'],
        'company': ['company_name', 'company_address', 'company_email', 'company_phone'],
        'legal': ['siret', 'vat_number'],
        'banking': ['iban', 'bic']
    }
    
    # All fields for 100% completion
    ALL_FIELDS = [
        'logo_base64',           # Logo uploaded
        'company_name',          # Company name
        'company_address',       # Company address
        'company_email',         # Company email
        'company_phone',         # Company phone
        'siret',                 # SIRET
        'legal_form',           # Legal form
        'vat_number',           # VAT number
        'iban',                 # IBAN
        'bic',                  # BIC
        'invoice_footer'        # Legal mentions / invoice terms
    ]
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get overall user statistics"""
        
        # Total users
        total_result = await self.db.execute(
            select(func.count(User.id))
        )
        total_users = total_result.scalar() or 0
        
        # Active users
        active_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_result.scalar() or 0
        
        # Users by subscription plan
        plan_result = await self.db.execute(
            select(User.subscription_plan, func.count(User.id))
            .group_by(User.subscription_plan)
        )
        users_by_plan = {row[0] or 'unknown': row[1] for row in plan_result.all()}
        
        # Users by role
        role_result = await self.db.execute(
            select(User.role, func.count(User.id))
            .group_by(User.role)
        )
        users_by_role = {row[0] or 'user': row[1] for row in role_result.all()}
        
        # New users this month
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
        new_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.created_at >= month_start)
        )
        new_users_this_month = new_users_result.scalar() or 0
        
        # Email verified
        verified_result = await self.db.execute(
            select(func.count(User.id)).where(User.email_verified == True)
        )
        email_verified = verified_result.scalar() or 0
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'email_verified': email_verified,
            'email_unverified': total_users - email_verified,
            'new_users_this_month': new_users_this_month,
            'users_by_plan': users_by_plan,
            'users_by_role': users_by_role
        }
    
    async def get_profile_completion_stats(self) -> Dict[str, Any]:
        """Get profile completion statistics across all users"""
        
        # Get all user settings
        result = await self.db.execute(
            select(UserSettings)
        )
        all_settings = list(result.scalars().all())
        
        if not all_settings:
            return {
                'average_completion': 0,
                'completion_distribution': {},
                'category_averages': {
                    'profile': 0,
                    'company': 0,
                    'legal': 0,
                    'banking': 0
                },
                'users_with_complete_profile': 0,
                'users_with_incomplete_profile': 0,
                'missing_fields_summary': {}
            }
        
        # Calculate completion for each user
        completions = []
        category_totals = {'profile': 0, 'company': 0, 'legal': 0, 'banking': 0}
        missing_fields_count = {field: 0 for field in self.ALL_FIELDS}
        complete_profiles = 0
        
        for settings in all_settings:
            completion = self._calculate_completion(settings)
            completions.append(completion['total_percentage'])
            
            if completion['total_percentage'] >= 100:
                complete_profiles += 1
            
            for cat, pct in completion['categories'].items():
                category_totals[cat] += pct
            
            for field, is_set in completion['fields'].items():
                if not is_set:
                    missing_fields_count[field] = missing_fields_count.get(field, 0) + 1
        
        total_users = len(all_settings)
        avg_completion = sum(completions) / total_users if total_users > 0 else 0
        
        # Distribution of completion rates
        distribution = {
            '0-25%': len([c for c in completions if c < 25]),
            '25-50%': len([c for c in completions if 25 <= c < 50]),
            '50-75%': len([c for c in completions if 50 <= c < 75]),
            '75-99%': len([c for c in completions if 75 <= c < 100]),
            '100%': len([c for c in completions if c >= 100])
        }
        
        return {
            'average_completion': round(avg_completion, 1),
            'completion_distribution': distribution,
            'category_averages': {
                cat: round(total / total_users, 1) if total_users > 0 else 0
                for cat, total in category_totals.items()
            },
            'users_with_complete_profile': complete_profiles,
            'users_with_incomplete_profile': total_users - complete_profiles,
            'missing_fields_summary': {
                field: count 
                for field, count in sorted(missing_fields_count.items(), key=lambda x: -x[1])
                if count > 0
            }
        }
    
    async def get_users_missing_info(self, info_type: str = 'all') -> List[Dict]:
        """Get list of users missing specific information"""
        
        # Get users with their settings
        result = await self.db.execute(
            select(User, UserSettings)
            .outerjoin(UserSettings, User.id == UserSettings.user_id)
            .where(User.role == 'user')  # Only regular users
        )
        users_with_settings = result.all()
        
        users_missing = []
        
        for user, settings in users_with_settings:
            missing_info = []
            
            if info_type in ['all', 'company']:
                if not settings or not settings.company_name:
                    missing_info.append('company_name')
                if not settings or not settings.siret:
                    missing_info.append('siret')
            
            if info_type in ['all', 'legal']:
                if not settings or not settings.vat_number:
                    missing_info.append('vat_number')
                if not settings or not settings.legal_form:
                    missing_info.append('legal_form')
            
            if info_type in ['all', 'banking']:
                if not settings or not settings.iban:
                    missing_info.append('iban')
                if not settings or not settings.bic:
                    missing_info.append('bic')
            
            if missing_info:
                completion = self._calculate_completion(settings) if settings else {'total_percentage': 0}
                users_missing.append({
                    'user_id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'missing_fields': missing_info,
                    'completion_percentage': completion['total_percentage']
                })
        
        return sorted(users_missing, key=lambda x: x['completion_percentage'])
    
    async def get_business_metrics(self) -> Dict[str, Any]:
        """Get business metrics for the platform"""
        
        # Total invoices and amount
        invoice_result = await self.db.execute(
            select(
                func.count(Invoice.id).label('count'),
                func.coalesce(func.sum(Invoice.total_ttc), 0).label('total'),
                func.coalesce(func.sum(Invoice.amount_paid), 0).label('paid')
            )
        )
        invoice_stats = invoice_result.one()
        
        # Total quotes
        quote_result = await self.db.execute(
            select(
                func.count(Quote.id).label('count'),
                func.coalesce(func.sum(Quote.total_ttc), 0).label('total')
            )
        )
        quote_stats = quote_result.one()
        
        # Total clients
        client_result = await self.db.execute(
            select(func.count(Client.id))
        )
        total_clients = client_result.scalar() or 0
        
        # Total projects
        project_result = await self.db.execute(
            select(func.count(Project.id))
        )
        total_projects = project_result.scalar() or 0
        
        return {
            'total_invoices': invoice_stats.count,
            'total_invoiced_amount': float(invoice_stats.total),
            'total_paid_amount': float(invoice_stats.paid),
            'total_quotes': quote_stats.count,
            'total_quoted_amount': float(quote_stats.total),
            'total_clients': total_clients,
            'total_projects': total_projects
        }
    
    async def get_admin_dashboard_summary(self) -> Dict[str, Any]:
        """Get complete admin dashboard summary"""
        user_stats = await self.get_user_statistics()
        profile_stats = await self.get_profile_completion_stats()
        business_stats = await self.get_business_metrics()
        
        # Users missing critical info
        users_no_company = await self.get_users_missing_info('company')
        users_no_banking = await self.get_users_missing_info('banking')
        users_no_legal = await self.get_users_missing_info('legal')
        
        return {
            'user_statistics': user_stats,
            'profile_completion': profile_stats,
            'business_metrics': business_stats,
            'alerts': {
                'users_missing_company_info': len(users_no_company),
                'users_missing_banking_info': len(users_no_banking),
                'users_missing_legal_info': len(users_no_legal)
            }
        }
    
    def _calculate_completion(self, settings: Optional[UserSettings]) -> Dict:
        """Calculate profile completion for a user"""
        if not settings:
            return {
                'total_percentage': 0,
                'categories': {'profile': 0, 'company': 0, 'legal': 0, 'banking': 0},
                'fields': {field: False for field in self.ALL_FIELDS},
                'completed_count': 0,
                'total_count': len(self.ALL_FIELDS)
            }
        
        # Check each field
        fields_status = {}
        for field in self.ALL_FIELDS:
            value = getattr(settings, field, None)
            is_set = bool(value and str(value).strip()) if value is not None else False
            fields_status[field] = is_set
        
        completed = sum(1 for v in fields_status.values() if v)
        total_percentage = (completed / len(self.ALL_FIELDS)) * 100
        
        # Calculate category percentages
        categories = {}
        
        # Profile: name from user, phone from user, email_verified
        profile_fields = ['company_email']  # Simplified
        profile_complete = sum(1 for f in profile_fields if fields_status.get(f, False))
        categories['profile'] = (profile_complete / max(len(profile_fields), 1)) * 100
        
        # Company
        company_fields = ['company_name', 'company_address', 'company_email', 'company_phone']
        company_complete = sum(1 for f in company_fields if fields_status.get(f, False))
        categories['company'] = (company_complete / len(company_fields)) * 100
        
        # Legal
        legal_fields = ['siret', 'vat_number', 'legal_form']
        legal_complete = sum(1 for f in legal_fields if fields_status.get(f, False))
        categories['legal'] = (legal_complete / len(legal_fields)) * 100
        
        # Banking
        banking_fields = ['iban', 'bic']
        banking_complete = sum(1 for f in banking_fields if fields_status.get(f, False))
        categories['banking'] = (banking_complete / len(banking_fields)) * 100
        
        return {
            'total_percentage': round(total_percentage, 1),
            'categories': {k: round(v, 1) for k, v in categories.items()},
            'fields': fields_status,
            'completed_count': completed,
            'total_count': len(self.ALL_FIELDS)
        }


def get_admin_dashboard_service(db: AsyncSession) -> AdminDashboardService:
    """Factory function for dependency injection"""
    return AdminDashboardService(db)

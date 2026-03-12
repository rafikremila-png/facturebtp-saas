-- =====================================================
-- FactureBTP - Row Level Security (RLS) Policies
-- Multi-tenant security: users can only access their own data
-- Version: 1.0.0
-- Date: 2025-03-11
-- =====================================================

-- ============== ENABLE RLS ON ALL TABLES ==============

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE recurring_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analyses ENABLE ROW LEVEL SECURITY;

-- ============== USERS TABLE ==============

DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id);

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id) WITH CHECK (auth.uid()::text = id);

DROP POLICY IF EXISTS "Service role full access to users" ON users;
CREATE POLICY "Service role full access to users" ON users
    FOR ALL USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');

-- ============== CLIENTS TABLE ==============

DROP POLICY IF EXISTS "Users can view own clients" ON clients;
CREATE POLICY "Users can view own clients" ON clients
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create clients" ON clients;
CREATE POLICY "Users can create clients" ON clients
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update own clients" ON clients;
CREATE POLICY "Users can update own clients" ON clients
    FOR UPDATE USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete own clients" ON clients;
CREATE POLICY "Users can delete own clients" ON clients
    FOR DELETE USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Service role full access to clients" ON clients;
CREATE POLICY "Service role full access to clients" ON clients
    FOR ALL USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');

-- ============== QUOTES TABLE ==============

DROP POLICY IF EXISTS "Users can view own quotes" ON quotes;
CREATE POLICY "Users can view own quotes" ON quotes
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create quotes" ON quotes;
CREATE POLICY "Users can create quotes" ON quotes
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update own quotes" ON quotes;
CREATE POLICY "Users can update own quotes" ON quotes
    FOR UPDATE USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete own quotes" ON quotes;
CREATE POLICY "Users can delete own quotes" ON quotes
    FOR DELETE USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Service role full access to quotes" ON quotes;
CREATE POLICY "Service role full access to quotes" ON quotes
    FOR ALL USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');

-- ============== INVOICES TABLE ==============

DROP POLICY IF EXISTS "Users can view own invoices" ON invoices;
CREATE POLICY "Users can view own invoices" ON invoices
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create invoices" ON invoices;
CREATE POLICY "Users can create invoices" ON invoices
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update own invoices" ON invoices;
CREATE POLICY "Users can update own invoices" ON invoices
    FOR UPDATE USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete own invoices" ON invoices;
CREATE POLICY "Users can delete own invoices" ON invoices
    FOR DELETE USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Service role full access to invoices" ON invoices;
CREATE POLICY "Service role full access to invoices" ON invoices
    FOR ALL USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');

-- ============== PROJECTS TABLE ==============

DROP POLICY IF EXISTS "Users can view own projects" ON projects;
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create projects" ON projects;
CREATE POLICY "Users can create projects" ON projects
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update own projects" ON projects;
CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete own projects" ON projects;
CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Service role full access to projects" ON projects;
CREATE POLICY "Service role full access to projects" ON projects
    FOR ALL USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');

-- ============== WORK_ITEMS TABLE ==============

DROP POLICY IF EXISTS "Users can view own work_items" ON work_items;
CREATE POLICY "Users can view own work_items" ON work_items
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create work_items" ON work_items;
CREATE POLICY "Users can create work_items" ON work_items
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update own work_items" ON work_items;
CREATE POLICY "Users can update own work_items" ON work_items
    FOR UPDATE USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete own work_items" ON work_items;
CREATE POLICY "Users can delete own work_items" ON work_items
    FOR DELETE USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Service role full access to work_items" ON work_items;
CREATE POLICY "Service role full access to work_items" ON work_items
    FOR ALL USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');

-- ============== SERVICE_REQUESTS TABLE ==============

DROP POLICY IF EXISTS "Users can view own service_requests" ON service_requests;
CREATE POLICY "Users can view own service_requests" ON service_requests
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create service_requests" ON service_requests;
CREATE POLICY "Users can create service_requests" ON service_requests
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update own service_requests" ON service_requests;
CREATE POLICY "Users can update own service_requests" ON service_requests
    FOR UPDATE USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete own service_requests" ON service_requests;
CREATE POLICY "Users can delete own service_requests" ON service_requests
    FOR DELETE USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Service role full access to service_requests" ON service_requests;
CREATE POLICY "Service role full access to service_requests" ON service_requests
    FOR ALL USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');

-- ============== USER_SETTINGS TABLE ==============

DROP POLICY IF EXISTS "Users can view own settings" ON user_settings;
CREATE POLICY "Users can view own settings" ON user_settings
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create settings" ON user_settings;
CREATE POLICY "Users can create settings" ON user_settings
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update own settings" ON user_settings;
CREATE POLICY "Users can update own settings" ON user_settings
    FOR UPDATE USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete own settings" ON user_settings;
CREATE POLICY "Users can delete own settings" ON user_settings
    FOR DELETE USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Service role full access to user_settings" ON user_settings;
CREATE POLICY "Service role full access to user_settings" ON user_settings
    FOR ALL USING (current_setting('request.jwt.claims', true)::json->>'role' = 'service_role');

-- ============== PAYMENTS TABLE ==============

DROP POLICY IF EXISTS "Users can view own payments" ON payments;
CREATE POLICY "Users can view own payments" ON payments
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create payments" ON payments;
CREATE POLICY "Users can create payments" ON payments
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

-- ============== INVOICE_REMINDERS TABLE ==============

DROP POLICY IF EXISTS "Users can view own reminders" ON invoice_reminders;
CREATE POLICY "Users can view own reminders" ON invoice_reminders
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create reminders" ON invoice_reminders;
CREATE POLICY "Users can create reminders" ON invoice_reminders
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update own reminders" ON invoice_reminders;
CREATE POLICY "Users can update own reminders" ON invoice_reminders
    FOR UPDATE USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);

-- ============== RECURRING_INVOICES TABLE ==============

DROP POLICY IF EXISTS "Users can view own recurring" ON recurring_invoices;
CREATE POLICY "Users can view own recurring" ON recurring_invoices
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create recurring" ON recurring_invoices;
CREATE POLICY "Users can create recurring" ON recurring_invoices
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can update own recurring" ON recurring_invoices;
CREATE POLICY "Users can update own recurring" ON recurring_invoices
    FOR UPDATE USING (auth.uid()::text = user_id) WITH CHECK (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can delete own recurring" ON recurring_invoices;
CREATE POLICY "Users can delete own recurring" ON recurring_invoices
    FOR DELETE USING (auth.uid()::text = user_id);

-- ============== AI_ANALYSES TABLE ==============

DROP POLICY IF EXISTS "Users can view own analyses" ON ai_analyses;
CREATE POLICY "Users can view own analyses" ON ai_analyses
    FOR SELECT USING (auth.uid()::text = user_id);

DROP POLICY IF EXISTS "Users can create analyses" ON ai_analyses;
CREATE POLICY "Users can create analyses" ON ai_analyses
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

-- ============== SUMMARY ==============
-- Total policies created:
-- - users: 3 (SELECT, UPDATE, service_role)
-- - clients: 5 (CRUD + service_role)
-- - quotes: 5 (CRUD + service_role)
-- - invoices: 5 (CRUD + service_role)
-- - projects: 5 (CRUD + service_role)
-- - work_items: 5 (CRUD + service_role)
-- - service_requests: 5 (CRUD + service_role)
-- - user_settings: 5 (CRUD + service_role)
-- - payments: 2 (SELECT, INSERT)
-- - invoice_reminders: 3 (SELECT, INSERT, UPDATE)
-- - recurring_invoices: 4 (CRUD)
-- - ai_analyses: 2 (SELECT, INSERT)

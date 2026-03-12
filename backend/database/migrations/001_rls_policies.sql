-- =====================================================
-- FactureBTP - Row Level Security (RLS) Policies
-- Multi-tenant security: users can only access their own data
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

-- ============== USERS TABLE ==============
-- Users can only read/update their own profile

DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Service role can do everything (for admin operations)
DROP POLICY IF EXISTS "Service role full access to users" ON users;
CREATE POLICY "Service role full access to users" ON users
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- ============== CLIENTS TABLE ==============
-- Users can only access their own clients

DROP POLICY IF EXISTS "Users can view own clients" ON clients;
CREATE POLICY "Users can view own clients" ON clients
    FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create clients" ON clients;
CREATE POLICY "Users can create clients" ON clients
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own clients" ON clients;
CREATE POLICY "Users can update own clients" ON clients
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own clients" ON clients;
CREATE POLICY "Users can delete own clients" ON clients
    FOR DELETE
    USING (auth.uid() = user_id);

-- Service role full access
DROP POLICY IF EXISTS "Service role full access to clients" ON clients;
CREATE POLICY "Service role full access to clients" ON clients
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- ============== QUOTES TABLE ==============
-- Users can only access their own quotes

DROP POLICY IF EXISTS "Users can view own quotes" ON quotes;
CREATE POLICY "Users can view own quotes" ON quotes
    FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create quotes" ON quotes;
CREATE POLICY "Users can create quotes" ON quotes
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own quotes" ON quotes;
CREATE POLICY "Users can update own quotes" ON quotes
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own quotes" ON quotes;
CREATE POLICY "Users can delete own quotes" ON quotes
    FOR DELETE
    USING (auth.uid() = user_id);

-- Service role full access
DROP POLICY IF EXISTS "Service role full access to quotes" ON quotes;
CREATE POLICY "Service role full access to quotes" ON quotes
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- ============== INVOICES TABLE ==============
-- Users can only access their own invoices

DROP POLICY IF EXISTS "Users can view own invoices" ON invoices;
CREATE POLICY "Users can view own invoices" ON invoices
    FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create invoices" ON invoices;
CREATE POLICY "Users can create invoices" ON invoices
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own invoices" ON invoices;
CREATE POLICY "Users can update own invoices" ON invoices
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own invoices" ON invoices;
CREATE POLICY "Users can delete own invoices" ON invoices
    FOR DELETE
    USING (auth.uid() = user_id);

-- Service role full access
DROP POLICY IF EXISTS "Service role full access to invoices" ON invoices;
CREATE POLICY "Service role full access to invoices" ON invoices
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- ============== PROJECTS TABLE ==============
-- Users can only access their own projects

DROP POLICY IF EXISTS "Users can view own projects" ON projects;
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create projects" ON projects;
CREATE POLICY "Users can create projects" ON projects
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own projects" ON projects;
CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own projects" ON projects;
CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE
    USING (auth.uid() = user_id);

-- Service role full access
DROP POLICY IF EXISTS "Service role full access to projects" ON projects;
CREATE POLICY "Service role full access to projects" ON projects
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- ============== WORK_ITEMS TABLE ==============
-- Users can only access their own work items (library)

DROP POLICY IF EXISTS "Users can view own work_items" ON work_items;
CREATE POLICY "Users can view own work_items" ON work_items
    FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create work_items" ON work_items;
CREATE POLICY "Users can create work_items" ON work_items
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own work_items" ON work_items;
CREATE POLICY "Users can update own work_items" ON work_items
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own work_items" ON work_items;
CREATE POLICY "Users can delete own work_items" ON work_items
    FOR DELETE
    USING (auth.uid() = user_id);

-- Service role full access
DROP POLICY IF EXISTS "Service role full access to work_items" ON work_items;
CREATE POLICY "Service role full access to work_items" ON work_items
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- ============== SERVICE_REQUESTS TABLE ==============
-- Users can only access their own service requests

DROP POLICY IF EXISTS "Users can view own service_requests" ON service_requests;
CREATE POLICY "Users can view own service_requests" ON service_requests
    FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create service_requests" ON service_requests;
CREATE POLICY "Users can create service_requests" ON service_requests
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own service_requests" ON service_requests;
CREATE POLICY "Users can update own service_requests" ON service_requests
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own service_requests" ON service_requests;
CREATE POLICY "Users can delete own service_requests" ON service_requests
    FOR DELETE
    USING (auth.uid() = user_id);

-- Service role full access
DROP POLICY IF EXISTS "Service role full access to service_requests" ON service_requests;
CREATE POLICY "Service role full access to service_requests" ON service_requests
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- ============== USER_SETTINGS TABLE ==============
-- Users can only access their own settings

DROP POLICY IF EXISTS "Users can view own user_settings" ON user_settings;
CREATE POLICY "Users can view own user_settings" ON user_settings
    FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create user_settings" ON user_settings;
CREATE POLICY "Users can create user_settings" ON user_settings
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own user_settings" ON user_settings;
CREATE POLICY "Users can update own user_settings" ON user_settings
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own user_settings" ON user_settings;
CREATE POLICY "Users can delete own user_settings" ON user_settings
    FOR DELETE
    USING (auth.uid() = user_id);

-- Service role full access
DROP POLICY IF EXISTS "Service role full access to user_settings" ON user_settings;
CREATE POLICY "Service role full access to user_settings" ON user_settings
    FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- ============== VERIFICATION ==============
-- List all policies to verify
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

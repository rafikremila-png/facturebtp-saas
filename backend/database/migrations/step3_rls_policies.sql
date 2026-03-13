-- =====================================================
-- PARTIE 3: ROW LEVEL SECURITY (RLS)
-- Exécutez cette partie après les Parties 1 et 2
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE predefined_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE kits ENABLE ROW LEVEL SECURITY;
ALTER TABLE share_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE counters ENABLE ROW LEVEL SECURITY;

-- ===== USERS POLICIES =====
DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile" ON users 
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile" ON users 
    FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert own profile" ON users;
CREATE POLICY "Users can insert own profile" ON users 
    FOR INSERT WITH CHECK (auth.uid() = id);

-- ===== SETTINGS POLICIES =====
DROP POLICY IF EXISTS "Users can manage own settings" ON settings;
CREATE POLICY "Users can manage own settings" ON settings 
    FOR ALL USING (auth.uid() = user_id);

-- ===== SUBSCRIPTIONS POLICIES =====
DROP POLICY IF EXISTS "Users can view own subscription" ON subscriptions;
CREATE POLICY "Users can view own subscription" ON subscriptions 
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own subscription" ON subscriptions;
CREATE POLICY "Users can manage own subscription" ON subscriptions 
    FOR ALL USING (auth.uid() = user_id);

-- ===== CLIENTS POLICIES =====
DROP POLICY IF EXISTS "Users can view own clients" ON clients;
CREATE POLICY "Users can view own clients" ON clients 
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own clients" ON clients;
CREATE POLICY "Users can insert own clients" ON clients 
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own clients" ON clients;
CREATE POLICY "Users can update own clients" ON clients 
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own clients" ON clients;
CREATE POLICY "Users can delete own clients" ON clients 
    FOR DELETE USING (auth.uid() = user_id);

-- ===== QUOTES POLICIES =====
DROP POLICY IF EXISTS "Users can view own quotes" ON quotes;
CREATE POLICY "Users can view own quotes" ON quotes 
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own quotes" ON quotes;
CREATE POLICY "Users can insert own quotes" ON quotes 
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own quotes" ON quotes;
CREATE POLICY "Users can update own quotes" ON quotes 
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own quotes" ON quotes;
CREATE POLICY "Users can delete own quotes" ON quotes 
    FOR DELETE USING (auth.uid() = user_id);

-- Policy for shared quotes (public access via token)
DROP POLICY IF EXISTS "Anyone can view shared quotes" ON quotes;
CREATE POLICY "Anyone can view shared quotes" ON quotes 
    FOR SELECT USING (share_token IS NOT NULL);

-- ===== INVOICES POLICIES =====
DROP POLICY IF EXISTS "Users can view own invoices" ON invoices;
CREATE POLICY "Users can view own invoices" ON invoices 
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own invoices" ON invoices;
CREATE POLICY "Users can insert own invoices" ON invoices 
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own invoices" ON invoices;
CREATE POLICY "Users can update own invoices" ON invoices 
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own invoices" ON invoices;
CREATE POLICY "Users can delete own invoices" ON invoices 
    FOR DELETE USING (auth.uid() = user_id);

-- Policy for shared invoices
DROP POLICY IF EXISTS "Anyone can view shared invoices" ON invoices;
CREATE POLICY "Anyone can view shared invoices" ON invoices 
    FOR SELECT USING (share_token IS NOT NULL);

-- ===== PREDEFINED ITEMS POLICIES =====
DROP POLICY IF EXISTS "Users can view own or global items" ON predefined_items;
CREATE POLICY "Users can view own or global items" ON predefined_items 
    FOR SELECT USING (auth.uid() = user_id OR is_global = true);

DROP POLICY IF EXISTS "Users can manage own items" ON predefined_items;
CREATE POLICY "Users can manage own items" ON predefined_items 
    FOR ALL USING (auth.uid() = user_id);

-- ===== KITS POLICIES =====
DROP POLICY IF EXISTS "Users can view own or global kits" ON kits;
CREATE POLICY "Users can view own or global kits" ON kits 
    FOR SELECT USING (auth.uid() = user_id OR is_global = true);

DROP POLICY IF EXISTS "Users can manage own kits" ON kits;
CREATE POLICY "Users can manage own kits" ON kits 
    FOR ALL USING (auth.uid() = user_id);

-- ===== SHARE LINKS POLICIES =====
DROP POLICY IF EXISTS "Users can manage own share links" ON share_links;
CREATE POLICY "Users can manage own share links" ON share_links 
    FOR ALL USING (auth.uid() = user_id);

-- ===== COUNTERS POLICIES =====
DROP POLICY IF EXISTS "Users can manage own counters" ON counters;
CREATE POLICY "Users can manage own counters" ON counters 
    FOR ALL USING (auth.uid() = user_id);

SELECT 'Partie 3 (RLS) exécutée avec succès!' as status;

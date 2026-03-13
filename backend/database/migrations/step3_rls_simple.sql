-- =====================================================
-- PARTIE 3 SIMPLIFIÉE: ROW LEVEL SECURITY (RLS)
-- Compatible avec VARCHAR et UUID
-- =====================================================

-- Enable RLS on tables that exist
DO $$ 
BEGIN
    -- Users
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Settings
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'settings') THEN
        ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Subscriptions
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'subscriptions') THEN
        ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Clients
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'clients') THEN
        ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Quotes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'quotes') THEN
        ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Invoices
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'invoices') THEN
        ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Predefined items
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'predefined_items') THEN
        ALTER TABLE predefined_items ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Kits
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'kits') THEN
        ALTER TABLE kits ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Share links
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'share_links') THEN
        ALTER TABLE share_links ENABLE ROW LEVEL SECURITY;
    END IF;
    
    -- Counters
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'counters') THEN
        ALTER TABLE counters ENABLE ROW LEVEL SECURITY;
    END IF;
END $$;

-- ===== USERS POLICIES =====
DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile" ON users 
    FOR SELECT USING (auth.uid()::text = id::text);

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile" ON users 
    FOR UPDATE USING (auth.uid()::text = id::text);

DROP POLICY IF EXISTS "Users can insert own profile" ON users;
CREATE POLICY "Users can insert own profile" ON users 
    FOR INSERT WITH CHECK (auth.uid()::text = id::text);

-- ===== SETTINGS POLICIES =====
DROP POLICY IF EXISTS "Users can manage own settings" ON settings;
CREATE POLICY "Users can manage own settings" ON settings 
    FOR ALL USING (auth.uid()::text = user_id::text);

-- ===== SUBSCRIPTIONS POLICIES =====
DROP POLICY IF EXISTS "Users can manage own subscription" ON subscriptions;
CREATE POLICY "Users can manage own subscription" ON subscriptions 
    FOR ALL USING (auth.uid()::text = user_id::text);

-- ===== CLIENTS POLICIES =====
DROP POLICY IF EXISTS "Users can view own clients" ON clients;
CREATE POLICY "Users can view own clients" ON clients 
    FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can insert own clients" ON clients;
CREATE POLICY "Users can insert own clients" ON clients 
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can update own clients" ON clients;
CREATE POLICY "Users can update own clients" ON clients 
    FOR UPDATE USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can delete own clients" ON clients;
CREATE POLICY "Users can delete own clients" ON clients 
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- ===== QUOTES POLICIES =====
DROP POLICY IF EXISTS "Users can view own quotes" ON quotes;
CREATE POLICY "Users can view own quotes" ON quotes 
    FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can insert own quotes" ON quotes;
CREATE POLICY "Users can insert own quotes" ON quotes 
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can update own quotes" ON quotes;
CREATE POLICY "Users can update own quotes" ON quotes 
    FOR UPDATE USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can delete own quotes" ON quotes;
CREATE POLICY "Users can delete own quotes" ON quotes 
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- ===== INVOICES POLICIES =====
DROP POLICY IF EXISTS "Users can view own invoices" ON invoices;
CREATE POLICY "Users can view own invoices" ON invoices 
    FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can insert own invoices" ON invoices;
CREATE POLICY "Users can insert own invoices" ON invoices 
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can update own invoices" ON invoices;
CREATE POLICY "Users can update own invoices" ON invoices 
    FOR UPDATE USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can delete own invoices" ON invoices;
CREATE POLICY "Users can delete own invoices" ON invoices 
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- ===== PREDEFINED ITEMS POLICIES =====
DROP POLICY IF EXISTS "Users can view own items" ON predefined_items;
CREATE POLICY "Users can view own items" ON predefined_items 
    FOR SELECT USING (auth.uid()::text = user_id::text OR is_global = true);

DROP POLICY IF EXISTS "Users can manage own items" ON predefined_items;
CREATE POLICY "Users can manage own items" ON predefined_items 
    FOR ALL USING (auth.uid()::text = user_id::text);

-- ===== KITS POLICIES =====
DROP POLICY IF EXISTS "Users can view own kits" ON kits;
CREATE POLICY "Users can view own kits" ON kits 
    FOR SELECT USING (auth.uid()::text = user_id::text OR is_global = true);

DROP POLICY IF EXISTS "Users can manage own kits" ON kits;
CREATE POLICY "Users can manage own kits" ON kits 
    FOR ALL USING (auth.uid()::text = user_id::text);

-- ===== SHARE LINKS POLICIES =====
DROP POLICY IF EXISTS "Users can manage own share links" ON share_links;
CREATE POLICY "Users can manage own share links" ON share_links 
    FOR ALL USING (auth.uid()::text = user_id::text);

-- ===== COUNTERS POLICIES =====
DROP POLICY IF EXISTS "Users can manage own counters" ON counters;
CREATE POLICY "Users can manage own counters" ON counters 
    FOR ALL USING (auth.uid()::text = user_id::text);

SELECT 'RLS Policies créées avec succès!' as status;
